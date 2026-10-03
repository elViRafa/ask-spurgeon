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


def test_choose_seq_length_kwarg_prefers_max_length() -> None:
    class NewSFT:
        def __init__(self, max_length=None, packing=False, **kwargs):
            pass

    class OldSFT:
        def __init__(self, max_seq_length=None, packing=False, **kwargs):
            pass

    class KwargsOnly:
        def __init__(self, **kwargs):
            pass

    assert cr.choose_seq_length_kwarg(NewSFT) == "max_length"
    assert cr.choose_seq_length_kwarg(OldSFT) == "max_seq_length"
    # **kwargs only → legacy name; TypeError remap handles TRL 0.24 reject
    assert cr.choose_seq_length_kwarg(KwargsOnly) == "max_seq_length"


def test_classify_training_args_typeerror_remap_max_seq_length() -> None:
    err = TypeError(
        "SFTConfig.__init__() got an unexpected keyword argument 'max_seq_length'"
    )
    kwargs = {"max_seq_length": 2048, "lr_scheduler_type": "cosine_with_min_lr"}
    action, warn = cr.classify_training_args_typeerror(
        err, kwargs, "cosine_with_min_lr", {"min_lr": 1e-6}
    )
    assert action == "remap_max_length"
    assert "max_length" in (warn or "")
    # Must NOT fall back to cosine when the error is max_seq_length
    assert action != "fallback_cosine"


def test_classify_training_args_typeerror_fallback_cosine_only_for_scheduler() -> None:
    err = TypeError(
        "TrainingArguments.__init__() got an unexpected keyword argument 'lr_scheduler_kwargs'"
    )
    kwargs = {"max_seq_length": 2048, "lr_scheduler_kwargs": {"min_lr": 1e-6}}
    action, warn = cr.classify_training_args_typeerror(
        err, kwargs, "cosine_with_min_lr", {"min_lr": 1e-6}
    )
    assert action == "fallback_cosine"
    assert "cosine" in (warn or "")


def test_classify_training_args_typeerror_unrelated_raises() -> None:
    err = TypeError("SFTConfig.__init__() got an unexpected keyword argument 'bogus'")
    kwargs = {"max_seq_length": 2048, "lr_scheduler_type": "cosine_with_min_lr"}
    action, warn = cr.classify_training_args_typeerror(
        err, kwargs, "cosine_with_min_lr", {"min_lr": 1e-6}
    )
    assert action == "raise"
    assert warn is None


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
    assert cfg["composite_early_stop_metrics"] == ["eval_spurgeon_loss", "eval_mix_loss"]
    assert cfg.get("continue_profile") == ""
    assert cfg.get("continue_max_steps") is None
    assert cr.resolve_continue_training_config(env={}, packed_epoch_steps=100) == {}


def test_resolve_continue_training_config_s7(tmp_path: Path) -> None:
    work = tmp_path / "s7work"
    work.mkdir(parents=True)
    env = {
        "CPT_RUN_MODE": "continue",
        "CPT_CONTINUE_PROFILE": "s7",
        "CPT_WORK_ROOT": str(work),
    }
    cfg = cr.resolve_continue_training_config(env=env, packed_epoch_steps=4128)
    assert cfg["continue_profile"] == "s7"
    assert cfg["learning_rate"] == 2e-6
    assert cfg["embedding_learning_rate"] == 8e-7
    assert cfg["warmup_ratio"] == 0.04
    assert cfg["early_stop_min_steps"] == 400  # not 0.4*4128
    assert cfg["early_stop_patience"] == 4
    assert cfg["early_stop_epsilon"] == 0.003
    assert cfg["eval_steps"] == 50
    assert cfg["save_steps"] == 50
    assert cfg["lr_scheduler_type"] == "cosine_with_min_lr"
    assert cfg["lr_scheduler_kwargs"] == {"min_lr_rate": 0.1}
    assert cfg["continue_max_steps"] == 955
    assert cfg["output_dir"] == str(work / "checkpoints_s7")
    assert cfg["eval_buckets_during_train"] == [
        "spurgeon",
        "puritan",
        "confession",
        "general",
        "new_authors",
    ]
    assert "eval_general_loss" not in cfg["composite_early_stop_metrics"]
    assert "eval_new_authors_loss" not in cfg["composite_early_stop_metrics"]
    assert cfg["composite_early_stop_metrics"] == [
        "eval_spurgeon_loss",
        "eval_puritan_loss",
        "eval_confession_loss",
    ]
    assert "eval_mix_loss" not in cfg["composite_early_stop_metrics"]
    assert cfg["composite_seed_bests"]["eval_spurgeon_loss"] == 2.4987
    assert "eval_mix_loss" not in cfg["composite_seed_bests"]
    # In-train @ ckpt-2050 — not isolation-C full-holdout CE
    assert cfg["composite_seed_bests"]["eval_puritan_loss"] == 1.751
    assert cfg["composite_seed_bests"]["eval_confession_loss"] == 1.668
    assert cfg["abort_spurgeon_delta"] == 0.12
    assert cfg["s5_spurgeon_guardrail"] == 0.01
    assert cfg["metric_for_best"] == "eval_puritan_loss"
    assert cfg["s5_best_adapter_dir"] == str(work / "theology_cpt_lora_s5best")
    env_metric = dict(env)
    env_metric["METRIC_FOR_BEST"] = "eval_spurgeon_loss"
    cfg2 = cr.resolve_continue_training_config(env=env_metric, packed_epoch_steps=100)
    assert cfg2["metric_for_best"] == "eval_spurgeon_loss"
    layout = cr.layout_paths(str(work), env=env)
    assert layout["output_dir"] == str(work / "checkpoints_s7")


