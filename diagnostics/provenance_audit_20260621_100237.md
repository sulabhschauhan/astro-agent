# Provenance Audit -- 2026-05-27 Unlogged Progress-File Write

**Generated:** 2026-06-21 10:02:27 UTC  
**Read-only investigation** -- no files modified/deleted/moved; no git refs changed.

Prior finding (`diagnostics/chunking_code_audit_20260621_092249.md`, Q6): 8 of 14 `data/progress/*.json` files were overwritten with already-chunked content within an 11-second window (19:27:29-19:27:40 local) on 2026-05-27, 7-19 minutes after `run_overnight.py`'s own log closed cleanly at 19:20:01. No code in the repo can produce that write. This report searches outside the codebase for evidence of what did.

## 1. Filesystem forensics on data/progress/*.json

Note: on Windows, Python's `st_ctime` is file **creation** time, not a metadata-change time (unlike Unix). Reported as-is.

| mtime | ctime (creation) | size (bytes) | book |
|---|---|---|---|
| 2026-05-27T09:48:20 | 2026-05-27T09:48:20 | 838660 | BPHS - 1 RSanthanam |
| 2026-05-27T10:21:57 | 2026-05-27T10:21:57 | 972718 | BPHS - 2 RSanthanam |
| 2026-05-27T11:27:53 | 2026-05-27T11:27:53 | 416339 | cheiroslanguageo00chei_1 |
| 2026-05-27T11:52:23 | 2026-05-27T11:52:23 | 625546 | Saravali of Kalyana Varma Santhanam R. (Astrology) |
| 2026-05-27T12:43:11 | 2026-05-27T12:43:11 | 722450 | Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri |
| 2026-05-27T19:27:29 | 2026-05-27T13:20:27 | 625252 | Deva-keralam **<-- affected** |
| 2026-05-27T19:27:29 | 2026-05-27T15:56:27 | 190931 | Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan **<-- affected** |
| 2026-05-27T19:27:30 | 2026-05-27T18:18:02 | 306855 | Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series **<-- affected** |
| 2026-05-27T19:27:33 | 2026-05-27T09:18:15 | 580376 | Muhurtha-Chinthamani **<-- affected** |
| 2026-05-27T19:27:35 | 2026-05-27T08:18:35 | 461375 | Prasna Marga 1 **<-- affected** |
| 2026-05-27T19:27:37 | 2026-05-27T08:46:40 | 390299 | Prasna Marga 2 **<-- affected** |
| 2026-05-27T19:27:38 | 2026-05-27T19:18:57 | 338898 | Sarvartha-Chintamani **<-- affected** |
| 2026-05-27T19:27:40 | 2026-05-27T09:00:02 | 332195 | uttkalamrita-kalidas-ps-sastri **<-- affected** |
| 2026-05-30T10:45:37 | 2026-05-30T10:45:37 | 726164 | Jyotish_Lal Kitab_B.M. Gosvami |

The 8 affected books' mtimes span 2026-05-27T19:27:29 to 2026-05-27T19:27:40 -- confirms the 11-second burst window from the prior audit, reproduced independently here.

**Stray .bak/.tmp/~/.orig/.swp files under data/:**
None found.

## 2. Git reflog, full log, stash, fsck

### git reflog --date=iso (full output)

