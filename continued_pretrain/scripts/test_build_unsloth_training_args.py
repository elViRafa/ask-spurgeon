"""Unit tests for UnslothTrainingArguments max_seq_length remap / cosine fallback."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cpt_runtime as cr  # noqa: E402


class _FakeTA:
    """Mock UnslothTrainingArguments / SFTConfig constructor."""

    def __init__(self, *, reject_max_seq_length=True, reject_constant_scheduler=False):
        self.reject_max_seq_length = reject_max_seq_length
        self.reject_constant_scheduler = reject_constant_scheduler
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))
        if self.reject_max_seq_length and "max_seq_length" in kwargs:
            raise TypeError(
                "SFTConfig.__init__() got an unexpected keyword argument 'max_seq_length'"
            )
        if self.reject_constant_scheduler and kwargs.get("lr_scheduler_type") == "constant":
            raise TypeError(
                "SFTConfig.__init__() got an unexpected keyword argument related to "
                "lr_scheduler_type=constant / lr_scheduler_kwargs"
            )
        return {"ok": True, "kwargs": dict(kwargs)}


def test_remap_max_seq_length_keeps_constant_scheduler(capsys):
    ctor = _FakeTA(reject_max_seq_length=True)
    kwargs = {
        "learning_rate": 5e-6,
        "lr_scheduler_type": "constant",
        "max_seq_length": 2048,
        "output_dir": "/tmp/out",
    }
    args, sched, sched_kw = cr.build_unsloth_training_args(
        ctor,
        kwargs,
        lr_scheduler="constant",
        lr_scheduler_kwargs=None,
    )
    out = capsys.readouterr().out
    assert "remapped to max_length=2048" in out
    assert "falling back to cosine" not in out
    assert sched == "constant"
    assert sched_kw is None
    assert args["kwargs"]["max_length"] == 2048
    assert "max_seq_length" not in args["kwargs"]
    assert args["kwargs"]["lr_scheduler_type"] == "constant"
    assert len(ctor.calls) == 2
    assert "max_seq_length" in ctor.calls[0]
    assert "max_length" in ctor.calls[1]


def test_max_seq_length_error_does_not_trigger_cosine_fallback(capsys):
    """Reproduce the m_hi continue crash: max_seq TypeError must not become cosine."""
    ctor = _FakeTA(reject_max_seq_length=True)
    kwargs = {
        "lr_scheduler_type": "constant",
        "max_seq_length": 2048,
    }
    _args, sched, _sched_kw = cr.build_unsloth_training_args(
        ctor,
        kwargs,
        lr_scheduler="constant",
        lr_scheduler_kwargs=None,
    )
    out = capsys.readouterr().out
    assert "falling back to cosine" not in out
    assert sched == "constant"
    # Cosine must never appear in any constructor call for this path.
    assert all(c.get("lr_scheduler_type") == "constant" for c in ctor.calls)


def test_scheduler_error_still_falls_back_to_cosine(capsys):
    ctor = _FakeTA(reject_max_seq_length=False, reject_constant_scheduler=True)
    kwargs = {
        "lr_scheduler_type": "constant",
        "max_length": 2048,
        "lr_scheduler_kwargs": {"min_lr_rate": 0.1},
    }
    args, sched, sched_kw = cr.build_unsloth_training_args(
        ctor,
        kwargs,
        lr_scheduler="constant",
        lr_scheduler_kwargs={"min_lr_rate": 0.1},
    )
    out = capsys.readouterr().out
    assert "falling back to cosine" in out
    assert "remapped to max_length" not in out
    assert sched == "cosine"
    assert sched_kw is None
    assert args["kwargs"]["lr_scheduler_type"] == "cosine"
    assert "lr_scheduler_kwargs" not in args["kwargs"]


def test_remap_then_scheduler_fallback(capsys):
    """After max_seq remap, a scheduler TypeError may still fall back to cosine."""
    ctor = _FakeTA(reject_max_seq_length=True, reject_constant_scheduler=True)
    kwargs = {
        "lr_scheduler_type": "constant",
        "max_seq_length": 1024,
    }
    args, sched, sched_kw = cr.build_unsloth_training_args(
        ctor,
        kwargs,
        lr_scheduler="constant",
        lr_scheduler_kwargs=None,
    )
    out = capsys.readouterr().out
    assert "remapped to max_length=1024" in out
    assert "falling back to cosine" in out
    assert sched == "cosine"
    assert sched_kw is None
    assert args["kwargs"]["max_length"] == 1024
    assert args["kwargs"]["lr_scheduler_type"] == "cosine"
