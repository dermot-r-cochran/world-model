"""The README's quick start runs the worked example, and a reader who runs it
once runs it again. Until 2026-11-11 the second run ended in a traceback: the
example keeps its world in ./document_example.db, and the runtime refuses an
identity that already exists (ADR-002), so the world the first run left behind
refused the second."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "document_extraction" / "run_example.py"


def _run_example(cwd: Path) -> subprocess.CompletedProcess[str]:
    # The quick start's own command, as its own process, in a directory of its
    # own. src/ goes on the path so this holds with or without an install.
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT / "src"), env.get("PYTHONPATH")]))
    return subprocess.run(
        [sys.executable, str(EXAMPLE)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_regression_the_worked_example_runs_a_second_time(tmp_path):
    first = _run_example(tmp_path)
    second = _run_example(tmp_path)

    for run in (first, second):
        assert run.returncode == 0, run.stderr
        assert "Invariant violations: 0" in run.stdout
        assert "ALIGNMENT_STRATEGY_MISMATCH" in run.stdout
        # Each run reports one world built once, not the earlier run's world
        # with a second claim appended to it.
        assert run.stdout.count("'claim_created'") == 1

    # The world stays on disk after the run, to be opened and read.
    assert (tmp_path / "document_example.db").exists()