```
7a5f4da HEAD@{2026-06-21 08:36:46 +0400}: commit: Session 22 close: P2.2.2 Sade Sati done, interpretive spike FAIL, roadmap paused
99b0562 HEAD@{2026-06-21 08:22:57 +0400}: commit: Interpretive-text feasibility spike: Saturn 11th-from-Lagna, Sheridan
e96ebd7 HEAD@{2026-06-21 08:22:42 +0400}: commit: P2.2.2 Sade Sati: compute_sade_sati() implementation + reference-chart tests
f0586d6 HEAD@{2026-06-21 07:02:51 +0400}: commit: P2.2.1 Gochara: transits/ package scaffold + compute_gochara() implementation
91c25b3 HEAD@{2026-06-21 06:59:11 +0400}: commit: Session 21 close: P2.2.1 Gochara green, SESSION_LOG + CLAUDE.md refresh
74f484e HEAD@{2026-06-20 17:39:44 +0400}: commit: Session 20 continued close: P2 reorder + Navamsa fixtures, SESSION_LOG + CLAUDE.md refresh
e94ec07 HEAD@{2026-06-20 17:39:38 +0400}: commit: P2.1 Navamsa (D9): activate all 4 reference-chart fixtures (David, Sulabh, Surbhi, Sheridan)
8f0fddb HEAD@{2026-06-20 16:46:41 +0400}: commit: Session 20 close: P2.1 Navamsa (D9) done, SESSION_LOG + CLAUDE.md refresh
16036ec HEAD@{2026-06-20 16:05:26 +0400}: commit: P2.1 closeout: Ketu retrograde line gets analogous comment to Rahu
2a70f1a HEAD@{2026-06-20 10:01:24 +0400}: commit: P2.1 Navamsa (D9): compute_navamsa module + tests, 21 new + 4 skipped
1f86950 HEAD@{2026-06-20 08:56:32 +0400}: commit: Session 19 close: P1.3 Aspects done, SESSION_LOG + CLAUDE.md refresh
23efe58 HEAD@{2026-06-20 08:48:53 +0400}: commit: P1.3 Aspects: complete (table + behavior + 73 tests, 5/7/9 lock for nodes)
aee45ed HEAD@{2026-06-19 19:13:52 +0400}: commit: Session 19 P1.3: graha drishti public function surface (aspects.py)
de910eb HEAD@{2026-06-19 14:18:40 +0400}: commit: Session 19 P1.3: structural tests for ASPECTED_HOUSES_BY_PLANET (54 new tests)
de9debe HEAD@{2026-06-19 10:16:53 +0400}: commit: Session 19 P1.3: graha drishti aspect-position data table
8704379 HEAD@{2026-06-19 09:36:56 +0400}: commit: Session 19 P1.3: behavioral tests for friendship.py (250 new tests)
d9a89ef HEAD@{2026-06-19 08:49:20 +0400}: commit: Session 19 P1.3: public planet scope + explicit Rahu/Ketu guard on pancha_dha_maitri
d66da33 HEAD@{2026-06-19 08:45:17 +0400}: commit: Session 19 P1.3: rename compound-relationship labels to PVR Sanskrit terms
6bc5f89 HEAD@{2026-06-19 08:25:10 +0400}: commit: Session 19 P1.3: friendship logic - natural, tatkalika, pancha-dha maitri
f85a694 HEAD@{2026-06-18 16:07:29 +0400}: commit: Session 19 P1.3: structural tests for natural friendship tables
b483957 HEAD@{2026-06-18 15:52:08 +0400}: commit: Session 19 P1.3: natural friendship + compound relationship tables (PVR Table 7/8)
3a4deb3 HEAD@{2026-06-18 15:14:56 +0400}: commit: Session 19 P1.3: behavioral tests for get_dignity_status()
c13bb65 HEAD@{2026-06-18 15:03:35 +0400}: commit: Session 19 P1.3: dignity classification logic + structural tests
7670b06 HEAD@{2026-06-18 14:20:11 +0400}: commit: Session 19 P1.3 prep: dignity tables (PVR Table 6)
75382ef HEAD@{2026-06-17 18:32:27 +0400}: commit: Session 19 P1.2b + P1.2c + ayanamsa: full Panchanga element set
52edce2 HEAD@{2026-06-16 22:25:06 +0400}: commit: Session 19 P1.1a + P1.2a: house_counting migration + Panchanga sunrise/sunset
162da70 HEAD@{2026-06-16 16:01:33 +0400}: commit: Phase 0: calculations/ package skeleton (45 empty placeholders)- Empty modules across core/, vargas/, strength/, dashas/, yogas/, transits/, ashtakavarga/, jaimini/, annual/, helpers/- All __init__.py empty except top-level package docstring- chart_calculator.py untouched- 41/41 tests passing
efb36a9 HEAD@{2026-06-16 13:27:16 +0400}: commit: Session 18: Mudda Dasha + Lagna house-counting resolution
709aa55 HEAD@{2026-06-15 17:44:28 +0400}: commit: feat(session-17): location-aware timezone resolution, Muntha calculation
c4f36ce HEAD@{2026-06-15 11:32:58 +0400}: commit: feat(session-17): Varshaphal solar-return epoch, chart, and boundary-sensitivity helper
404f33c HEAD@{2026-06-15 11:31:59 +0400}: commit: docs(session-17): add AstroSage reference charts + ayanamsa investigation writeup
b6de45b HEAD@{2026-06-15 09:53:09 +0400}: commit: chore(session-16): remove stale hand-laterality diagnostic scripts
bd12347 HEAD@{2026-06-14 22:02:41 +0400}: commit: Session 16: consolidate palm geometry validation, remove hand-laterality detection, add upload confirmation+swap, fix chat formatting/flash bugs
00d15c3 HEAD@{2026-06-14 21:44:27 +0400}: commit: refactor(session-15): consolidate palm geometry into single GPT call, add hand-confirm/swap UI
3fe33f0 HEAD@{2026-06-14 20:04:53 +0400}: commit: chore(session-15): diagnostic scripts + unlabeled test images
9e8597b HEAD@{2026-06-14 17:44:15 +0400}: commit: fix(session-15): slot-independent palm hand detection + working style rule 9
4bf3a11 HEAD@{2026-06-14 14:57:13 +0400}: commit: fix(session-15): dynamic fallback context_order on classify() API failure
4c2fa72 HEAD@{2026-05-30 14:29:35 +0400}: commit: chore(session-14): final session log update — complete entry, no debt
5c8ee4a HEAD@{2026-05-30 14:25:14 +0400}: commit: refactor(session-14): relocate multi-part rule, strip confidence UI from app.py
15601b1 HEAD@{2026-05-30 14:17:37 +0400}: commit: chore(session-14): mark session complete, update CLAUDE.md + SESSION_LOG
b771be4 HEAD@{2026-05-30 13:56:26 +0400}: commit: fix(session-14): palm slot-mismatch detection + multi-sub-question instruction
8c788fc HEAD@{2026-05-30 13:48:43 +0400}: commit: refactor(session-14): GPT query rewriter, gut config.py, delete context_router.py
4371f9b HEAD@{2026-05-30 13:25:02 +0400}: commit: feat(session-14): wire ContextBundle+classify() end-to-end; 37/37 tests passing
99fc976 HEAD@{2026-05-30 12:27:26 +0400}: commit: feat(session-14): unified classifier, hand_detail vision, prompt_builder new slots
797456a HEAD@{2026-05-30 11:53:19 +0400}: commit: feat(session-14): add ContextBundle dataclass — zero agent/ imports, availability_map()
4c394bc HEAD@{2026-05-30 11:37:11 +0400}: commit: chore(session-13): update CLAUDE.md + SESSION_LOG, fix app.py result collision
7753349 HEAD@{2026-05-30 11:08:29 +0400}: commit: feat(session-13): ingest Jyotish_Lal Kitab_B.M. Gosvami, purge LAL KITAB-1941
9f1dce2 HEAD@{2026-05-29 15:55:24 +0400}: commit: feat(session-12): fix multi_source_search book list — 14-book flat list with exact ChromaDB strings
ba769b2 HEAD@{2026-05-29 14:55:46 +0400}: commit: feat(session-11): cross-verification, multi-source retrieval, CQ fixes
368a6ab HEAD@{2026-05-29 14:43:38 +0400}: commit: feat(session-11): missing-context dialogue + disclaimer CQ guard
80f9797 HEAD@{2026-05-28 22:35:22 +0400}: commit: Session 10: session log + CLAUDE.md updated, known debt logged
b255c2d HEAD@{2026-05-28 22:34:35 +0400}: commit: Session 10 complete: dual-palm pipeline, rerun fix, nudge specificity, expander layout, 40/40 tests
b982e04 HEAD@{2026-05-28 21:54:47 +0400}: commit: Session 10: palm describe pipeline + rerun loop fix
631a6c4 HEAD@{2026-05-28 21:38:54 +0400}: commit: feat(session-10): context_order routing, dual-palm pipeline, validation + 25 tests passing
6134c30 HEAD@{2026-05-28 17:10:33 +0400}: commit: fix(.gitignore): separate Thumbs.db and data/sessions/ onto distinct lines
60c15a8 HEAD@{2026-05-28 16:49:51 +0400}: commit: docs: add LAYER FIRST working style rule to CLAUDE.md and .cursorrules
40c6ade HEAD@{2026-05-28 16:47:46 +0400}: commit: feat(prompt_builder): replace Palmistry queries with Context synthesis rules
d79aca9 HEAD@{2026-05-28 16:45:26 +0400}: commit: fix(astrosage_parser): merge repeated section occurrences across PDF page breaks
9fb4185 HEAD@{2026-05-28 15:53:33 +0400}: commit: Session 10: place autocomplete, astrosage parser tests, has_palm fix
7775be8 HEAD@{2026-05-28 15:22:51 +0400}: commit: Session 9 complete — update SESSION_LOG.md and CLAUDE.md session focus
27bb3b4 HEAD@{2026-05-28 15:20:22 +0400}: commit: refactor: token optimisation — remove stack/sessions/token-hygiene from CLAUDE.md, fix cursorrules agent dedup
fa75db4 HEAD@{2026-05-28 14:50:35 +0400}: commit: Session 10: pdf_context param + palm image upload
5de6722 HEAD@{2026-05-28 14:39:55 +0400}: commit: Session 10: wire context_router into chat flow + nudge display
77c1aa0 HEAD@{2026-05-28 14:26:32 +0400}: commit: Session 10: context_router.py - keyword-based context router with nudge builder
4f0daf3 HEAD@{2026-05-28 13:57:09 +0400}: commit: Session 9 complete - CLAUDE.md session focus updated
dfaa85f HEAD@{2026-05-28 12:29:21 +0400}: commit: Session 9: needs_disclaimer() wired - append DISCLAIMER only if GPT omits it
d001f95 HEAD@{2026-05-28 12:25:46 +0400}: commit: Session 9: wire AstroSage PDF upload + merge into kundali_context
77cb109 HEAD@{2026-05-28 12:17:12 +0400}: commit: Session 9: astrosage_parser.py - section reorder by _PRIORITY_ORDER complete
5681e29 HEAD@{2026-05-28 10:03:01 +0400}: commit: Session 8 complete: CLAUDE.md + SESSION_LOG updated
ae1f66e HEAD@{2026-05-28 09:41:02 +0400}: commit: Remove data artifacts from tracking, update .gitignore
bf8432a HEAD@{2026-05-28 09:40:00 +0400}: commit: Session 8: U-1,U-2,U-3,ISSUE-2,ISSUE-3,ISSUE-6 fixed + 6-agent framework + palm nudge Option C + 3 unit tests passing
e319afa HEAD@{2026-05-28 08:45:27 +0400}: commit: Add 6-agent framework: .claude/ agents, templates, CLAUDE.md wiring
3d10816 HEAD@{2026-05-28 00:08:13 +0400}: commit: Compress .cursorrules and ui_ux.md — remove redundant and stale rules
31ccb35 HEAD@{2026-05-27 23:57:51 +0400}: commit: Session 7: config.py REWRITE_MAP sanitizer + Streamlit frontend
e1328b2 HEAD@{2026-05-27 23:43:42 +0400}: commit: Add deferred TODOs per debate agent action list
dd0eedf HEAD@{2026-05-27 23:30:57 +0400}: commit: Add debate.md playbook agent
556a3e8 HEAD@{2026-05-27 23:21:02 +0400}: commit: Add ui_ux.md playbook agent
869a071 HEAD@{2026-05-27 19:53:15 +0400}: commit: Add format_kundali_context() to chart_calculator.py
7d1f88e HEAD@{2026-05-27 19:19:38 +0400}: commit: Session 5: chart_calculator.py — Vimshottari dasha, Lahiri ayanamsha, whole-sign houses, IST timezone
5afc37d HEAD@{2026-05-26 22:51:29 +0400}: commit: Crash recovery: per-book progress saves, run_overnight.py pipeline, embedder reads pre-chunked input
bce3dc9 HEAD@{2026-05-26 22:39:48 +0400}: commit: Pre-run config: sort PDFs by size, update book registry for Muhurta Chintamani
663abaf HEAD@{2026-05-26 22:20:18 +0400}: commit: Fix classify_page(): remove dead Pattern 3 planetary sub-check
fee33ef HEAD@{2026-05-26 21:56:44 +0400}: commit: Fix: add load_dotenv() to image_extractor.py; fix stale docstring in embedder.py
5e8570f HEAD@{2026-05-26 19:33:58 +0400}: commit: Add playbook_export/ — patterns, mistakes, decisions, checklists
c1b0bbb HEAD@{2026-05-26 19:23:19 +0400}: commit: Add playbook_export/ — reusable AI project setup templates
241eaba HEAD@{2026-05-26 19:13:23 +0400}: commit: Update CLAUDE.md: Session 4 translator.py marked COMPLETE
f6ef437 HEAD@{2026-05-26 19:12:56 +0400}: commit: Session 4: translator.py — Hindi ingestion pipeline
fb45725 HEAD@{2026-05-26 18:53:43 +0400}: commit: Session 4 plan: translator.py design locked in CLAUDE.md + .cursorrules
4ed50a0 HEAD@{2026-05-26 18:47:16 +0400}: commit: Revised session plan: 12-book registry, Sessions 4-8 roadmap
1f7800f HEAD@{2026-05-26 18:24:08 +0400}: commit: Session 3 complete: session wiring, history trim, 24/24 QA
ee48763 HEAD@{2026-05-26 17:13:41 +0400}: commit: Session 4: session_manager.py + default user context files
465b07d HEAD@{2026-05-26 16:46:14 +0400}: commit: Session 3 complete: prompt_builder.py + astrologer.py migration
8248d12 HEAD@{2026-05-26 16:38:46 +0400}: commit: Session 3: astrologer.py complete + QA updates
4d16d76 HEAD@{2026-05-26 16:13:26 +0400}: commit: Session 3: four-agent review system + query_engine.py
43fda8a HEAD@{2026-05-26 15:50:28 +0400}: commit: Session 2 complete: embedder working, 3029 chunks in ChromaDB
df37752 HEAD@{2026-05-26 14:22:44 +0400}: commit: Session 2: classifier, chunker, embedder, agent personas
8a0b680 HEAD@{2026-05-26 13:39:05 +0400}: commit: Session 2: mixed classifier, strip_devanagari, agent visual intelligence notes
41ade88 HEAD@{2026-05-26 12:00:27 +0400}: commit: Add working style standards to cursorrules and CLAUDE.md
34de4c7 HEAD@{2026-05-26 00:02:35 +0400}: commit: Session 1 complete: pdf_processor, image_extractor, chunker + overnight run started
5d0e0a4 HEAD@{2026-05-25 23:35:12 +0400}: commit: Add gitignore, remove large files from tracking
7277832 HEAD@{2026-05-25 23:32:51 +0400}: commit: Add book registry and topic tags to cursorrules
4fc44b3 HEAD@{2026-05-25 21:39:00 +0400}: commit: Add .cursorrules project context
1aa0e48 HEAD@{2026-05-25 21:13:10 +0400}: commit: Initial folder structure
1a5e989 HEAD@{2026-05-25 21:09:42 +0400}: clone: from https://github.com/sulabhschauhan/astro-agent.git
```
Reflog is a clean linear sequence of `commit` and one `clone` entry -- no `reset`, `rebase`, `checkout`, `stash` (pop/apply), or `commit (amend)` entries anywhere in the project's history. No evidence of branch-switching or history rewriting.

