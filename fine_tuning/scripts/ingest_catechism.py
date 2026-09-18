#!/usr/bin/env python3
"""Ingest Spurgeon's Puritan Catechism into the local vector store for RAG parity.

Indexes each Q&A as a Document with metadata:
  author=Charles Haddon Spurgeon
  doc_type=catechism
  work=Puritan Catechism
  catechism_number=N
  title=Puritan Catechism Q.N

Default target: Chroma persist dir (local). Pass --qdrant to use Qdrant instead.

Usage (repo root):
  python fine_tuning/scripts/ingest_catechism.py
  python fine_tuning/scripts/ingest_catechism.py --limit 20
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_REPO = Path(__file__).resolve().parent.parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from config import (  # noqa: E402
    CHROMA_COLLECTION,
    CHROMA_PERSIST_DIR,
    DEFAULT_AUTHOR,
    EMBEDDING_MODEL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_URL,
    VECTOR_STORE,
)

DEFAULT_SRC = _REPO / "data" / "catechism" / "puritan_catechism.json"


def load_items(src: Path, limit: int) -> list[dict]:
    raw = json.loads(src.read_text(encoding="utf-8"))
    items = list(raw.get("Data") or [])
    if limit > 0:
        items = items[:limit]
    return items


def to_documents(items: list[dict]) -> list[Document]:
    docs: list[Document] = []
    for item in items:
        n = int(item["Number"])
        q = item["Question"].strip()
        a = (item.get("AnswerWithProofs") or item["Answer"]).strip()
        text = f"Q. {q}\nA. {a}"
        proofs = item.get("Proofs") or []
        if isinstance(proofs, list):
            refs_flat = "; ".join(str(x) for x in proofs)
        else:
            refs_flat = str(proofs) if proofs else ""
        meta = {
            "author": DEFAULT_AUTHOR,
            "doc_type": "catechism",
            "work": "Puritan Catechism",
            "catechism_number": n,
            "title": f"Puritan Catechism Q.{n}",
            "sermon_number": "",
            "volume": "",
            "year": 1855,
            "primary_scripture": "",
            "bible_book": "",
            "source_url": "https://www.blueletterbible.org/study/ccc/chs_puritancatechism.cfm",
            "bible_references": refs_flat,
        }
        docs.append(Document(text=text, metadata=meta))
    return docs


def build_chroma_index(docs: list[Document]) -> None:
    try:
        import chromadb
        from llama_index.vector_stores.chroma import ChromaVectorStore
    except ImportError as e:
        raise SystemExit(f"chromadb required for local catechism ingest: {e}") from e

    persist = Path(CHROMA_PERSIST_DIR or (_REPO / "chroma_db"))
    persist.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist))
    collection = client.get_or_create_collection(CHROMA_COLLECTION)
    store = ChromaVectorStore(chroma_collection=collection)
    storage = StorageContext.from_defaults(vector_store=store)
    VectorStoreIndex.from_documents(docs, storage_context=storage, show_progress=True)
    print(f"Indexed {len(docs)} catechism docs into Chroma {CHROMA_COLLECTION} @ {persist}")


def build_qdrant_index(docs: list[Document]) -> None:
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient

    if not QDRANT_URL:
        raise SystemExit("QDRANT_URL not set")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY or None, timeout=60)
    store = QdrantVectorStore(client=client, collection_name=QDRANT_COLLECTION)
    storage = StorageContext.from_defaults(vector_store=store)
    VectorStoreIndex.from_documents(docs, storage_context=storage, show_progress=True)
    print(f"Indexed {len(docs)} catechism docs into Qdrant {QDRANT_COLLECTION}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ingest Puritan Catechism for RAG")
    p.add_argument("--src", default=str(DEFAULT_SRC))
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--qdrant", action="store_true", help="Force Qdrant instead of Chroma")
    p.add_argument(
        "--chroma",
        action="store_true",
        help="Force local Chroma (default when Qdrant is unreachable / for local RAG parity)",
    )
    args = p.parse_args(argv)

    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
    items = load_items(Path(args.src), args.limit)
    docs = to_documents(items)
    if not docs:
        print("ERROR: no catechism items", file=sys.stderr)
        return 2

    # Prefer local Chroma for this parity path unless --qdrant is explicit.
    if args.qdrant and not args.chroma:
        build_qdrant_index(docs)
    else:
        build_chroma_index(docs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
