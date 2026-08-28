#!/usr/bin/env python3
"""Local unit test for Kaggle path resolution used in B_training_sota / C_eval_sota."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

SKIP_WALK_DIRS = {"hf_home", "unsloth_compiled_cache", ".cache", "hub", "__pycache__"}


def _posix(p: str) -> str:
    return Path(p).as_posix()


def _pruned_walk(input_root: Path, max_depth: int = 10):
    root = str(input_root)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_WALK_DIRS and not d.startswith(".")]
        depth = Path(dirpath).relative_to(root).parts
        if len(depth) > max_depth:
            dirnames[:] = []
            continue
        yield dirpath, dirnames, filenames


def find_adapter(input_root: Path) -> str | None:
    markers = []
    for dirpath, _dirnames, filenames in _pruned_walk(input_root):
        if "adapter_config.json" not in filenames:
            continue
        n = _posix(dirpath)
        if "theology_cpt_lora" in n or "checkpoints_sota" in n:
            markers.append(dirpath)
    ranked = []
    for p in markers:
        n = _posix(p)
        score = 0
        if n.endswith("/theology_cpt_lora") or "/theology_cpt_lora/" in n:
            score += 100
        if "checkpoint-" in n:
            score += 5
        ranked.append((score, p))
    ranked.sort(reverse=True)
    return ranked[0][1] if ranked else None


def find_hf_dataset_root(input_root: Path) -> str | None:
    bases = [
        input_root / "theology-cpt-dataset",
        input_root / "datasets" / "rafaelvieira1" / "theology-cpt-dataset",
    ]
    for base in bases:
        if not base.exists():
            continue
        nested = base / "theology_dataset"
        for cand in (nested, base):
            if (cand / "dataset_dict.json").is_file():
                return str(cand)
    return None


def find_holdout_root(input_root: Path) -> str | None:
    hits = []
    for dirpath, dirnames, _filenames in _pruned_walk(input_root):
        if "theology_holdouts" in dirnames:
            cand = os.path.join(dirpath, "theology_holdouts")
            if (Path(cand) / "spurgeon" / "dataset_info.json").is_file():
                hits.append(cand)
        if Path(dirpath).name == "theology_holdouts" and (
            Path(dirpath) / "spurgeon" / "dataset_info.json"
        ).is_file():
            hits.append(dirpath)
    for prefer in ("/notebooks/", "/theology-cpt-dataset/"):
        for h in hits:
            if prefer.rstrip("/") in _posix(h):
                return h
    return hits[0] if hits else None


def text_tokenizer(tok):
    inner = tok
    for _ in range(4):
        nxt = getattr(inner, "tokenizer", None)
        if nxt is None or nxt is inner:
            break
        inner = nxt
    return inner


def ids_for_text(tok, text, add_special_tokens=False):
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    t = text_tokenizer(tok)
    if hasattr(t, "encode") and getattr(t, "image_processor", None) is None:
        ids = t.encode(text, add_special_tokens=add_special_tokens)
        if hasattr(ids, "tolist"):
            ids = ids.tolist()
        if ids and isinstance(ids[0], (list, tuple)):
            ids = list(ids[0])
        return [int(x) for x in ids]
    try:
        out = t(text=text, add_special_tokens=add_special_tokens)
    except TypeError:
        out = t(text, add_special_tokens=add_special_tokens)
    ids = out["input_ids"]
    if hasattr(ids, "tolist"):
        ids = ids.tolist()
    if ids and isinstance(ids[0], (list, tuple)):
        ids = list(ids[0])
    return [int(x) for x in ids]


class _InnerTok:
    def encode(self, text, add_special_tokens=False):
        return [11, 22, 33] if "Sermon" in text else [1]


class _VLProcessor:
    """Mirrors Qwen3.5 Processor: first positional arg is images."""

    image_processor = object()

    def __init__(self):
        self.tokenizer = _InnerTok()

    def __call__(self, images=None, text=None, add_special_tokens=False, **kwargs):
        if images is not None:
            raise ValueError(
                "Incorrect image source. Must be a valid URL starting with `http://` or "
                f"`https://`, a valid path to an image file, or a base64 encoded string. Got {images}"
            )
        return {"input_ids": [[7, 8, 9]]}


def test_vl_processor_text_not_image() -> None:
    sermon = "Sermon 32 | The Necessity of Increased Faith\nAnd the apostle said unto the Lord"
    proc = _VLProcessor()
    try:
        proc(sermon)
        raise AssertionError("positional processor call should treat text as image")
    except ValueError as e:
        assert "Incorrect image source" in str(e), e
    ids = ids_for_text(proc, sermon)
    assert ids == [11, 22, 33], ids


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "kaggle" / "input"
        # Layout matching current Kaggle upload (files at dataset root)
        ds = root / "theology-cpt-dataset"
        ds.mkdir(parents=True)
        (ds / "dataset_dict.json").write_text('{"splits":["train","test"]}', encoding="utf-8")
        (ds / "train").mkdir()
        found = find_hf_dataset_root(root)
        assert found == str(ds), found

        # Nested layout also works
        root2 = Path(tmp) / "kaggle2" / "input"
        nested = root2 / "datasets" / "rafaelvieira1" / "theology-cpt-dataset" / "theology_dataset"
        nested.mkdir(parents=True)
        (nested / "dataset_dict.json").write_text("{}", encoding="utf-8")
        found2 = find_hf_dataset_root(root2)
        assert found2 == str(nested), found2

        # Kernel-source layout used by C_eval (2026-08-24 Kaggle mount)
        root3 = Path(tmp) / "kaggle3" / "input"
        kernel = root3 / "notebooks" / "rafaelvieira1" / "theology-cpt-v2-b-training-sota"
        lora = kernel / "theology_cpt_lora"
        ckpt = kernel / "checkpoints_sota" / "checkpoint-50"
        decoy = kernel / "hf_home" / "hub" / "models--someone" / "adapters"
        hold = kernel / "theology_holdouts" / "spurgeon"
        corpus_txt = root3 / "datasets" / "rafaelvieira1" / "theology-cpt-corpus" / "holdouts"
        lora.mkdir(parents=True)
        ckpt.mkdir(parents=True)
        decoy.mkdir(parents=True)
        hold.mkdir(parents=True)
        corpus_txt.mkdir(parents=True)
        (lora / "adapter_config.json").write_text("{}", encoding="utf-8")
        (ckpt / "adapter_config.json").write_text("{}", encoding="utf-8")
        (decoy / "adapter_config.json").write_text("{}", encoding="utf-8")
        (hold / "dataset_info.json").write_text("{}", encoding="utf-8")
        (corpus_txt / "spurgeon_holdout.txt").write_text("x", encoding="utf-8")
        found3 = find_adapter(root3)
        assert found3 == str(lora), found3
        found_h = find_holdout_root(root3)
        assert found_h == str(kernel / "theology_holdouts"), found_h

        # If only checkpoint-50 exists, use it
        root4 = Path(tmp) / "kaggle4" / "input"
        only_ckpt = (
            root4
            / "notebooks"
            / "rafaelvieira1"
            / "theology-cpt-v2-b-training-sota"
            / "checkpoints_sota"
            / "checkpoint-50"
        )
        only_ckpt.mkdir(parents=True)
        (only_ckpt / "adapter_config.json").write_text("{}", encoding="utf-8")
        found4 = find_adapter(root4)
        assert found4 == str(only_ckpt), found4

    test_vl_processor_text_not_image()

    print("PASS: Kaggle HF dataset path resolution")
    print("PASS: Kaggle kernel-source adapter path resolution")
    print("PASS: Kaggle theology_holdouts preferred over corpus txt")
    print("PASS: checkpoint-50 fallback when LoRA missing")
    print("PASS: VL processor does not treat sermon text as image")


if __name__ == "__main__":
    main()
