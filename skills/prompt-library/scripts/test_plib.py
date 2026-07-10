#!/usr/bin/env python3
"""Tests for plib.py (prompt-library, privacy-gated). Run: python3 test_plib.py"""
import importlib.util
import io
import os
import tempfile
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("plib", os.path.join(HERE, "plib.py"))
plib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(plib)


def _run(argv, stdin=""):
    import sys
    old = sys.stdin
    sys.stdin = io.StringIO(stdin)
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = plib.main(argv)
    finally:
        sys.stdin = old
    return rc, out.getvalue(), err.getvalue()


def run():
    # privacy_scan unit checks (extra=[] so no local private-terms file leaks into the test)
    assert plib.privacy_scan("clean reusable prompt about dashboards", extra=[]) == []
    assert any(l == "absolute home path" for l, _ in plib.privacy_scan("see /home/bob/x", extra=[]))
    assert any(l == "email address" for l, _ in plib.privacy_scan("mail me a@b.com", extra=[]))
    # user-specific terms come from the caller / local file, not shipped literals:
    assert any(l == "private term" for l, _ in plib.privacy_scan("reuse the ZZCODENAME brief", extra=["ZZCODENAME"]))

    with tempfile.TemporaryDirectory() as root:
        base = ["--root", root]

        # 1. add a CLEAN prompt -> stored + indexed
        rc, out, err = _run(["add", *base, "--title", "Redesign a dashboard", "--scenarios", "ui,redesign",
                             "--source", "claude-code", "--tags", "design"],
                            stdin="You are redesigning a data dashboard. Produce N rounds, each a full mock.\n")
        assert rc == 0, f"clean add should succeed: {err}"
        p = out.strip()
        assert os.path.basename(p) == "redesign-a-dashboard.md"
        assert "You are redesigning a data dashboard" in open(p, encoding="utf-8").read()
        idx = open(os.path.join(root, "INDEX.md"), encoding="utf-8").read()
        assert "Redesign a dashboard" in idx and "ui,redesign" in idx

        # 2. add a prompt with an absolute path -> REFUSED, not stored
        rc, out, err = _run(["add", *base, "--title", "Bad one"],
                            stdin="run the script at /home/someone/secret/run.sh\n")
        assert rc == 1 and "REFUSED" in err and "absolute home path" in err
        assert not os.path.exists(os.path.join(root, "prompts", "bad-one.md")), "refused prompt not written"

        # 3. refuse on email; and on a user-specific private term loaded from a LOCAL file (env-pointed)
        rc, _, err = _run(["add", *base, "--title", "E"], stdin="ping me at foo@bar.com\n")
        assert rc == 1 and "email" in err
        import tempfile as _tf
        tf = os.path.join(root, "terms.txt")
        open(tf, "w").write("# my private terms\nZZCODENAME\n")
        os.environ["PLIB_PRIVATE_TERMS"] = tf
        try:
            rc, _, err = _run(["add", *base, "--title", "C"], stdin="reuse the ZZCODENAME prompt\n")
            assert rc == 1 and "private term" in err, f"local private term must block: {err}"

            # 4. private content in the TITLE is also caught (term in title, clean body)
            rc, _, err = _run(["add", *base, "--title", "ZZCODENAME playbook"], stdin="totally clean body\n")
            assert rc == 1 and "private term" in err
        finally:
            del os.environ["PLIB_PRIVATE_TERMS"]

        # 5. scan command: exit 1 on private, 0 on clean
        rc, _, _ = _run(["scan"], stdin="/media/disk/x\n")
        assert rc == 1
        rc, _, _ = _run(["scan"], stdin="a perfectly clean line\n")
        assert rc == 0

        # 6. find ranks by keyword
        _run(["add", *base, "--title", "Write release notes", "--scenarios", "docs"],
             stdin="Draft concise release notes from the git log.\n")
        rc, out, _ = _run(["find", *base, "--query", "dashboard"])
        lines = [ln for ln in out.strip().splitlines() if ln]
        assert lines and lines[0].endswith("redesign-a-dashboard.md"), f"find top, got {out!r}"

    print("plib.py: all 6 tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
