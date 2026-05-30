# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"


Read CLAUDE.md before doing anything.
Two tasks in sequence. Stop and report after each.
Task 1 — Purge LAL KITAB-1941 from ChromaDB:

Fetch all chunk IDs where book_name == "LAL KITAB-1941"
Print count before deletion
Delete them
Verify count after deletion is 0
Print confirmation

Task 2 — Run existing ingestion pipeline on new Lal Kitab PDF:

Source file: data/pdfs/Jyotish_Lal Kitab_B.M. Gosvami.pdf
Run exactly the same pipeline used for all other English books:
pdf_processor → image_extractor → chunker → embedder
Do NOT run translator.py — this is an English PDF
Use the existing run_overnight.py or call each stage in order as done for previous books
Print progress at each stage: page count, chunk count after chunker, chunk count after embedder
Print the exact book_name string stored in ChromaDB after embedding (check collection metadata)

Do not modify any pipeline code. Use existing functions as-is. Report after Task 1 completes before starting Task 2.