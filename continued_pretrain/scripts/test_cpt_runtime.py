#!/usr/bin/env python3
"""Unit tests for cpt_runtime.py (path / GPU / resume / dtype / save policy)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cpt_runtime as cr  # noqa: E402


def _write(path: Path, text: str = "{}") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_resolve_work_root_env(tmp_path: Path) -> None:
    target = tmp_path / "vol"
    target.mkdir()
    env = {"CPT_WORK_ROOT": str(target)}
    assert Path(cr.resolve_work_root(env=env)) == target.resolve()


def test_layout_paths(tmp_path: Path) -> None:
    layout = cr.layout_paths(str(tmp_path))
    assert layout["output_dir"] == str(tmp_path / "checkpoints_sota")
    assert layout["adapter_out"].endswith("theology_cpt_lora")


def test_find_hf_dataset_nested_and_flat(tmp_path: Path) -> None:
    nested = tmp_path / "a_output" / "theology_dataset"
    _write(nested / "dataset_dict.json")
    found = cr.find_hf_dataset_root([str(tmp_path / "a_output")])
    assert found == str(nested)

    flat = tmp_path / "theology-cpt-dataset"
    _write(flat / "dataset_dict.json")
    found2 = cr.find_hf_dataset_root([str(flat)])
    assert found2 == str(flat)


def test_find_hf_holdout_root(tmp_path: Path) -> None:
    hold = tmp_path / "theology_holdouts" / "spurgeon"
    _write(hold / "dataset_info.json")
    found = cr.find_hf_holdout_root([str(tmp_path / "theology_holdouts")])
    assert found == str(tmp_path / "theology_holdouts")

    buried = tmp_path / "kaggle" / "input" / "theology-cpt-dataset" / "theology_holdouts"
    _write(buried / "spurgeon" / "state.json")
    found2 = cr.find_hf_holdout_root(
        [],
        walk_roots=[str(tmp_path / "kaggle" / "input")],
    )
    assert found2 == str(buried)


def test_find_highest_checkpoint(tmp_path: Path) -> None:
    root = tmp_path / "checkpoints_sota"
    _write(root / "checkpoint-50" / "trainer_state.json")
    _write(root / "checkpoint-100" / "trainer_state.json")
    (root / "checkpoint-75").mkdir(parents=True)  # incomplete — no trainer_state
    found = cr.find_highest_checkpoint(str(root))
    assert found == str(root / "checkpoint-100")


def test_resolve_prev_checkpoint_force_fresh(tmp_path: Path) -> None:
    root = tmp_path / "checkpoints_sota"
    _write(root / "checkpoint-25" / "trainer_state.json")
    env = {"PREV_RUN_CHECKPOINT": ""}
    assert cr.resolve_prev_checkpoint(str(tmp_path), env=env, kaggle_input=str(tmp_path / "none")) is None


def test_resolve_prev_checkpoint_explicit(tmp_path: Path) -> None:
    ckpt = tmp_path / "ckpt"
    env = {"PREV_RUN_CHECKPOINT": str(ckpt)}
    assert cr.resolve_prev_checkpoint(str(tmp_path), env=env) == str(ckpt)


def test_resolve_prev_checkpoint_auto_local(tmp_path: Path) -> None:
    root = tmp_path / "checkpoints_sota"
    _write(root / "checkpoint-25" / "trainer_state.json")
    _write(root / "checkpoint-75" / "trainer_state.json")
    env = {}
    found = cr.resolve_prev_checkpoint(str(tmp_path), env=env, kaggle_input=str(tmp_path / "missing"))
    assert found == str(root / "checkpoint-75")


def test_resolve_prev_checkpoint_kaggle_input_only(tmp_path: Path) -> None:
    work = tmp_path / "working"
    work.mkdir(parents=True)
    kaggle_in = tmp_path / "input"
    ckpt = (
        kaggle_in
        / "notebooks"
        / "rafaelvieira1"
        / "theology-cpt-v2-b-training-sota"
        / "checkpoints_sota"
        / "checkpoint-100"
    )
    _write(ckpt / "trainer_state.json")
    found = cr.resolve_prev_checkpoint(str(work), env={}, kaggle_input=str(kaggle_in))
    assert found == str(ckpt)


def test_gpu_profile() -> None:
    assert cr.resolve_gpu_profile(cc_major=8, env={}) == "ampere"
    assert cr.resolve_gpu_profile(cc_major=7, env={}) == "t4"
    assert cr.resolve_gpu_profile(cc_major=8, env={"GPU_PROFILE": "t4"}) == "t4"
    assert cr.resolve_gpu_profile(cc_major=7, env={"GPU_PROFILE": "ampere"}) == "ampere"
    assert cr.resolve_gpu_profile(cc_major=None, env={}) == "t4"


def test_trainer_mixed_precision() -> None:
    # Ampere / Ada: bf16 even with embed LoRA
    assert cr.trainer_mixed_precision(train_embeddings=True, bf16_supported=True) == (False, True)
    assert cr.trainer_mixed_precision(train_embeddings=False, bf16_supported=True) == (False, True)
    # T4 + embeds: float32
    assert cr.trainer_mixed_precision(train_embeddings=True, bf16_supported=False) == (False, False)
    # T4 no embeds: fp16
    assert cr.trainer_mixed_precision(train_embeddings=False, bf16_supported=False) == (True, False)


def test_checkpoint_save_policy(tmp_path: Path) -> None:
    runpod = cr.checkpoint_save_policy(str(tmp_path))
    assert runpod == {"save_total_limit": 3, "save_only_model": False}
    kaggle = cr.checkpoint_save_policy("/kaggle/working")
    assert kaggle == {"save_total_limit": 1, "save_only_model": True}


def test_sha256_file_and_local_lora_dir(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    blob = tmp_path / "adapter_model.safetensors"
    blob.write_bytes(b"cpt-adapter-bytes")
    digest = cr.sha256_file(str(blob))
    assert digest == __import__("hashlib").sha256(b"cpt-adapter-bytes").hexdigest()
    assert cr.local_lora_dir(str(tmp_path)) is None
    lora = tmp_path / "theology_cpt_lora"
    _write(lora / "adapter_config.json")
    assert cr.local_lora_dir(str(tmp_path)) == str(lora)


def test_find_adapter_prefers_final_lora(tmp_path: Path) -> None:
    kernel = tmp_path / "notebooks" / "rafaelvieira1" / "theology-cpt-v2-b-training-sota"
    lora = kernel / "theology_cpt_lora"
    ckpt = kernel / "checkpoints_sota" / "checkpoint-50"
    decoy = kernel / "hf_home" / "hub" / "models--x" / "adapters"
    _write(lora / "adapter_config.json")
    _write(ckpt / "adapter_config.json")
    _write(decoy / "adapter_config.json")
    found = cr.find_adapter([str(tmp_path)])
    assert found == str(lora)


def test_find_file_mcq(tmp_path: Path) -> None:
    corpus = tmp_path / "theology-cpt-corpus"
    _write(corpus / "catechism_mcq.json", '{"sets":{}}')
    found = cr.find_file("catechism_mcq.json", [str(tmp_path)], prefer_substrings=("theology-cpt-corpus",))
    assert found == str(corpus / "catechism_mcq.json")


def test_spurgeon_rose_by_step() -> None:
    hist_rise = [
        {"step": 25, "loss": 2.1},
        {"step": 25, "eval_spurgeon_loss": 2.33},
        {"step": 50, "loss": 2.0},
        {"step": 50, "eval_spurgeon_loss": 2.40},
    ]
    assert cr.spurgeon_rose_by_step(hist_rise) is True
    hist_flat = [
        {"step": 25, "eval_spurgeon_loss": 2.33},
        {"step": 50, "eval_spurgeon_loss": 2.33},
    ]
    assert cr.spurgeon_rose_by_step(hist_flat) is False
    hist_fall = [
        {"step": 25, "eval_spurgeon_loss": 2.33},
        {"step": 50, "eval_spurgeon_loss": 2.30},
    ]
    assert cr.spurgeon_rose_by_step(hist_fall) is False
    assert cr.spurgeon_rose_by_step([{"step": 50, "eval_spurgeon_loss": 2.4}]) is False
    assert cr.spurgeon_rose_by_step([]) is False
    assert cr.spurgeon_loss_at_step(hist_rise, 25) == 2.33
    assert cr.spurgeon_loss_at_step(hist_rise, 50) == 2.40


def test_resolve_run_mode() -> None:
    assert cr.resolve_run_mode(env={}) == "fresh"
    assert cr.resolve_run_mode(env={"CPT_RUN_MODE": "continue"}) == "continue"
    assert cr.resolve_run_mode(env={"CPT_RUN_MODE": "CONTINUE"}) == "continue"


def test_resolve_continue_training_config() -> None:
    env = {"CPT_RUN_MODE": "continue"}
    cfg = cr.resolve_continue_training_config(env=env, packed_epoch_steps=4128)
    assert cfg["learning_rate"] == 4e-6
    assert cfg["embedding_learning_rate"] == 1.5e-6
    assert cfg["abort_spurgeon_step"] == 0
    assert cfg["eval_docs_per_bucket"] == 16
    assert cfg["eval_buckets_during_train"] == ["spurgeon", "puritan", "confession"]
    assert cfg["early_stop_min_steps"] == 1652  # ceil(0.4 * 4128)
    assert cfg["use_composite_early_stop"] is True
    assert cr.resolve_continue_training_config(env={}, packed_epoch_steps=100) == {}


def test_composite_flat_state_s5_like() -> None:
    """Spurgeon flat while mix still improves — streak must not accumulate to halt."""
    metrics = [
        {"eval_spurgeon_loss": 2.254, "eval_mix_loss": 2.085},
        {"eval_spurgeon_loss": 2.254, "eval_mix_loss": 2.050},
        {"eval_spurgeon_loss": 2.255, "eval_mix_loss": 2.029},
    ]
    keys = ["eval_spurgeon_loss", "eval_mix_loss"]
    bests = {}
    streak = 0
    for row in metrics:
        bests, streak, improved = cr.update_composite_flat_state(
            bests, streak, row, keys, epsilon=0.005
        )
        assert improved is True
    assert streak == 0
    assert cr.composite_should_halt(streak, patience=2) is False


def test_composite_flat_state_both_flat_halts() -> None:
    metrics = [
        {"eval_spurgeon_loss": 2.254, "eval_mix_loss": 2.029},
        {"eval_spurgeon_loss": 2.254, "eval_mix_loss": 2.028},
        {"eval_spurgeon_loss": 2.255, "eval_mix_loss": 2.027},
    ]
    keys = ["eval_spurgeon_loss", "eval_mix_loss"]
    bests = {}
    streak = 0
    for row in metrics:
        bests, streak, _improved = cr.update_composite_flat_state(
            bests, streak, row, keys, epsilon=0.005
        )
    assert streak == 2
    assert cr.composite_should_halt(streak, patience=2) is True


def test_metric_improved() -> None:
    assert cr.metric_improved(2.20, 2.25, 0.005) is True
    assert cr.metric_improved(2.246, 2.25, 0.005) is False
    assert cr.metric_improved(2.255, 2.25, 0.005) is False


def test_resolve_init_adapter_env_and_local(tmp_path: Path) -> None:
    base = tmp_path / "init"
    base.mkdir(parents=True)
    work = base / "work"
    work.mkdir()
    lora = work / "theology_cpt_lora"
    _write(lora / "adapter_config.json")
    env = {"CPT_RUN_MODE": "continue", "CPT_INIT_ADAPTER": str(work / "custom_lora")}
    _write(work / "custom_lora" / "adapter_config.json")
    assert cr.resolve_init_adapter(str(work), env=env) == str(work / "custom_lora")
    env2 = {"CPT_RUN_MODE": "continue"}
    assert cr.resolve_init_adapter(str(work), env=env2) == str(lora)
    assert cr.resolve_init_adapter(str(work), env={}) is None


def test_dataset_search_includes_a_output_v3(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir(parents=True)
    data = work / "a_output_v3" / "theology_dataset"
    _write(data / "dataset_dict.json")
    roots = cr.dataset_search_roots(
        str(work),
        env={},
        kaggle_input=str(tmp_path / "nope"),
        cwd=str(tmp_path),
    )
    assert any("a_output_v3" in root for root in roots)
    found = cr.find_hf_dataset_root(roots)
    assert found == str(data)


def test_dataset_search_uses_cpt_data_root(tmp_path: Path) -> None:
    data = tmp_path / "data"
    _write(data / "theology_dataset" / "dataset_dict.json")
    env = {"CPT_DATA_ROOT": str(data)}
    roots = cr.dataset_search_roots(str(tmp_path / "work"), env=env, kaggle_input=str(tmp_path / "nope"), cwd=str(tmp_path))
    found = cr.find_hf_dataset_root(roots)
    assert found == str(data / "theology_dataset")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        test_resolve_work_root_env(tmp_path)
        test_layout_paths(tmp_path)
        test_find_hf_dataset_nested_and_flat(tmp_path / "ds")
        test_find_hf_holdout_root(tmp_path / "ho")
        test_find_highest_checkpoint(tmp_path / "ck")
        test_resolve_prev_checkpoint_force_fresh(tmp_path / "fresh")
        test_resolve_prev_checkpoint_explicit(tmp_path / "expl")
        test_resolve_prev_checkpoint_auto_local(tmp_path / "auto")
        test_resolve_prev_checkpoint_kaggle_input_only(tmp_path / "kag")
        test_gpu_profile()
        test_trainer_mixed_precision()
        test_checkpoint_save_policy(tmp_path / "vol")
        test_sha256_file_and_local_lora_dir(tmp_path / "sha")
        test_find_adapter_prefers_final_lora(tmp_path / "ad")
        test_find_file_mcq(tmp_path / "mcq")
        test_spurgeon_rose_by_step()
        test_resolve_run_mode()
        test_resolve_continue_training_config()
        test_composite_flat_state_s5_like()
        test_composite_flat_state_both_flat_halts()
        test_metric_improved()
        test_resolve_init_adapter_env_and_local(tmp_path)
        test_dataset_search_includes_a_output_v3(tmp_path)
        test_dataset_search_uses_cpt_data_root(tmp_path / "envds")
    print("PASS: work_root env")
    print("PASS: layout_paths")
    print("PASS: HF dataset nested/flat")
    print("PASS: HF holdout + walk")
    print("PASS: highest checkpoint")
    print("PASS: PREV_RUN_CHECKPOINT empty = fresh")
    print("PASS: PREV_RUN_CHECKPOINT explicit")
    print("PASS: auto-resume local work_root")
    print("PASS: auto-resume kaggle input walker")
    print("PASS: GPU_PROFILE auto + env override")
    print("PASS: trainer mixed precision (bf16+embeds)")
    print("PASS: save policy kaggle vs runpod")
    print("PASS: sha256_file + local_lora_dir")
    print("PASS: adapter prefers final LoRA")
    print("PASS: catechism_mcq find")
    print("PASS: abort if eval_spurgeon rose by step 50")
    print("PASS: CPT_RUN_MODE fresh/continue")
    print("PASS: continue training config")
    print("PASS: composite flat S5-like (mix still improving)")
    print("PASS: composite flat both-flat halt")
    print("PASS: metric_improved epsilon")
    print("PASS: resolve_init_adapter env/local")
    print("PASS: a_output_v3 dataset search")
    print("PASS: CPT_DATA_ROOT dataset search")


if __name__ == "__main__":
    main()