def test_s7_replay_drops_mix_from_composite() -> None:
    env = {
        "CPT_RUN_MODE": "continue",
        "CPT_CONTINUE_PROFILE": "s7",
        "COMPOSITE_EARLY_STOP_METRICS": (
            "eval_spurgeon_loss,eval_puritan_loss,eval_confession_loss"
        ),
    }
    cfg = cr.resolve_continue_training_config(env=env, packed_epoch_steps=100)
    assert cfg["composite_early_stop_metrics"] == [
        "eval_spurgeon_loss",
        "eval_puritan_loss",
        "eval_confession_loss",
    ]
    assert "eval_mix_loss" not in cfg["composite_early_stop_metrics"]


def test_s5_best_should_save_guardrail() -> None:
    seed = 2.4987
    s5 = cr.s5_loss_from_metrics(
        {"eval_puritan_loss": 1.70, "eval_confession_loss": 1.60}
    )
    assert abs(s5 - 1.65) < 1e-9
    # First s5 with spurgeon within guardrail → save
    assert cr.s5_best_should_save(s5, None, 2.50, seed, guardrail=0.01) is True
    # Spurgeon past guardrail → no save even if s5 improves
    assert cr.s5_best_should_save(1.50, 1.65, 2.52, seed, guardrail=0.01) is False
    # Better s5 + spurgeon OK → save
    assert cr.s5_best_should_save(1.60, 1.65, 2.505, seed, guardrail=0.01) is True
    # Worse s5 → no save
    assert cr.s5_best_should_save(1.70, 1.65, 2.50, seed, guardrail=0.01) is False


def test_seed_regression_abort_two_cycles() -> None:
    seed = 2.4987
    delta = 0.12
    streak = 0
    streak = cr.seed_regression_streak(2.62, seed, delta, streak)
    assert streak == 1
    assert cr.seed_regression_should_abort(streak, required=2) is False
    streak = cr.seed_regression_streak(2.63, seed, delta, streak)
    assert streak == 2
    assert cr.seed_regression_should_abort(streak, required=2) is True
    # Recovery resets
    streak = cr.seed_regression_streak(2.50, seed, delta, streak)
    assert streak == 0


def test_composite_seed_bests_spike_does_not_replace_seed() -> None:
    """First eval worse than S6 seed must not become the halt baseline."""
    keys = [
        "eval_spurgeon_loss",
        "eval_mix_loss",
        "eval_puritan_loss",
        "eval_confession_loss",
    ]
    seed = dict(cr.S7_DEFAULT_COMPOSITE_SEED_BESTS)
    seed["eval_mix_loss"] = 2.0208
    # Spike like S6 resume at 2075
    spiked = {
        "eval_spurgeon_loss": 2.6185,
        "eval_mix_loss": 2.1157,
        "eval_puritan_loss": 1.834,
        "eval_confession_loss": 1.755,
    }
    bests, streak, improved = cr.update_composite_flat_state(
        seed, 0, spiked, keys, epsilon=0.005
    )
    assert improved is False
    assert streak == 1
    assert bests["eval_spurgeon_loss"] == 2.4987
    # Flat again vs seed → streak 2 → halt
    bests, streak, improved = cr.update_composite_flat_state(
        bests, streak, spiked, keys, epsilon=0.005
    )
    assert improved is False
    assert streak == 2
    assert cr.composite_should_halt(streak, patience=2) is True


