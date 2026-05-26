"""
translator.py
Translates Hindi page chunks to English using GPT-4o-mini.
Pipeline position: pdf_processor → image_extractor → chunker → translator → embedder
Reads data/all_chunks.json, writes data/translated_chunks.json.
Supports crash recovery: restarts from translated_chunks.json if it already exists.
"""

import json
import logging
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

# Partial-match stems (case-insensitive contains) — update if PDF filenames differ.
# Run pdf_processor on Hindi PDFs first, then check book_name values in all_chunks.json.
HINDI_BOOKS: set[str] = {"hasta samudrika", "jataka parijata", "lal kitab"}

INPUT_PATH = "data/all_chunks.json"
OUTPUT_PATH = "data/translated_chunks.json"
GPT_MODEL = "gpt-4o-mini"
DEVANAGARI_HIN_THRESHOLD = 0.25  # consistent with chunker.py DEVANAGARI_HIN_THRESHOLD
SAVE_INTERVAL = 50               # write progress to disk every N translated chunks
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BASE_DELAY = 10       # seconds; doubles each retry (10, 20, 40)

# GPT-4o-mini pricing — update if Anthropic pricing changes
INPUT_COST_PER_TOKEN  = 0.15 / 1_000_000   # $0.15 / 1M input tokens
OUTPUT_COST_PER_TOKEN = 0.60 / 1_000_000   # $0.60 / 1M output tokens

SYSTEM_PROMPT = (
    "You are a professional translator specializing in classical Hindi texts on "
    "Vedic astrology and palmistry.\n\n"
    "Translate the following Hindi text to English. Rules:\n"
    "- Preserve all Sanskrit and Vedic technical terms in romanized form: "
    "Graha, Bhava, Nakshatra, Rasi, Lagna, Yoga, Dasha, Mahadasha, Antardasha, "
    "Ayanamsha, etc.\n"
    "- Do not translate proper nouns, deity names, or names of sages\n"
    "- Preserve the original paragraph structure exactly\n"
    "- Output only the English translation — no explanations, notes, or commentary"
)


# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def _is_hindi_book(book_name: str) -> bool:
    """Case-insensitive partial match against HINDI_BOOKS stems."""
    name_lower = book_name.lower()
    return any(stem in name_lower for stem in HINDI_BOOKS)


def _devanagari_fraction(text: str) -> float:
    """Fraction of non-whitespace characters that are Devanagari (U+0900–U+097F)."""
    non_ws = [c for c in text if not c.isspace()]
    if not non_ws:
        return 0.0
    return sum(1 for c in non_ws if "ऀ" <= c <= "ॿ") / len(non_ws)


def _should_translate(chunk: dict) -> bool:
    """True if this chunk is a candidate for translation in this run."""
    if not _is_hindi_book(chunk.get("book_name", "")):
        return False
    if chunk.get("page_type") == "diagram":
        return False  # diagram pages handled by image_extractor.py
    if "original_hindi" in chunk:
        return False  # already translated — idempotency guard
    text = chunk.get("text", "")
    if not text.strip():
        return False
    return _devanagari_fraction(text) >= DEVANAGARI_HIN_THRESHOLD


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------