### git stash list

```
(empty)
```

### git fsck --unreachable --no-reflogs --dangling

```
(no unreachable/dangling objects)
```

### Commits that ADDED / REMOVED each progress file (dynamically located, not hardcoded)

| book | first commit adding it | commit removing it |
|---|---|---|
| Deva-keralam | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| Jataka Parijata with explanation of Pt. Kapileshvara Shastri and Vimala Hindi Tika of Pt. Shri Matri Prasad Shastri Series No. 10 - Kashi Sanskrit Series | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| Muhurtha-Chinthamani | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| Prasna Marga 1 | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| Prasna Marga 2 | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| Sarvartha-Chintamani | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| uttkalamrita-kalidas-ps-sastri | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| BPHS - 1 RSanthanam | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| BPHS - 2 RSanthanam | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| cheiroslanguageo00chei_1 | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| Saravali of Kalyana Varma Santhanam R. (Astrology) | bf8432a5986198154afa14acc78c5be0ed8e0a97 2026-05-28 09:40:00 +0400 | ae1f66e68538f1f00d25bbb079c4203a4fef0a41 2026-05-28 09:41:02 +0400 |
| Jyotish_Lal Kitab_B.M. Gosvami | (not found) | (never removed / still tracked) |

All 14 progress files were added to git in the **same single commit** (`bf8432a5986198154afa14acc78c5be0ed8e0a97`), and removed in the next commit ~62 seconds later. This is an accidental commit-then-revert, not a deliberate provenance event by itself -- but it gives us an **immutable git blob** of the corrupted files from the morning after the incident, independent of live filesystem mtimes.

