#!/usr/bin/env python3
"""Build/refresh the local autoresearch tool index from the two upstream awesome-lists.

Token-efficient design: this is the ONLY place the full lists are read. The result is a
compact local index (``data/index.json``) that ``query.py`` searches; the catalog is NEVER
loaded wholesale into an agent's context. Run on demand or via the weekly systemd timer.

Stdlib only (no pip deps). Records each upstream commit SHA in ``data/state.json`` so updates
can be tracked cheaply by ``check_updates.py``.

Sources:
  - alvinreal/awesome-autoresearch  (parsed from README.md; CC0)
  - yibie/awesome-autoresearch      (parsed from categories/*.md, auto-discovered)
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
UA = {"User-Agent": "autoresearch-toolfinder/1.0 (+jajupmochi/agent-harness)"}

SOURCES = [
    {"key": "alvinreal", "owner": "alvinreal", "repo": "awesome-autoresearch",
     "branch": "main", "mode": "readme"},
    {"key": "yibie", "owner": "yibie", "repo": "awesome-autoresearch",
     "branch": "main", "mode": "categories"},
]

BADGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
HEADER = re.compile(r"^(#{2,4})\s+(.*?)\s*#*$")
EMOJI = re.compile(r"[\U0001f000-\U0001faff☀-➿️]")
SKIP_NAMES = {"source", "contributing", "license", "prs welcome", "awesome", "back to top"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 (trusted hosts)
        return r.read().decode("utf-8", "replace")


def raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"


def deemoji(s: str) -> str:
    return EMOJI.sub("", s).strip(" :#").strip()


def clean_desc(line: str) -> str:
    s = BADGE.sub("", line)
    s = LINK.sub("", s)
    s = s.strip().lstrip("-*|").strip()
    s = re.sub(r"^[—–-]\s*", "", s).strip()
    s = s.strip("|").strip()
    return re.sub(r"\s+", " ", s)[:280]


def parse(md: str, source: str, fixed_category: str | None = None) -> list[dict]:
    out: list[dict] = []
    section = fixed_category or "(general)"
    for line in md.splitlines():
        if fixed_category is None:
            h = HEADER.match(line)
            if h:
                section = deemoji(h.group(2)) or section
                continue
        for m in LINK.finditer(line):
            name, url = m.group(1).strip(), m.group(2).strip()
            name = re.sub(r"^[*_`\s]+|[*_`\s]+$", "", name)  # strip markdown bold/italic/code
            if "img.shields.io" in url or "awesome.re" in url or url.endswith("/badge.svg"):
                continue
            if not name or name.lower() in SKIP_NAMES:
                continue
            out.append({"name": name, "url": url, "category": section,
                        "source": source, "desc": clean_desc(line)})
    return out


def latest_sha(owner: str, repo: str, branch: str):
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}/commits?sha={branch}&per_page=1"
        data = json.loads(fetch(url, timeout=20))
        return data[0]["sha"][:12], data[0]["commit"]["committer"]["date"]
    except Exception as e:  # noqa: BLE001 (best-effort; rate limits expected)
        print(f"[warn] latest_sha {owner}/{repo}: {e}", file=sys.stderr)
        return None, None


def collect(src: dict) -> list[dict]:
    owner, repo, branch = src["owner"], src["repo"], src["branch"]
    entries: list[dict] = []
    if src["mode"] == "readme":
        entries = parse(fetch(raw_url(owner, repo, branch, "README.md")), src["key"])
    elif src["mode"] == "categories":
        readme = fetch(raw_url(owner, repo, branch, "README.md"))
        cats = sorted(set(re.findall(r"categories/([\w-]+\.md)", readme)))
        for c in cats:
            try:
                cmd = fetch(raw_url(owner, repo, branch, f"categories/{c}"))
            except urllib.error.HTTPError:
                continue
            catname = c[:-3].replace("-", " ").title()
            entries += parse(cmd, src["key"], fixed_category=catname)
    # de-duplicate within a source by normalized URL
    seen, dedup = set(), []
    for e in entries:
        k = e["url"].rstrip("/").lower()
        if k in seen:
            continue
        seen.add(k)
        dedup.append(e)
    return dedup


def main() -> int:
    os.makedirs(DATA, exist_ok=True)
    all_entries: list[dict] = []
    state = {"generated": now_iso(), "sources": {}}
    for src in SOURCES:
        try:
            entries = collect(src)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] {src['key']}: fetch/parse failed: {e}", file=sys.stderr)
            entries = []
        sha, date = latest_sha(src["owner"], src["repo"], src["branch"])
        state["sources"][src["key"]] = {
            "owner": src["owner"], "repo": src["repo"], "branch": src["branch"],
            "sha": sha, "upstream_commit_date": date, "synced_at": now_iso(),
            "n_entries": len(entries), "url": f"https://github.com/{src['owner']}/{src['repo']}",
        }
        all_entries += entries
        print(f"[ok] {src['key']}: {len(entries)} entries  sha={sha}")
    index = {"generated": state["generated"], "n": len(all_entries),
             "sources": [s["key"] for s in SOURCES], "entries": all_entries}
    with open(os.path.join(DATA, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    with open(os.path.join(DATA, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"[done] {len(all_entries)} total entries -> {os.path.join(DATA, 'index.json')}")
    return 0 if all_entries else 1


if __name__ == "__main__":
    sys.exit(main())
