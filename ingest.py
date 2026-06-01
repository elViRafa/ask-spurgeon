#!/usr/bin/env python3
"""
Ask Spurgeon — Ingestion Pipeline

Builds a high-quality vector index in Qdrant (default) or local ChromaDB from Spurgeon sermons.

Recommended data source (best quality):
    git clone https://github.com/lyteword/chspurgeon-sermons.git data/chspurgeon-sermons

Alternative (original PDFs):
    Download chs1.pdf ... chs3563.pdf into data/sermons/

Usage:
    python ingest.py --source markdown --limit 100
    python ingest.py --source pdf --limit 20
    python ingest.py --recreate-collection
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator
import json

from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()   # Must be called BEFORE importing config.py

from llama_index.core import Document, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import StorageContext, VectorStoreIndex

# Optional ChromaDB support
try:
    from llama_index.vector_stores.chroma import ChromaVectorStore
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType, Filter, FieldCondition, MatchValue

# Local imports
from config import (
    VECTOR_STORE,
    QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION,
    CHROMA_HOST, CHROMA_PORT, CHROMA_COLLECTION, CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL, EMBEDDING_DIM,
    CHUNK_SIZE, CHUNK_OVERLAP, BATCH_SIZE, MAX_SERMONS,
    SERMONS_DIR, MARKDOWN_DIR, DEFAULT_AUTHOR,
)
from utils.metadata import parse_markdown_sermon, parse_pdf_sermon_text
from utils.bible_refs import extract_bible_references


# =============================================================================
# Qdrant Setup
# =============================================================================

def get_qdrant_client() -> QdrantClient:
    if not QDRANT_URL:
        raise RuntimeError("QDRANT_URL not set. See .env.example")
    return QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY or None,
        timeout=60,
    )


def recreate_collection(client: QdrantClient, collection: str = QDRANT_COLLECTION) -> None:
    """Delete and recreate the collection with proper vector + payload indexes."""
    print(f"Recreating collection: {collection}")

    if client.collection_exists(collection):
        client.delete_collection(collection)

    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )

    # Payload indexes for fast filtering (critical for the app)
    client.create_payload_index(collection, "author", field_schema=PayloadSchemaType.KEYWORD)
    client.create_payload_index(collection, "sermon_number", field_schema=PayloadSchemaType.INTEGER)
    client.create_payload_index(collection, "volume", field_schema=PayloadSchemaType.INTEGER)
    client.create_payload_index(collection, "year", field_schema=PayloadSchemaType.INTEGER)
    client.create_payload_index(collection, "bible_book", field_schema=PayloadSchemaType.KEYWORD)
    client.create_payload_index(collection, "bible_references", field_schema=PayloadSchemaType.KEYWORD)  # array

    print("Collection + indexes created.")


def get_or_create_collection(client: QdrantClient, collection: str = QDRANT_COLLECTION) -> None:
    if not client.collection_exists(collection):
        print(f"Collection {collection} does not exist — creating...")
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        # Create indexes even on first creation
        for field in ["author", "sermon_number", "volume", "year", "bible_book", "bible_references"]:
            try:
                schema = PayloadSchemaType.INTEGER if field in ("sermon_number", "volume", "year") else PayloadSchemaType.KEYWORD
                client.create_payload_index(collection, field, field_schema=schema)
            except Exception:
                pass


# =============================================================================
# Document Loading
# =============================================================================

def iter_markdown_sermons(limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """Yield parsed sermon dicts from the lyteword markdown collection."""
    if not MARKDOWN_DIR.exists():
        raise FileNotFoundError(
            f"Markdown directory not found: {MARKDOWN_DIR}\n"
            "Clone it with:\n"
            "  git clone https://github.com/lyteword/chspurgeon-sermons.git data/chspurgeon-sermons"
        )

    # Walk volumes in order
    volume_dirs = sorted(MARKDOWN_DIR.glob("volume-*"), key=lambda p: int(p.name.split("-")[1]))

    count = 0
    for vol_dir in volume_dirs:
        # Support both naming conventions used in the repo:
        #   sermon-123.md  (early volumes)
        #   sermon_547.md  (later volumes)
        md_files = list(vol_dir.glob("sermon-*.md")) + list(vol_dir.glob("sermon_*.md"))

        # Robust sorting that works with both hyphen and underscore
        def sermon_sort_key(p):
            name = p.stem.lower().replace("sermon-", "").replace("sermon_", "")
            num = name.split("-")[0].split("_")[0]
            try:
                return int(num)
            except:
                return 999999

        for md_file in sorted(md_files, key=sermon_sort_key):
            if limit and count >= limit:
                return
            try:
                meta = parse_markdown_sermon(md_file)
                yield meta
                count += 1
            except Exception as e:
                print(f"Warning: failed to parse {md_file}: {e}")


def iter_pdf_sermons(limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """Yield parsed sermon dicts from chs*.pdf files (requires pypdf + pdfplumber)."""
    if not SERMONS_DIR.exists():
        raise FileNotFoundError(f"PDF directory not found: {SERMONS_DIR}")

    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber required for PDF ingestion. pip install pdfplumber")

    pdf_files = sorted(
        SERMONS_DIR.glob("chs*.pdf"),
        key=lambda p: int(p.stem.replace("chs", "") or 0)
    )

    count = 0
    for pdf_path in pdf_files:
        if limit and count >= limit:
            return
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            meta = parse_pdf_sermon_text(full_text, pdf_path.name)
            meta["full_text"] = full_text
            yield meta
            count += 1
        except Exception as e:
            print(f"Warning: failed to parse {pdf_path.name}: {e}")


# =============================================================================
# Chunking + Metadata Enrichment
# =============================================================================

def make_documents_from_sermon(sermon: Dict[str, Any]) -> List[Document]:
    """
    Split a sermon into LlamaIndex Documents.
    Every chunk carries rich author-aware + filterable metadata.
    """
    text = sermon["full_text"]
    if not text or len(text) < 200:
        return []

    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_text(text)

    docs: List[Document] = []
    for chunk in chunks:
        # Re-extract refs from this specific chunk (more precise than sermon-level)
        chunk_refs = extract_bible_references(chunk, max_refs=12)

        # ChromaDB requires simple metadata values (no lists)
        bible_refs = list(set(sermon.get("bible_references", []) + chunk_refs))
        chunk_refs_list = chunk_refs

        metadata = {
            "author": sermon.get("author", DEFAULT_AUTHOR),
            "sermon_number": sermon.get("sermon_number"),
            "title": sermon.get("title", ""),
            "volume": sermon.get("volume"),
            "year": sermon.get("year"),
            "primary_scripture": sermon.get("primary_scripture", ""),
            "bible_book": sermon.get("bible_book", ""),
            "source_url": sermon.get("source_url", ""),
            # Convert lists to comma-separated strings for ChromaDB compatibility
            "bible_references": ",".join(map(str, bible_refs)) if bible_refs else "",
            "chunk_bible_references": ",".join(map(str, chunk_refs_list)) if chunk_refs_list else "",
        }

        doc = Document(
            text=chunk,
            metadata=metadata,
            excluded_llm_metadata_keys=["full_text"],  # never send raw full sermon
        )
        docs.append(doc)

    return docs


# =============================================================================
# Main Ingestion
# =============================================================================

def build_index(
    source: str = "markdown",
    limit: Optional[int] = None,
    recreate: bool = False,
    batch_size: int = BATCH_SIZE,
) -> None:
    print(f"Starting ingestion | source={source} | limit={limit or 'all'} | recreate={recreate}")

    # Configure global LlamaIndex settings
    embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
    Settings.embed_model = embed_model
    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP

    # Prepare vector store (Qdrant or ChromaDB)
    if VECTOR_STORE == "chroma":
        if not CHROMA_AVAILABLE:
            print("ERROR: ChromaDB support not installed.")
            print("Install with: pip install chromadb llama-index-vector-stores-chroma")
            sys.exit(1)

        if CHROMA_PERSIST_DIR:
            print(f"Using local persistent ChromaDB at: {CHROMA_PERSIST_DIR}")
            chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        else:
            print(f"Using local ChromaDB (Docker) at {CHROMA_HOST}:{CHROMA_PORT}")
            chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

        # Create collection if it doesn't exist
        try:
            chroma_client.get_collection(CHROMA_COLLECTION)
        except Exception:
            chroma_client.create_collection(CHROMA_COLLECTION)

        chroma_collection = chroma_client.get_collection(CHROMA_COLLECTION)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        print(f"ChromaDB collection ready: {CHROMA_COLLECTION}")

        # Chroma doesn't need the old Qdrant client logic
        client = None

    else:
        # Default: Qdrant
        client = get_qdrant_client()
        if recreate:
            recreate_collection(client)
        else:
            get_or_create_collection(client)

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION,
            batch_size=batch_size,
        )
        print(f"Using Qdrant collection: {QDRANT_COLLECTION}")

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Stream documents
    if source == "markdown":
        sermon_iter = iter_markdown_sermons(limit=limit)
    elif source == "pdf":
        sermon_iter = iter_pdf_sermons(limit=limit)
    else:
        raise ValueError("source must be 'markdown' or 'pdf'")

    all_nodes = []
    processed = 0

    for sermon in tqdm(sermon_iter, desc="Processing sermons"):
        docs = make_documents_from_sermon(sermon)
        if docs:
            all_nodes.extend(docs)
        processed += 1

        # Periodic upsert to avoid huge memory usage
        if len(all_nodes) >= 800:
            print(f"Upserting batch of {len(all_nodes)} nodes...")
            VectorStoreIndex(nodes=all_nodes, storage_context=storage_context, embed_model=embed_model)
            all_nodes = []

    # Final batch
    if all_nodes:
        print(f"Final upsert of {len(all_nodes)} nodes...")
        VectorStoreIndex(nodes=all_nodes, storage_context=storage_context, embed_model=embed_model)

    print(f"\nIngestion complete. Processed {processed} sermons.")
    if VECTOR_STORE == "chroma":
        print(f"ChromaDB collection: {CHROMA_COLLECTION} (local Docker)")
    else:
        print(f"Qdrant collection: {QDRANT_COLLECTION}")
    print("You can now run: streamlit run app.py")


def main():
    parser = argparse.ArgumentParser(description="Ingest Spurgeon sermons into Qdrant or local ChromaDB")
    parser.add_argument("--source", choices=["markdown", "pdf"], default="markdown",
                        help="Data source (markdown recommended)")
    parser.add_argument("--limit", type=int, default=MAX_SERMONS or 0,
                        help="Maximum number of sermons to ingest (0 = all)")
    parser.add_argument("--recreate-collection", action="store_true",
                        help="Delete and recreate the Qdrant collection")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    limit = args.limit if args.limit > 0 else None

    build_index(
        source=args.source,
        limit=limit,
        recreate=args.recreate_collection,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