### Independent corroboration via the immutable blob at `bf8432a5986198154afa14acc78c5be0ed8e0a97`

`git show bf8432a5986198154afa14acc78c5be0ed8e0a97:data/progress/Deva-keralam.json` -- first chunk_id: `Deva-keralam_p1_c0` (684 entries total).

**This confirms the `_c0` corruption was already present in the git-committed snapshot taken the morning of 2026-05-28 (09:40 local) -- i.e. independently of live mtimes, the corruption is proven to predate Session 13 (2026-05-30) by an immutable, tamper-evident source.**

`git show bf8432a5986198154afa14acc78c5be0ed8e0a97:data/chunked_chunks.json` -- Deva-keralam page 8 entries at that commit:
```
Deva-keralam_p8_c0  (len(text)=682)
Deva-keralam_p8_c1  (len(text)=562)
Deva-keralam_p8_c2  (len(text)=252)
```

At this commit, `chunked_chunks.json` still shows the single-suffixed, correct form for this page -- the double-suffix only appears in the *current* file (written 2026-05-30, Session 13). This is consistent with the chunking_code_audit's timeline: corruption of the progress files on 2026-05-27, compounded by a single re-chunk during Session 13.

### git log --all --since=2026-05-25 --until=2026-06-01 --name-status --pretty=fuller

