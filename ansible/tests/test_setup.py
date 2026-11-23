"""Unit tests for the WorkstationManager setup script."""

import importlib.util
import subprocess
from pathlib import Path
from unittest import mock

_SPEC = importlib.util.spec_from_file_location(
    "setup", Path(__file__).parent.parent / "setup.py"
)
setup = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(setup)


def _fake_git(name_val, email_val):
    """Return a subprocess.run stand-in plus a list recording every call."""
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(list(cmd))
        if cmd[:3] == ["git", "config", "--global"] and len(cmd) == 4:
            val = name_val if cmd[3] == "user.name" else email_val
            return subprocess.CompletedProcess(cmd, 0, stdout=(val + "\n") if val else "")
        return subprocess.CompletedProcess(cmd, 0)

    return fake_run, calls


def _writes(calls):
    return [c for c in calls if c[:3] == ["git", "config", "--global"] and len(c) == 5]


def test_configure_git_prompts_and_sets_when_unset():
    fake_run, calls = _fake_git("", "")
    with mock.patch.object(setup.subprocess, "run", fake_run), \
            mock.patch("builtins.input", side_effect=["Alice", "alice@example.com"]):
        setup.WorkstationManager().configure_git()

    assert ["git", "config", "--global", "user.name", "Alice"] in _writes(calls)
    assert ["git", "config", "--global", "user.email", "alice@example.com"] in _writes(calls)


def test_configure_git_skips_when_already_set():
    fake_run, calls = _fake_git("Bob", "bob@example.com")
    with mock.patch.object(setup.subprocess, "run", fake_run), \
            mock.patch("builtins.input", side_effect=AssertionError("should not prompt")):
        setup.WorkstationManager().configure_git()

    assert _writes(calls) == []


def test_configure_git_skips_blank_input():
    fake_run, calls = _fake_git("", "")
    with mock.patch.object(setup.subprocess, "run", fake_run), \
            mock.patch("builtins.input", side_effect=["", ""]):
        setup.WorkstationManager().configure_git()

    assert _writes(calls) == []
