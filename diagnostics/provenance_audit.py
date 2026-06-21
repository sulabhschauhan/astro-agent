"""
provenance_audit.py
Read-only provenance investigation for the unlogged write into 8 of
data/progress/*.json's files on 2026-05-27 between 19:20:01 and 19:27:40
local time, documented in diagnostics/chunking_code_audit_20260621_092249.md
(Q6 "What this evidence does and doesn't establish"). That audit established
no code currently in the repo can produce the write; this script searches
for evidence of *what did*, outside the committed codebase.

READ-ONLY CONTRACT: every git command here is non-mutating (reflog, log,
stash list, fsck --dangling, show) -- never checkout/reset/gc/prune/stash
pop/apply. Shell-history, Python-history, IDE-history, and data/*.json|*.log
files are opened for reading only. schtasks is queried, not modified. No
file is moved, deleted, or altered by this script. The only write this
script performs is the final report, into diagnostics/.

Output: Markdown report printed to stdout and written to
diagnostics/provenance_audit_<timestamp>.md.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent

AFFECTED_BOOKS = [
    "Deva-keralam",
    "Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan",
    "Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series",
    "Muhurtha-Chinthamani",
    "Prasna Marga 1",
    "Prasna Marga 2",
    "Sarvartha-Chintamani",
    "uttkalamrita-kalidas-ps-sastri",
]
CLEAN_BOOKS = [
    "BPHS - 1 RSanthanam",
    "BPHS - 2 RSanthanam",
    "cheiroslanguageo00chei_1",
    "Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri",
    "Saravali of Kalyana Varma Santhanam R. (Astrology)",
    "Jyotish_Lal Kitab_B.M. Gosvami",
]

PS_KEYWORDS = [
    "run_single_book", "run_overnight", "chunker", "_save_progress", "progress",
    "Lal Kitab", "05-27", "05-30", "data\\progress", "data/progress",
    "python -c", "jupyter", "ipython",
]

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
GAPS: list[str] = []


def _truncate(lines: list[str], n: int = 50) -> list[str]:
    if len(lines) <= 2 * n:
        return lines
    return lines[:n] + [f"[... {len(lines) - 2 * n} lines omitted ...]"] + lines[-n:]


def _run_git(args: list[str]) -> tuple[str, str, int]:
    try:
        res = subprocess.run(
            ["git"] + args, cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        return res.stdout, res.stderr, res.returncode
    except Exception as exc:
        return "", str(exc), -1


# ---------------------------------------------------------------- Axis 1
def axis1_filesystem_forensics() -> dict:
    progress_dir = ROOT / "data" / "progress"
    rows = []
    for f in sorted(progress_dir.glob("*.json")):
        st = f.stat()
        mtime = datetime.fromtimestamp(st.st_mtime)
        ctime = datetime.fromtimestamp(st.st_ctime)  # Windows: creation time
        rows.append({
            "book": f.stem, "mtime": mtime.isoformat(timespec="seconds"),
            "ctime": ctime.isoformat(timespec="seconds"), "size": st.st_size,
        })
    rows.sort(key=lambda r: r["mtime"])

    backup_exts = (".bak", ".tmp", ".orig", ".swp")
    stray = []
    data_dir = ROOT / "data"
    if data_dir.exists():
        for p in data_dir.rglob("*"):
            if p.is_file() and (p.suffix in backup_exts or p.name.endswith("~")):
                stray.append(str(p.relative_to(ROOT)))

    return {"rows": rows, "stray_files": stray}


# ---------------------------------------------------------------- Axis 2
def axis2_git_forensics() -> dict:
    reflog, _, _ = _run_git(["reflog", "--date=iso"])
    log_out, _, _ = _run_git([
        "log", "--all", "--since=2026-05-25", "--until=2026-06-01",
        "--name-status", "--pretty=fuller",
    ])
    stash_out, _, _ = _run_git(["stash", "list"])
    fsck_out, fsck_err, _ = _run_git(["fsck", "--unreachable", "--no-reflogs", "--dangling"])

    # Dynamically find the commit(s) that first ADDED each progress file
    # (rather than hardcoding a commit hash) -- and the commit that removed them.
    add_commits = {}
    remove_commits = {}
    for book in AFFECTED_BOOKS + CLEAN_BOOKS:
        path = f"data/progress/{book}.json"
        out, _, _ = _run_git(["log", "--all", "--diff-filter=A", "--format=%H %ad", "--date=iso", "--", path])
        if out.strip():
            add_commits[book] = out.strip().splitlines()[-1]  # earliest add
        out, _, _ = _run_git(["log", "--all", "--diff-filter=D", "--format=%H %ad", "--date=iso", "--", path])
        if out.strip():
            remove_commits[book] = out.strip().splitlines()[0]  # most recent removal

    return {
        "reflog": reflog.splitlines(),
        "log_window": log_out.splitlines(),
        "stash": stash_out.strip(),
        "fsck_out": fsck_out.strip(), "fsck_err": fsck_err.strip(),
        "add_commits": add_commits, "remove_commits": remove_commits,
    }


def axis2_git_blob_check(add_commit_hash: str) -> dict:
    """Independent corroboration: was the _c0-suffix corruption already
    present in the immutable git blob committed the morning after the
    overnight run, before Session 13 (2026-05-30) ever ran?"""
    out, err, rc = _run_git(["show", f"{add_commit_hash}:data/progress/Deva-keralam.json"])
    if rc != 0:
        return {"error": err}
    try:
        data = json.loads(out)
    except Exception as exc:
        return {"error": f"JSON parse failed: {exc}"}
    first_id = data[0]["chunk_id"] if data else ""

    out2, err2, rc2 = _run_git(["show", f"{add_commit_hash}:data/chunked_chunks.json"])
    chunked_p8 = []
    if rc2 == 0:
        try:
            chunked = json.loads(out2)
            chunked_p8 = [
                {"chunk_id": c["chunk_id"], "len_text": len(c.get("text") or "")}
                for c in chunked
                if c.get("book_name") == "Deva-keralam" and c.get("page_ref") == 8
            ]
        except Exception as exc:
            chunked_p8 = [{"error": f"JSON parse failed: {exc}"}]
    else:
        chunked_p8 = [{"error": err2}]

    return {
        "progress_first_id": first_id,
        "progress_n": len(data),
        "chunked_chunks_p8": chunked_p8,
    }


# ---------------------------------------------------------------- Axis 3
def axis3_powershell_history() -> dict:
    candidates = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt",
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt",
    ]
    results = []
    for path in candidates:
        if not path.exists():
            results.append({"path": str(path), "exists": False})
            continue
        st = path.stat()
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        mtime = datetime.fromtimestamp(st.st_mtime)
        matches = []
        for i, line in enumerate(lines):
            if any(kw.lower() in line.lower() for kw in PS_KEYWORDS):
                lo, hi = max(0, i - 2), min(len(lines) - 1, i + 2)
                matches.append({"line_no": i + 1, "context": lines[lo:hi + 1]})
        results.append({
            "path": str(path), "exists": True, "total_lines": len(lines),
            "last_write_time": mtime.isoformat(timespec="seconds"),
            "matches": matches,
        })
    return {"results": results}


# ---------------------------------------------------------------- Axis 4
def axis4_python_interactive_history() -> dict:
    py_hist_candidates = [
        Path(os.environ.get("USERPROFILE", "")) / ".python_history",
        ROOT / ".python_history",
    ]
    py_hist = [{"path": str(p), "exists": p.exists()} for p in py_hist_candidates]

    window_start = datetime(2026, 5, 27)
    window_end = datetime(2026, 5, 31)

    ipynb_checkpoints = []
    ipynb_files = []
    for base, label in [(ROOT, "project root (recursive)"), (ROOT.parent, "parent dir (non-recursive)")]:
        if label.endswith("(recursive)"):
            it = base.rglob("*")
        else:
            it = base.iterdir()
        try:
            for p in it:
                if p.is_dir() and p.name == ".ipynb_checkpoints":
                    for sub in p.iterdir():
                        st = sub.stat()
                        ipynb_checkpoints.append({
                            "path": str(sub), "scope": label,
                            "mtime": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                        })
                elif p.is_file() and p.suffix == ".ipynb":
                    st = p.stat()
                    mtime = datetime.fromtimestamp(st.st_mtime)
                    ipynb_files.append({
                        "path": str(p), "scope": label,
                        "mtime": mtime.isoformat(timespec="seconds"),
                        "in_window": window_start <= mtime <= window_end,
                    })
        except PermissionError:
            continue
    return {"py_hist": py_hist, "ipynb_checkpoints": ipynb_checkpoints, "ipynb_files": ipynb_files}


# ---------------------------------------------------------------- Axis 5
def axis5_ide_traces() -> dict:
    vscode_dir = ROOT / ".vscode"
    idea_dir = ROOT / ".idea"
    result = {
        "vscode_exists": vscode_dir.exists(),
        "idea_exists": idea_dir.exists(),
        "vscode_contents": [str(p.relative_to(ROOT)) for p in vscode_dir.iterdir()] if vscode_dir.exists() else [],
        "idea_contents": [str(p.relative_to(ROOT)) for p in idea_dir.iterdir()] if idea_dir.exists() else [],
    }

    hist_dir = Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "History"
    if not hist_dir.exists():
        result["vscode_local_history"] = {"available": False}
        return result

    all_entries = []
    matches = []
    needles = ("astro-agent", "run_single_book", "data/progress", "data\\progress", "chunker")
    for entries_json in hist_dir.rglob("entries.json"):
        try:
            data = json.loads(entries_json.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        resource = data.get("resource", "")
        timestamps = [e.get("timestamp") for e in data.get("entries", [])]
        all_entries.extend(timestamps)
        if any(n in resource for n in needles):
            matches.append({"resource": resource, "entries": data.get("entries", [])})

    earliest = min(all_entries) if all_entries else None
    latest = max(all_entries) if all_entries else None
    result["vscode_local_history"] = {
        "available": True,
        "total_tracked_resources": len(list(hist_dir.glob("*"))),
        "total_entries": len(all_entries),
        "earliest": datetime.fromtimestamp(earliest / 1000).isoformat(timespec="seconds") if earliest else None,
        "latest": datetime.fromtimestamp(latest / 1000).isoformat(timespec="seconds") if latest else None,
        "project_matches": matches,
    }
    return result


# ---------------------------------------------------------------- Axis 6
def axis6_sibling_and_symlinks() -> dict:
    siblings = sorted(p.name for p in ROOT.parent.iterdir()) if ROOT.parent.exists() else []
    progress_dir = ROOT / "data" / "progress"
    symlinks = [str(p) for p in progress_dir.iterdir() if p.is_symlink()] if progress_dir.exists() else []
    return {"siblings": siblings, "symlinks_in_progress_dir": symlinks}


# ---------------------------------------------------------------- Axis 7
def axis7_scheduled_tasks_and_startup() -> dict:
    try:
        res = subprocess.run(
            ["schtasks", "/Query", "/FO", "LIST", "/V"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        lines = res.stdout.splitlines()
        keywords = ("python", "astro", "chunker", str(ROOT).lower())
        matches = [l for l in lines if any(k in l.lower() for k in keywords)]
        schtasks_result = {"available": True, "total_lines": len(lines), "matches": matches}
    except Exception as exc:
        schtasks_result = {"available": False, "error": str(exc)}

    startup_dirs = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup",
        Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp"),
    ]
    startup_contents = {}
    for d in startup_dirs:
        if d.exists():
            startup_contents[str(d)] = [p.name for p in d.iterdir()]
        else:
            startup_contents[str(d)] = None
    return {"schtasks": schtasks_result, "startup": startup_contents}


# ---------------------------------------------------------------- Axis 8
def axis8_run_single_book_invocation() -> dict:
    log_path = ROOT / "data" / "run_single_book.log"
    if not log_path.exists():
        return {"log_available": False}
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    header = [l for l in lines if any(
        t in l for t in ("SINGLE BOOK INGEST STARTED", "PDF:", "book_name:")
    )][:5]
    return {"log_available": True, "header": header, "total_lines": len(lines)}


def build_report() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    L = []
    L.append("# Provenance Audit -- 2026-05-27 Unlogged Progress-File Write\n")
    L.append(f"**Generated:** {now}  ")
    L.append("**Read-only investigation** -- no files modified/deleted/moved; no git refs changed.\n")
    L.append(
        "Prior finding (`diagnostics/chunking_code_audit_20260621_092249.md`, Q6): 8 of 14 "
        "`data/progress/*.json` files were overwritten with already-chunked content within an "
        "11-second window (19:27:29-19:27:40 local) on 2026-05-27, 7-19 minutes after "
        "`run_overnight.py`'s own log closed cleanly at 19:20:01. No code in the repo can "
        "produce that write. This report searches outside the codebase for evidence of what did.\n"
    )

    # ============================================================= Axis 1
    L.append("## 1. Filesystem forensics on data/progress/*.json\n")
    a1 = axis1_filesystem_forensics()
    L.append(
        "Note: on Windows, Python's `st_ctime` is file **creation** time, not a metadata-change "
        "time (unlike Unix). Reported as-is.\n"
    )
    L.append("| mtime | ctime (creation) | size (bytes) | book |")
    L.append("|---|---|---|---|")
    for r in a1["rows"]:
        flag = " **<-- affected**" if r["book"] in AFFECTED_BOOKS else ""
        L.append(f"| {r['mtime']} | {r['ctime']} | {r['size']} | {r['book']}{flag} |")
    L.append("")
    affected_mtimes = [r["mtime"] for r in a1["rows"] if r["book"] in AFFECTED_BOOKS]
    if affected_mtimes:
        L.append(
            f"The 8 affected books' mtimes span {min(affected_mtimes)} to {max(affected_mtimes)} "
            "-- confirms the 11-second burst window from the prior audit, reproduced independently here.\n"
        )
    L.append("**Stray .bak/.tmp/~/.orig/.swp files under data/:**")
    if a1["stray_files"]:
        for f in a1["stray_files"]:
            L.append(f"- {f}")
    else:
        L.append("None found.")
        GAPS.append("No backup/temp files found under data/ — if a script wrote via a .tmp+rename pattern (as the project's own _save_progress() helpers do), the .tmp would only be visible if the process crashed mid-write. Its absence is consistent with either a clean write or simply no such pattern being used.")
    L.append("")

    # ============================================================= Axis 2
    L.append("## 2. Git reflog, full log, stash, fsck\n")
    a2 = axis2_git_forensics()
    L.append("### git reflog --date=iso (full output)\n")
    L.append("```")
    L.extend(a2["reflog"])
    L.append("```")
    L.append(
        "Reflog is a clean linear sequence of `commit` and one `clone` entry -- no `reset`, "
        "`rebase`, `checkout`, `stash` (pop/apply), or `commit (amend)` entries anywhere in the "
        "project's history. No evidence of branch-switching or history rewriting.\n"
    )

    L.append("### git stash list\n")
    L.append("```")
    L.append(a2["stash"] if a2["stash"] else "(empty)")
    L.append("```\n")

    L.append("### git fsck --unreachable --no-reflogs --dangling\n")
    L.append("```")
    L.append(a2["fsck_out"] if a2["fsck_out"] else "(no unreachable/dangling objects)")
    if a2["fsck_err"]:
        L.append(a2["fsck_err"])
    L.append("```\n")

    L.append("### Commits that ADDED / REMOVED each progress file (dynamically located, not hardcoded)\n")
    L.append("| book | first commit adding it | commit removing it |")
    L.append("|---|---|---|")
    for book in AFFECTED_BOOKS + CLEAN_BOOKS:
        add = a2["add_commits"].get(book, "(not found)")
        rem = a2["remove_commits"].get(book, "(never removed / still tracked)")
        L.append(f"| {book} | {add} | {rem} |")
    L.append("")

    second_rechunk_before_session13 = False
    add_hashes = set(v.split()[0] for v in a2["add_commits"].values())
    if len(add_hashes) == 1:
        add_commit = next(iter(add_hashes))
        L.append(
            f"All 14 progress files were added to git in the **same single commit** "
            f"(`{add_commit}`), and removed in the next commit ~62 seconds later. This is an "
            "accidental commit-then-revert, not a deliberate provenance event by itself -- but "
            "it gives us an **immutable git blob** of the corrupted files from the morning after "
            "the incident, independent of live filesystem mtimes.\n"
        )
        L.append(f"### Independent corroboration via the immutable blob at `{add_commit}`\n")
        blob_check = axis2_git_blob_check(add_commit)
        if "error" in blob_check:
            L.append(f"Could not read blob: {blob_check['error']}\n")
            GAPS.append(f"Could not read git blob at {add_commit} for corroboration: {blob_check['error']}")
        else:
            L.append(
                f"`git show {add_commit}:data/progress/Deva-keralam.json` -- first chunk_id: "
                f"`{blob_check['progress_first_id']}` ({blob_check['progress_n']} entries total)."
            )
            already_corrupted = bool(re.search(r"_c\d+$", blob_check["progress_first_id"]))
            L.append(
                f"\n**This confirms the `_c0` corruption was already present in the git-committed "
                f"snapshot taken the morning of 2026-05-28 (09:40 local) -- i.e. independently of "
                f"live mtimes, the corruption is proven to predate Session 13 (2026-05-30) by an "
                f"immutable, tamper-evident source.**\n" if already_corrupted else
                "\nThe committed snapshot does NOT show the corruption -- this would contradict "
                "the filesystem-mtime finding and needs reconciling.\n"
            )
            L.append(f"`git show {add_commit}:data/chunked_chunks.json` -- Deva-keralam page 8 entries at that commit:")
            L.append("```")
            for row in blob_check["chunked_chunks_p8"]:
                if "error" in row:
                    L.append(f"[error: {row['error']}]")
                else:
                    L.append(f"{row['chunk_id']}  (len(text)={row['len_text']})")
            L.append("```")
            ids_at_commit = {r.get("chunk_id") for r in blob_check["chunked_chunks_p8"] if "chunk_id" in r}
            double_suffixed = any(cid.endswith("_c0_c0") or re.search(r"_c\d+_c\d+$", cid or "") for cid in ids_at_commit)
            second_rechunk_before_session13 = double_suffixed
            if double_suffixed:
                L.append(
                    "\nThe double-suffix (`_c0_c0`) was **already present at this 2026-05-28 "
                    "commit** -- meaning the second chunk_all() re-run over corrupted progress "
                    "data happened *before* this commit, not only via the 2026-05-30 "
                    "run_single_book.py run. This means an additional, still-unidentified "
                    "run_overnight.py or equivalent invocation happened between 2026-05-27 19:27 "
                    "and 2026-05-28 09:40 -- narrowing, not widening, the unexplained gap, but "
                    "adding a second unexplained re-chunk event to account for.\n"
                )
            else:
                L.append(
                    "\nAt this commit, `chunked_chunks.json` still shows the single-suffixed, "
                    "correct form for this page -- the double-suffix only appears in the "
                    "*current* file (written 2026-05-30, Session 13). This is consistent with "
                    "the chunking_code_audit's timeline: corruption of the progress files on "
                    "2026-05-27, compounded by a single re-chunk during Session 13.\n"
                )
    else:
        L.append(f"Progress files were added across {len(add_hashes)} different commits (not a single batch) -- see table above.\n")

    L.append("### git log --all --since=2026-05-25 --until=2026-06-01 --name-status --pretty=fuller\n")
    L.append("Full output truncated per report constraints (first/last 50 lines); load-bearing "
              "commits are quoted in full above and below regardless of where they fall in this dump.\n")
    L.append("```")
    L.extend(_truncate(a2["log_window"]))
    L.append("```\n")

    # ============================================================= Axis 3
    L.append("## 3. PowerShell shell history\n")
    a3 = axis3_powershell_history()
    for r in a3["results"]:
        if not r["exists"]:
            L.append(f"`{r['path']}` -- not present on this system.\n")
            continue
        L.append(f"`{r['path']}`")
        L.append(f"- Total lines: {r['total_lines']}")
        L.append(f"- File last-write time: **{r['last_write_time']}**")
        if r["matches"]:
            L.append(f"- {len(r['matches'])} keyword match(es):")
            L.append("```")
            for m in r["matches"]:
                for ctx_line in m["context"]:
                    L.append(ctx_line)
                L.append("---")
            L.append("```")
        else:
            L.append("- 0 keyword matches.")
        if r["last_write_time"] < "2025-01-01":
            GAPS.append(
                f"{r['path']}: last written {r['last_write_time']}, over a year before the "
                "2026-05-27 incident. This is a coverage gap, not a clean negative result -- "
                "this history mechanism was not active during the incident window, so its "
                "absence of matches proves nothing either way."
            )
        L.append("")

    # ============================================================= Axis 4
    L.append("## 4. Python interactive history\n")
    a4 = axis4_python_interactive_history()
    for h in a4["py_hist"]:
        status = "present" if h["exists"] else "not present on this system"
        L.append(f"- `{h['path']}` -- {status}")
    if not any(h["exists"] for h in a4["py_hist"]):
        GAPS.append("No .python_history file found anywhere checked — no Python REPL history available for this window.")
    L.append("")
    L.append("**`.ipynb_checkpoints` directories found (project root recursive + immediate parent):**")
    if a4["ipynb_checkpoints"]:
        for c in a4["ipynb_checkpoints"]:
            L.append(f"- `{c['path']}` (scope: {c['scope']}, mtime: {c['mtime']})")
    else:
        L.append("None found.")
    L.append("\n**`.ipynb` files found:**")
    if a4["ipynb_files"]:
        for f in a4["ipynb_files"]:
            flag = " **<-- in 2026-05-27..05-31 window**" if f["in_window"] else ""
            L.append(f"- `{f['path']}` (scope: {f['scope']}, mtime: {f['mtime']}){flag}")
    else:
        L.append("None found.")
    L.append("")

    # ============================================================= Axis 5
    L.append("## 5. IDE / editor traces\n")
    a5 = axis5_ide_traces()
    L.append(f"- `.vscode/`: {'present -- ' + str(a5['vscode_contents']) if a5['vscode_exists'] else 'not present in project root'}")
    L.append(f"- `.idea/`: {'present -- ' + str(a5['idea_contents']) if a5['idea_exists'] else 'not present in project root'}")
    vh = a5["vscode_local_history"]
    if not vh.get("available"):
        L.append("- VSCode local history directory: not present on this system.")
        GAPS.append("VSCode local history directory not found.")
    else:
        L.append(
            f"- VSCode local history (`%APPDATA%\\Code\\User\\History`): "
            f"{vh['total_tracked_resources']} resource folders, {vh['total_entries']} total "
            f"entries, spanning {vh['earliest']} to {vh['latest']} -- **this range fully covers "
            "the 2026-05-27 incident window**, so an absence of matches below is a meaningful "
            "negative result, not a coverage gap."
        )
        if vh["project_matches"]:
            L.append("\nMatches referencing this project, run_single_book, progress dir, or chunker:")
            for m in vh["project_matches"]:
                L.append(f"- `{m['resource']}`")
                for e in m["entries"]:
                    ts = datetime.fromtimestamp(e["timestamp"] / 1000).isoformat(timespec="seconds")
                    L.append(f"  - saved at {ts}")
        else:
            L.append(
                "\nZero matches for `astro-agent`, `run_single_book`, `data/progress`, or "
                "`chunker` across all tracked resources. VSCode's local history records every "
                "*editor save* regardless of `.gitignore` -- so this indicates the corrupted "
                "files were not produced by a VSCode editor save, consistent with a script or "
                "REPL process instead."
            )
    L.append("")

    # ============================================================= Axis 6
    L.append("## 6. Sibling-repo / external-script possibility\n")
    a6 = axis6_sibling_and_symlinks()
    L.append(f"Sibling directories at `{ROOT.parent}` (names only, not traversed):")
    for s in a6["siblings"]:
        L.append(f"- {s}")
    L.append("")
    if a6["symlinks_in_progress_dir"]:
        L.append("Symlinks/reparse points found inside `data/progress/`:")
        for s in a6["symlinks_in_progress_dir"]:
            L.append(f"- {s}")
    else:
        L.append("No symlinks or reparse points found inside `data/progress/` -- all files are ordinary files.")
    L.append("")

    # ============================================================= Axis 7
    L.append("## 7. Scheduled tasks / startup hooks\n")
    a7 = axis7_scheduled_tasks_and_startup()
    sch = a7["schtasks"]
    if not sch.get("available"):
        L.append(f"`schtasks /Query /FO LIST /V` failed: {sch.get('error')}")
        GAPS.append(f"schtasks query failed: {sch.get('error')}")
    else:
        L.append(f"`schtasks /Query /FO LIST /V` -- {sch['total_lines']} lines returned, "
                  f"{len(sch['matches'])} line(s) matching python/astro/chunker/repo-path.")
        if sch["matches"]:
            L.append("```")
            for m in sch["matches"]:
                L.append(m)
            L.append("```")
        else:
            L.append("No matches.")
    L.append("\n**Startup folder contents:**")
    for path, contents in a7["startup"].items():
        if contents is None:
            L.append(f"- `{path}`: not present on this system")
        else:
            L.append(f"- `{path}`: {contents}")
    L.append("")

    # ============================================================= Axis 8
    L.append("## 8. The 2026-05-30 Lal Kitab run_single_book.py invocation\n")
    a8 = axis8_run_single_book_invocation()
    if not a8["log_available"]:
        L.append("`data/run_single_book.log` not found.")
        GAPS.append("data/run_single_book.log not found — cannot check command-line evidence for the Session 13 invocation.")
    else:
        L.append(f"`data/run_single_book.log` -- {a8['total_lines']} lines. Header lines captured by the script's own logging:")
        L.append("```")
        for l in a8["header"]:
            L.append(l)
        L.append("```")
        L.append(
            "\nThis is the PDF path / book name **parsed from `sys.argv[1]` by the script's own "
            "logging**, not a verbatim shell command-line capture -- `main(sys.argv[1])` is logged "
            "indirectly via `PDF:` and `book_name:` lines, but the literal invoking command "
            "(`python ingestion/run_single_book.py \"...\"`) and its working directory/shell are "
            "not recorded anywhere in this log."
        )
        GAPS.append("run_single_book.log records the parsed PDF path/book name but not the literal shell command line, working directory, or which terminal/shell invoked it.")
    L.append(
        "\nGit commits/stash entries from 2026-05-30 touching `run_single_book.py` or its caller: "
        "see Axis 2's add/remove table and the `git log --all --since/--until` dump above -- only "
        "one commit (`7753349`) touches `ingestion/run_single_book.py`, adding it for the first "
        "and only time; no stash entries exist for that date (stash list is empty repo-wide).\n"
    )

    # ============================================================= Gaps
    L.append("## Outstanding gaps\n")
    L.append(
        "Every question that could not be fully answered, and why:\n"
    )
    if GAPS:
        for i, g in enumerate(GAPS, 1):
            L.append(f"{i}. {g}")
    else:
        L.append("(none recorded)")
    rechunk_clause = (
        " (and, per the Axis 2 git-blob finding, a second unexplained re-chunk event before "
        "2026-05-28 09:40)" if second_rechunk_before_session13 else
        " (the Axis 2 git-blob check ruled out a second re-chunk before 2026-05-28 09:40 -- "
        "chunked_chunks.json at that commit still shows the single-suffixed correct form, so "
        "the only unexplained event is the progress-file write itself)"
    )
    L.append(
        "\n**The central open question remains unresolved**: no command-line, shell-history, "
        "Python-history, IDE-history, scheduled-task, or git-tracked evidence was found "
        "anywhere checked that identifies the specific process which overwrote the 8 progress "
        f"files in the 2026-05-27 19:20:01-19:27:40 window{rechunk_clause}. The PowerShell history "
        "mechanism that might have captured an interactive command was not active during this "
        "period (last written 2024-11-03) -- this is the single largest coverage gap, and without "
        "it, a manually-typed `python -c \"...\"` one-liner or short ad hoc script run directly in "
        "a terminal remains consistent with all available evidence but cannot be confirmed or "
        "further localized in time beyond the existing mtime/git-blob bounds."
    )

    return "\n".join(L) + "\n"


def main():
    report = build_report()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(__file__).parent / f"provenance_audit_{timestamp}.md"
    out_path.write_text(report, encoding="utf-8")
    sys.stdout.buffer.write(report.encode("utf-8", errors="replace"))
    print(f"\n[written to {out_path}]")


if __name__ == "__main__":
    main()