Full output truncated per report constraints (first/last 50 lines); load-bearing commits are quoted in full above and below regardless of where they fall in this dump.

```
commit 4c2fa72e2c65a98d40a00d95be2287d97cc48320
Author:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
AuthorDate: Sat May 30 14:29:35 2026 +0400
Commit:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
CommitDate: Sat May 30 14:29:35 2026 +0400

    chore(session-14): final session log update — complete entry, no debt
    
    Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

M	CLAUDE.md
M	SESSION_LOG.md

commit 5c8ee4abc703878d63c89b2d7ee5de2a0512acab
Author:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
AuthorDate: Sat May 30 14:25:14 2026 +0400
Commit:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
CommitDate: Sat May 30 14:25:14 2026 +0400

    refactor(session-14): relocate multi-part rule, strip confidence UI from app.py
    
    prompt_builder.py: move MULTI-PART QUESTIONS instruction out of Language bullet
    list into a standalone named block after How you answer section.
    
    app.py: remove confidence score caption, low_confidence warning banner, and
    their backing storage (top_score/low_confidence) from both chat paths.
    low_confidence in ask() return dict and astrologer.py caveat logic untouched.
    
    Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

M	agent/prompt_builder.py
M	frontend/app.py

commit 15601b1770718f2bcd3abe655181c5efdef0fee6
Author:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
AuthorDate: Sat May 30 14:17:37 2026 +0400
Commit:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
CommitDate: Sat May 30 14:17:37 2026 +0400

    chore(session-14): mark session complete, update CLAUDE.md + SESSION_LOG
    
    Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>

M	CLAUDE.md
M	SESSION_LOG.md

commit b771be4e5c1a1dab3dda85a2f32a77e173b6f19b
Author:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
AuthorDate: Sat May 30 13:56:26 2026 +0400
Commit:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
[... 1172 lines omitted ...]
A	data/extracted_images/BPHS - 1 RSanthanam_page_1.jpg
A	data/extracted_images/BPHS - 1 RSanthanam_page_18.jpg
A	data/extracted_images/BPHS - 1 RSanthanam_page_22.jpg
A	data/extracted_images/BPHS - 1 RSanthanam_page_322.jpg
A	data/extracted_images/BPHS - 1 RSanthanam_page_378.jpg
A	data/extracted_images/BPHS - 1 RSanthanam_page_6.jpg
A	data/pdfs/BPHS - 1 RSanthanam.pdf
A	data/pdfs/BPHS - 2 RSanthanam.pdf
A	data/pdfs/Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri.pdf
A	data/pdfs/Saravali of Kalyana Varma Santhanam R. (Astrology).pdf
A	data/pdfs/cheiroslanguageo00chei_1.pdf
A	ingestion/image_extractor.py
A	ingestion/pdf_processor.py

commit 4fc44b3213a80dd01e19fb19937eb7e588ecd6a3
Author:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
AuthorDate: Mon May 25 21:39:00 2026 +0400
Commit:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
CommitDate: Mon May 25 21:39:00 2026 +0400

    Add .cursorrules project context

A	.cursorrules

commit 1aa0e48fb0064c7dfbabecb68d3566928a58e248
Author:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
AuthorDate: Mon May 25 21:13:10 2026 +0400
Commit:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
CommitDate: Mon May 25 21:13:10 2026 +0400

    Initial folder structure

A	agent/.gitkeep
A	api/.gitkeep
A	data/chroma_db/.gitkeep
A	data/extracted_images/.gitkeep
A	data/pdfs/.gitkeep
A	frontend/.gitkeep
A	ingestion/.gitkeep
A	retrieval/.gitkeep

commit 1a5e989cdd4d70072c4eb183b09b8be2d9c1282c
Author:     sulabhschauhan <sulabh.s.chauhan@gmail.com>
AuthorDate: Mon May 25 21:04:24 2026 +0400
Commit:     GitHub <noreply@github.com>
CommitDate: Mon May 25 21:04:24 2026 +0400

    Initial commit

A	README.md
```

