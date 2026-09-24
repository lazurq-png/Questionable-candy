"""ensure_cluster() in scripts/dev.py: start the local PostgreSQL if it is down.

It must do nothing under CI (the database is a service container) or where no
local install exists, and when it does start the cluster it must detach it and
say so -- an unattended run reads that line to learn the cluster went down.
"""
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "dev.py"
spec = importlib.util.spec_from_file_location("dev", SCRIPT)
dev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dev)


@pytest.fixture(name="pg")
def fixture_pg(tmp_path, monkeypatch):
    """A fake install under tmp_path, with pg_isready answers scripted per test."""
    suffix = ".exe" if dev.os.name == "nt" else ""
    (tmp_path / "bin").mkdir()
    for name in ("pg_isready", "pg_ctl"):
        (tmp_path / "bin" / (name + suffix)).write_text("")
    monkeypatch.setattr(dev, "PGSQL_HOME", tmp_path)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setattr(dev.time, "sleep", lambda _: None)

    state = {"answers": [], "started": []}
    monkeypatch.setattr(dev, "_pg_isready", lambda _: state["answers"].pop(0))
    monkeypatch.setattr(
        dev.subprocess, "Popen", lambda cmd, **kw: state["started"].append((cmd, kw))
    )
    return state


def test_ready_cluster_is_left_alone(pg):
    pg["answers"] = [dev.PG_READY]
    assert dev.ensure_cluster() == 0
    assert not pg["started"]


def test_down_cluster_is_started_detached_and_announced(pg, capsys):
    pg["answers"] = [dev.PG_DOWN, dev.PG_DOWN, dev.PG_READY]
    assert dev.ensure_cluster() == 0

    [(cmd, kwargs)] = pg["started"]
    assert cmd[1] == "start"
    assert "creationflags" in kwargs or kwargs.get("start_new_session")
    assert "is down -- starting it" in capsys.readouterr().out


def test_starting_cluster_is_waited_for_not_started_again(pg):
    pg["answers"] = [dev.PG_STARTING, dev.PG_READY]
    assert dev.ensure_cluster() == 0
    assert not pg["started"]


def test_cluster_that_never_comes_up_fails(pg, monkeypatch):
    clock = iter(range(0, 1000, 10))
    monkeypatch.setattr(dev.time, "monotonic", lambda: next(clock))
    pg["answers"] = [dev.PG_DOWN] * 100
    assert dev.ensure_cluster() == 1


def test_skipped_under_ci(pg, monkeypatch):
    monkeypatch.setenv("CI", "true")
    assert dev.ensure_cluster() == 0
    assert not pg["answers"] and not pg["started"]


def test_skipped_without_a_local_install(pg, monkeypatch, tmp_path):
    monkeypatch.setattr(dev, "PGSQL_HOME", tmp_path / "nowhere")
    assert dev.ensure_cluster() == 0
    assert not pg["started"]
