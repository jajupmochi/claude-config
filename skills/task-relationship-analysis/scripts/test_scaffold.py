#!/usr/bin/env python3
"""Tests for scaffold.py (task-relationship-analysis). Run: python3 test_scaffold.py"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("scaffold", os.path.join(HERE, "scaffold.py"))
sc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sc)


def run():
    # 1. N tasks -> exactly C(N,2) pairwise rows (every unordered pair once, none skipped)
    for n in (2, 3, 5):
        tasks = [f"t{i}" for i in range(n)]
        out = sc.scaffold(tasks)
        rows = [ln for ln in out.splitlines() if ln.startswith("| ") and "×" in ln]
        expected = n * (n - 1) // 2
        assert len(rows) == expected, f"n={n}: {len(rows)} pair rows, want {expected}"
        assert f"Pairs to consider: {expected}." in out

    # 2. task labels are listed and numbered
    out = sc.scaffold(["design API", "write tests", "deploy"])
    assert "1. design API" in out and "2. write tests" in out and "3. deploy" in out

    # 3. legend + checklist present (the anti-mechanical-execution guard)
    assert "SYN=synergy" in out and "Shared substrate" in out and "Ordering / DAG" in out
    assert "Do NOT start executing tasks in listed order" in out

    # 4. empty input -> graceful, no matrix, no crash
    out0 = sc.scaffold([])
    assert "No tasks provided" in out0 and "×" not in out0

    # 5. whitespace-only entries are dropped (scope to the Tasks section, before the matrix)
    out_ws = sc.scaffold(["a", "  ", "", "b"])
    lines = out_ws.splitlines()
    tasks_sec = lines[lines.index("## Tasks") + 1 : lines.index("## Pairwise matrix")]
    listed = [ln for ln in tasks_sec if ln.strip()]
    assert listed == ["1. a", "2. b"], f"blank entries dropped, got {listed}"

    # 6. main() via argv writes to stdout
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = sc.main(["x", "y"])
    assert rc == 0 and "1. x" in buf.getvalue() and "| 1 | (1) × (2) |" in buf.getvalue()

    print("scaffold.py: all 6 tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