## 3. PowerShell shell history

`C:\Users\sulab\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt`
- Total lines: 48
- File last-write time: **2024-11-03T17:19:05**
- 0 keyword matches.

`C:\Users\sulab\AppData\Roaming\Microsoft\PowerShell\PSReadLine\ConsoleHost_history.txt` -- not present on this system.

## 4. Python interactive history

- `C:\Users\sulab\.python_history` -- not present on this system
- `C:\Users\sulab\Documents\Python Scripts\astro-agent\.python_history` -- not present on this system

**`.ipynb_checkpoints` directories found (project root recursive + immediate parent):**
- `C:\Users\sulab\Documents\Python Scripts\.ipynb_checkpoints\Open_API_Key-checkpoint.py` (scope: parent dir (non-recursive), mtime: 2024-10-22T20:56:53)
- `C:\Users\sulab\Documents\Python Scripts\.ipynb_checkpoints\Test-checkpoint.ipynb` (scope: parent dir (non-recursive), mtime: 2024-10-24T14:39:52)

**`.ipynb` files found:**
- `C:\Users\sulab\Documents\Python Scripts\Test.ipynb` (scope: parent dir (non-recursive), mtime: 2025-12-24T18:27:08)

## 5. IDE / editor traces

- `.vscode/`: not present in project root
- `.idea/`: not present in project root
- VSCode local history (`%APPDATA%\Code\User\History`): 14 resource folders, 95 total entries, spanning 2024-10-20T11:33:47 to 2026-06-18T15:58:03 -- **this range fully covers the 2026-05-27 incident window**, so an absence of matches below is a meaningful negative result, not a coverage gap.

