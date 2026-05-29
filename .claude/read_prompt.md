# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"



Read CLAUDE.md before doing anything.
Make ONE surgical edit to ingestion/query_engine.py — the books default list inside multi_source_search() only. No other changes.
Replace the current 5-item hardcoded list with this exact 14-item list using the exact strings below (copy precisely — these are the actual book_name values stored in ChromaDB):
"BPHS - 1 RSanthanam"
"BPHS - 2 RSanthanam"
"cheiroslanguageo00chei_1"
"Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri"
"Saravali of Kalyana Varma Santhanam R. (Astrology)"
"Deva-keralam"
"Muhurtha-Chinthamani"
"Prasna Marga 1"
"Prasna Marga 2"
"Jataka Parijata with explanation of..."
"Sarvartha-Chintamani"
"Hasta Samudrika Shastra by Shri Vasant Lal Vyas 1976 Delhi - Janata Prakashan"
"LAL KITAB-1941"
"uttkalamrita-kalidas-ps-sastri"
Also update the docstring line that says 2 results per book × 5 books = 10 max chunks to 2 results per book × 14 books = 28 max chunks.
After the edit, run the full test suite once and report pass/fail count only. No other changes.