def test_s7_empty_prev_ignores_leftover_sota(tmp_path: Path) -> None:
    """PREV_RUN_CHECKPOINT='' must force fresh even when checkpoints_sota exists."""
    sota = tmp_path / "checkpoints_sota" / "checkpoint-2400"
    sota.mkdir(parents=True)
    _write(sota / "trainer_state.json")
    env = {
        "CPT_RUN_MODE": "continue",
        "CPT_CONTINUE_PROFILE": "s7",
        "PREV_RUN_CHECKPOINT": "",
    }
    assert (
        cr.resolve_prev_checkpoint(str(tmp_path), env=env, kaggle_input=str(tmp_path / "none"))
        is None
    )
    # Unset PREV with s7 profile must not auto-pick sota either
    env2 = {"CPT_RUN_MODE": "continue", "CPT_CONTINUE_PROFILE": "s7"}
    assert (
        cr.resolve_prev_checkpoint(str(tmp_path), env=env2, kaggle_input=str(tmp_path / "none"))
        is None
    )
    # Mid-S7: highest under checkpoints_s7 only
    s7 = tmp_path / "checkpoints_s7"
    _write(s7 / "checkpoint-100" / "trainer_state.json")
    _write(s7 / "checkpoint-250" / "trainer_state.json")
    found = cr.resolve_prev_checkpoint(
        str(tmp_path), env=env2, kaggle_input=str(tmp_path / "none")
    )
    assert found == str(s7 / "checkpoint-250")


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


def test_merge_eval_event_split_hf_cycle() -> None:
    """Mix then Spurgeon at the same step become one complete cycle."""
    keys = ["eval_spurgeon_loss", "eval_mix_loss"]
    cache = {}
    cache, merged = cr.merge_eval_event_for_step(
        cache, 25, {"eval_mix_loss": 2.085}, keys
    )
    assert merged is None
    assert cache[25]["eval_mix_loss"] == 2.085
    cache, merged = cr.merge_eval_event_for_step(
        cache, 25, {"eval_spurgeon_loss": 2.292}, keys
    )
    assert merged == {"eval_mix_loss": 2.085, "eval_spurgeon_loss": 2.292}
    assert 25 not in cache


def test_merge_eval_event_combined_dict_completes_immediately() -> None:
    keys = ["eval_spurgeon_loss", "eval_mix_loss"]
    cache, merged = cr.merge_eval_event_for_step(
        {},
        50,
        {"eval_spurgeon_loss": 2.29, "eval_mix_loss": 2.07},
        keys,
    )
    assert merged["eval_spurgeon_loss"] == 2.29
    assert merged["eval_mix_loss"] == 2.07
    assert cache == {}


def test_composite_split_events_s5_like_no_halt() -> None:
    """S5-like: sequential HF events; mix still falling so composite must not halt."""
    keys = ["eval_spurgeon_loss", "eval_mix_loss"]
    events = [
        (325, {"eval_mix_loss": 2.085}),
        (325, {"eval_spurgeon_loss": 2.254}),
        (350, {"eval_mix_loss": 2.050}),
        (350, {"eval_spurgeon_loss": 2.254}),
        (375, {"eval_mix_loss": 2.029}),
        (375, {"eval_spurgeon_loss": 2.255}),
    ]
    cache = {}
    bests = {}
    streak = 0
    for step, metrics in events:
        cache, merged = cr.merge_eval_event_for_step(cache, step, metrics, keys)
        if merged is None:
            continue
        bests, streak, _improved = cr.update_composite_flat_state(
            bests, streak, merged, keys, epsilon=0.005
        )
    assert streak == 0
    assert cr.composite_should_halt(streak, patience=2) is False