Matches referencing this project, run_single_book, progress dir, or chunker:
- `file:///c%3A/Users/sulab/Documents/Python%20Scripts/astro-agent/.claude/read_prompt.md`
  - saved at 2026-06-14T14:33:54
  - saved at 2026-06-14T15:01:08
  - saved at 2026-06-14T15:36:09
  - saved at 2026-06-14T15:58:37
  - saved at 2026-06-16T19:05:54
  - saved at 2026-06-18T15:58:03
- `file:///c%3A/Users/sulab/Documents/Python%20Scripts/astro-agent/SESSION_LOG.md`
  - saved at 2026-06-16T15:14:04
- `file:///c%3A/Users/sulab/Documents/Python%20Scripts/astro-agent/CLAUDE.md`
  - saved at 2026-06-14T16:34:01
  - saved at 2026-06-14T16:36:04
  - saved at 2026-06-16T15:13:36
  - saved at 2026-06-16T15:48:58

## 6. Sibling-repo / external-script possibility

Sibling directories at `C:\Users\sulab\Documents\Python Scripts` (names only, not traversed):
- .ipynb_checkpoints
- Open_API_Key.py
- Research Tool
- Restaurant Name Generator
- Test.ipynb
- __pycache__
- astro-agent

No symlinks or reparse points found inside `data/progress/` -- all files are ordinary files.