def _translate_text(text: str, client: OpenAI) -> tuple[str, float]:
    """
    Translate one Hindi text string to English via GPT-4o-mini.

    Returns:
        (translated_text, cost_usd)

    Raises:
        RateLimitError: all retries exhausted.
        RuntimeError: GPT returned empty translation.
    """
    for attempt in range(RATE_LIMIT_RETRIES):
        try:
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": text},
                ],
                temperature=0.1,
            )
            translated = response.choices[0].message.content.strip()
            if not translated:
                raise RuntimeError("GPT returned empty translation")
            cost = (
                response.usage.prompt_tokens     * INPUT_COST_PER_TOKEN
                + response.usage.completion_tokens * OUTPUT_COST_PER_TOKEN
            )
            return translated, cost
        except RateLimitError:
            if attempt == RATE_LIMIT_RETRIES - 1:
                raise
            delay = RATE_LIMIT_BASE_DELAY * (2 ** attempt)
            logger.warning(
                "Rate limit — retrying in %ds (attempt %d/%d)",
                delay, attempt + 1, RATE_LIMIT_RETRIES,
            )
            time.sleep(delay)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _save(chunks: list[dict], path: str) -> None:
    """Atomic write — .tmp then os.replace to prevent partial writes on crash."""
    p = Path(path)
    tmp = p.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(p)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to save {path}: {e}") from e


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def translate_all(
    chunks: list[dict],
    client: OpenAI,
    output_path: str = OUTPUT_PATH,
    save_interval: int = SAVE_INTERVAL,
) -> tuple[list[dict], int, float]:
    """
    Translate all eligible Hindi chunks in the list (mutates in-place).
    Saves progress to output_path every save_interval translated chunks.

    Returns:
        (chunks, translated_this_run, total_cost_usd)
    """
    indices = [i for i, c in enumerate(chunks) if _should_translate(c)]
    total = len(indices)

    if total == 0:
        logger.info("No chunks require translation.")
        return chunks, 0, 0.0

    logger.info("%d chunks to translate", total)
    translated_count = 0
    total_cost = 0.0

    for pos, idx in enumerate(indices, start=1):
        chunk = chunks[idx]
        try:
            translated, cost = _translate_text(chunk["text"], client)
            chunk["original_hindi"]    = chunk["text"]
            chunk["text"]              = translated
            chunk["translation_model"] = GPT_MODEL
            chunk["translation_cost"]  = round(cost, 8)
            total_cost    += cost
            translated_count += 1
            logger.info(
                "[%d/%d] %s — $%.6f",
                pos, total, chunk["chunk_id"], cost,
            )
        except Exception as e:
            logger.error("Failed to translate %s: %s — skipping", chunk["chunk_id"], e)
            continue

        if translated_count % save_interval == 0:
            _save(chunks, output_path)
            logger.info(
                "Progress saved: %d/%d translated, $%.4f so far",
                translated_count, total, total_cost,
            )

    return chunks, translated_count, total_cost


def run_pipeline(
    input_path: str = INPUT_PATH,
    output_path: str = OUTPUT_PATH,
) -> dict:
    """
    Full translation pipeline.
    If output_path already exists, loads it as the base (crash recovery).

    Returns:
        {total_chunks, translated_this_run, total_translated, total_cost_usd, output_path}
    """
    if not HINDI_BOOKS:
        logger.warning(
            "HINDI_BOOKS is empty — no chunks will be translated. "
            "Populate HINDI_BOOKS in translator.py with your Hindi PDF stem names."
        )

    base_path = output_path if Path(output_path).exists() else input_path
    logger.info("Loading chunks from %s", base_path)

    try:
        with open(base_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Input file not found: {base_path}. "
            "Run pdf_processor.py first to generate all_chunks.json."
        )

    logger.info("Loaded %d page chunks", len(chunks))

    already_translated = sum(1 for c in chunks if "original_hindi" in c)
    if already_translated:
        logger.info("Resuming — %d chunks already translated", already_translated)

    client = OpenAI()
    chunks, translated_this_run, total_cost = translate_all(chunks, client, output_path)

    _save(chunks, output_path)
    logger.info("Saved all chunks to %s", output_path)

    total_translated = sum(1 for c in chunks if "original_hindi" in c)

    summary = {
        "total_chunks":        len(chunks),
        "translated_this_run": translated_this_run,
        "total_translated":    total_translated,
        "total_cost_usd":      round(total_cost, 6),
        "output_path":         output_path,
    }
    logger.info(
        "Done — %d translated this run, %d total, $%.4f",
        translated_this_run, total_translated, total_cost,
    )
    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    summary = run_pipeline()
    print("\n--- Translation Report ---")
    print(f"Total chunks:       {summary['total_chunks']}")
    print(f"Translated this run:{summary['translated_this_run']}")
    print(f"Total translated:   {summary['total_translated']}")
    print(f"Total cost:         ${summary['total_cost_usd']:.4f}")
    print(f"Output:             {summary['output_path']}")