def test_composite_split_events_both_flat_halts() -> None:
    keys = ["eval_spurgeon_loss", "eval_mix_loss"]
    events = [
        (2000, {"eval_mix_loss": 2.029}),
        (2000, {"eval_spurgeon_loss": 2.254}),
        (2025, {"eval_mix_loss": 2.028}),
        (2025, {"eval_spurgeon_loss": 2.254}),
        (2050, {"eval_mix_loss": 2.027}),
        (2050, {"eval_spurgeon_loss": 2.255}),
    ]
    cache = {}
    bests = {}
    streak = 0
    for step, metrics in events:
        cache, merged = cr.merge_eval_event_for_step(cache, step, metrics, keys)
        if merged is None:
            continue
        bests, streak, _improved = cr.update_composite_flat_state(
            bests, streak, merged, keys, epsilon=0.005
        )
    assert streak == 2
    assert cr.composite_should_halt(streak, patience=2) is True


def test_split_events_without_merge_never_halt() -> None:
    """Document the old bug: feeding one bucket at a time never completes a cycle."""
    keys = ["eval_spurgeon_loss", "eval_mix_loss"]
    bests = {}
    streak = 0
    for metrics in (
        {"eval_mix_loss": 2.029},
        {"eval_spurgeon_loss": 2.254},
        {"eval_mix_loss": 2.028},
        {"eval_spurgeon_loss": 2.254},
    ):
        bests, streak, improved = cr.update_composite_flat_state(
            bests, streak, metrics, keys, epsilon=0.005
        )
        assert improved is True
    assert cr.composite_should_halt(streak, patience=2) is False


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
    assert any("a_output_v4" in root for root in roots)
    assert any("a_output_v5" in root for root in roots)
    assert any("a_output_v6" in root for root in roots)
    found = cr.find_hf_dataset_root(roots)
    assert found == str(data)


def test_dataset_search_prefers_a_output_v6(tmp_path: Path) -> None:
    work = tmp_path / "work"
    v3 = work / "a_output_v3" / "theology_dataset"
    v4 = work / "a_output_v4" / "theology_dataset"
    v5 = work / "a_output_v5" / "theology_dataset"
    v6 = work / "a_output_v6" / "theology_dataset"
    _write(v3 / "dataset_dict.json")
    _write(v4 / "dataset_dict.json")
    _write(v5 / "dataset_dict.json")
    _write(v6 / "dataset_dict.json")
    roots = cr.dataset_search_roots(
        str(work),
        env={},
        kaggle_input=str(tmp_path / "nope"),
        cwd=str(tmp_path),
    )
    found = cr.find_hf_dataset_root(roots)
    assert found == str(v6)


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
        test_resolve_continue_training_config_s7(tmp_path / "s7cfg")
        test_s7_replay_drops_mix_from_composite()
        test_s5_best_should_save_guardrail()
        test_seed_regression_abort_two_cycles()
        test_composite_seed_bests_spike_does_not_replace_seed()
        test_s7_empty_prev_ignores_leftover_sota(tmp_path / "s7prev")
        test_composite_flat_state_s5_like()
        test_composite_flat_state_both_flat_halts()
        test_merge_eval_event_split_hf_cycle()
        test_merge_eval_event_combined_dict_completes_immediately()
        test_composite_split_events_s5_like_no_halt()
        test_composite_split_events_both_flat_halts()
        test_split_events_without_merge_never_halt()
        test_metric_improved()
        test_resolve_init_adapter_env_and_local(tmp_path)
        test_dataset_search_includes_a_output_v3(tmp_path)
        test_dataset_search_prefers_a_output_v6(tmp_path / "v6pref")
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
    print("PASS: S7 continue profile")
    print("PASS: s5_best guardrail")
    print("PASS: seed regression abort")
    print("PASS: composite seed resists spike")
    print("PASS: S7 empty PREV ignores sota ckpts")
    print("PASS: composite flat S5-like (mix still improving)")
    print("PASS: composite flat both-flat halt")
    print("PASS: merge split HF eval events")
    print("PASS: merge combined eval dict")
    print("PASS: composite split-event S5-like no halt")
    print("PASS: composite split-event both-flat halt")
    print("PASS: unmerged split events never halt")
    print("PASS: metric_improved epsilon")
    print("PASS: resolve_init_adapter env/local")
    print("PASS: a_output_v3 dataset search")
    print("PASS: a_output_v6 preferred over v5/v4/v3")
    print("PASS: CPT_DATA_ROOT dataset search")


if __name__ == "__main__":
    main()