## 7. Scheduled tasks / startup hooks

`schtasks /Query /FO LIST /V` -- 7061 lines returned, 0 line(s) matching python/astro/chunker/repo-path.
No matches.

**Startup folder contents:**
- `C:\Users\sulab\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`: ['desktop.ini']
- `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp`: ['desktop.ini']

## 8. The 2026-05-30 Lal Kitab run_single_book.py invocation

`data/run_single_book.log` -- 8362 lines. Header lines captured by the script's own logging:
```
2026-05-30 09:50:18,182 - INFO - SINGLE BOOK INGEST STARTED  2026-05-30T05:50:18.182342+00:00
2026-05-30 09:50:18,182 - INFO - PDF:       data/pdfs/Jyotish_Lal Kitab_B.M. Gosvami.pdf
2026-05-30 09:50:18,182 - INFO - book_name: Jyotish_Lal Kitab_B.M. Gosvami
```

This is the PDF path / book name **parsed from `sys.argv[1]` by the script's own logging**, not a verbatim shell command-line capture -- `main(sys.argv[1])` is logged indirectly via `PDF:` and `book_name:` lines, but the literal invoking command (`python ingestion/run_single_book.py "..."`) and its working directory/shell are not recorded anywhere in this log.

Git commits/stash entries from 2026-05-30 touching `run_single_book.py` or its caller: see Axis 2's add/remove table and the `git log --all --since/--until` dump above -- only one commit (`7753349`) touches `ingestion/run_single_book.py`, adding it for the first and only time; no stash entries exist for that date (stash list is empty repo-wide).

## Outstanding gaps

Every question that could not be fully answered, and why:

1. No backup/temp files found under data/ — if a script wrote via a .tmp+rename pattern (as the project's own _save_progress() helpers do), the .tmp would only be visible if the process crashed mid-write. Its absence is consistent with either a clean write or simply no such pattern being used.
2. C:\Users\sulab\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt: last written 2024-11-03T17:19:05, over a year before the 2026-05-27 incident. This is a coverage gap, not a clean negative result -- this history mechanism was not active during the incident window, so its absence of matches proves nothing either way.
3. No .python_history file found anywhere checked — no Python REPL history available for this window.
4. run_single_book.log records the parsed PDF path/book name but not the literal shell command line, working directory, or which terminal/shell invoked it.

**The central open question remains unresolved**: no command-line, shell-history, Python-history, IDE-history, scheduled-task, or git-tracked evidence was found anywhere checked that identifies the specific process which overwrote the 8 progress files in the 2026-05-27 19:20:01-19:27:40 window (the Axis 2 git-blob check ruled out a second re-chunk before 2026-05-28 09:40 -- chunked_chunks.json at that commit still shows the single-suffixed correct form, so the only unexplained event is the progress-file write itself). The PowerShell history mechanism that might have captured an interactive command was not active during this period (last written 2024-11-03) -- this is the single largest coverage gap, and without it, a manually-typed `python -c "..."` one-liner or short ad hoc script run directly in a terminal remains consistent with all available evidence but cannot be confirmed or further localized in time beyond the existing mtime/git-blob bounds.
