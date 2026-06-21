# Post-Delete Saturn-11th Retrieval Re-run

**Generated:** 2026-06-21 13:05:14 UTC  
**Collection:** `astro_chunks` @ `data/chroma_db`  
**Query:** `'Saturn transit eleventh house effects classical'`, k=8, via `ingestion.query_engine.search()` (production path, unmodified)  
**Read-only run** -- no ChromaDB writes. One OpenAI embedding call for the query text, one `collection.query()` call.

## Post-delete top-8

| # | chunk_id | book_name | page_ref | score | text (first 250 chars) |
|---|---|---|---|---|---|
| 1 | `Deva-keralam_p147_c2` | Deva-keralam | 147 | 0.6686 | (b) Saturn’s Transit in 12th House: If Saturn be in transit in the 12th house which happens to be his close friend’s place, the subject will be engaged in thoughts ofa low caste woman ("Vrishali" apart from meaning “low caste woman” also means an unm |
| 2 | `Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri_p33_c1` | Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri | 33 | 0.6543 | other planets.  Effects of the transit of the Sun through the 12 houses.  Effects of the Moon’s'transit through the 12 houses.  Effects of Mar’s transit over the 12 houses.  Effects of Mercury's transit over the 12 houses.  Effect of Jupiter's transi |
| 3 | `Deva-keralam_p59_c1` | Deva-keralam | 59 | 0.6449 | to the native. Loss of quadrupeds, lands, calling and honour will follow. The 5th house having Saturn in transit will cause wavering mind, and entanglement in many (impracticable) thoughts (or plans). Destruc- tion of enemies and great comforts will  |
| 4 | `Deva-keralam_p59_c0` | Deva-keralam | 59 | 0.6403 | 42 Chandra Kala Nadi  3085. Saturn’s Transit in 12 Houses From As- cendant: When Saturn is found in transit in the respective bhavas counted from the ascendant, pre- dict following effects in order: Ist - danger; 2nd loss of money; 3rd - firm positio |
| 5 | `Deva-keralam_p59_c2` | Deva-keralam | 59 | 0.6326 | Notes: The concerned lines dealing with Saturn’s transit in 11th and 12th from ascendant are missing, as attributed to another source consulted by the author. The deficit can be made up by sloka 3084 supra.  The following information on effects of Sa |
| 6 | `Deva-keralam_p153_c0` | Deva-keralam | 153 | 0.6264 | 136  532 -536.Saturn’s Transit Effects: (a) Danger, damage, wealth, abdominal disease, great fear, de- struction of enemies, great courage, death, physical decay, suffering, gains and losses are the effects of Saturn moving in 12 places in order.  (b |
| 7 | `Deva-keralam_p147_c1` | Deva-keralam | 147 | 0.6198 | 482 - 485. (a) Effects of Saturn in Transit in Various Nakshatras: Saturn transiting the Janma Nakshatra will produce royal wrath, grief and infirm finances. If the transit be in the 2nd Nakshatra,  wealth, comforts, ornaments and robes will be ga- l |
| 8 | `Deva-keralam_p202_c2` | Deva-keralam | 202 | 0.6172 | (b) Jupiter (instead of Saturn) in transit in an above place will cause great happiness in respect of the Bhava, and the Bhava effects will progress.  Notes: (a) For example, take the 2nd house in case of Capricorn ascendant. The 8th therefrom (i.e.  |

## Distinct-passage check

- Distinct passages in post-delete top-8: 8/8
- Within-result duplicates: 0 -- PASS (0 expected)

## New vs. pre-delete top-8

- Pre-delete distinct passages (from spikes/saturn_11th_comparison.md): 5
- Post-delete results that match a pre-delete passage (held over): 5
- **Post-delete results that are NEW (not in the pre-delete top-8): 3**

New passages:

- `Deva-keralam_p153_c0` (Deva-keralam p.153, score=0.6264): 136  532 -536.Saturn’s Transit Effects: (a) Danger, damage, wealth, abdominal disease, great fear, de- struction of enemies, great courage, death, physical decay, suffering, gains and losses are the e
- `Deva-keralam_p147_c1` (Deva-keralam p.147, score=0.6198): 482 - 485. (a) Effects of Saturn in Transit in Various Nakshatras: Saturn transiting the Janma Nakshatra will produce royal wrath, grief and infirm finances. If the transit be in the 2nd Nakshatra,  w
- `Deva-keralam_p202_c2` (Deva-keralam p.202, score=0.6172): (b) Jupiter (instead of Saturn) in transit in an above place will cause great happiness in respect of the Bhava, and the Bhava effects will progress.  Notes: (a) For example, take the 2nd house in cas

Held-over passages (also in pre-delete top-8):

- `Deva-keralam_p147_c2` (Deva-keralam p.147, score=0.6686)
- `Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri_p33_c1` (Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri p.33, score=0.6543)
- `Deva-keralam_p59_c1` (Deva-keralam p.59, score=0.6449)
- `Deva-keralam_p59_c0` (Deva-keralam p.59, score=0.6403)
- `Deva-keralam_p59_c2` (Deva-keralam p.59, score=0.6326)

## Clean-book appearance check

- 1 result(s) from the 6 clean books appear in the post-delete top-8.
  - 1 held over (already ranked in the pre-delete top-8 too, not a new effect of this delete):
    - `Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri_p33_c1` (Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri p.33, score=0.6543)

## Subjective on-topic assessment (manual review, full text read -- not keyword-scored)

Honest count: **2 of 8** results directly and specifically address Saturn's transit effect in the 11th house. The other 6 break down as follows:

| # | chunk_id | verdict | why |
|---|---|---|---|
| 1 | `Deva-keralam_p147_c2` | adjacent, not on-topic | Saturn transit, but explicitly the **12th** house, not 11th. |
| 2 | `Phaladeepika_p33_c1` | off-topic | Table-of-contents heading -- lists chapter topics, has no actual content. |
| 3 | `Deva-keralam_p59_c1` | adjacent, not on-topic | Saturn-transit-by-house list, but this fragment only covers 5th-10th; text ends "...ascendant etc." right before reaching 11th. |
| 4 | `Deva-keralam_p59_c0` | **on-topic** | Explicit 12-house Saturn-transit list that states "11th - gains" by name. |
| 5 | `Deva-keralam_p59_c2` | **on-topic** | Explicitly names "Saturn's transit in 11th and 12th from ascendant" (flagging the source's own missing lines) and supplies a fallback: "11th - pleasures and wealth." Meta/caveated, but genuinely about the asked question. |
| 6 | `Deva-keralam_p153_c0` | adjacent, not on-topic | Another Saturn-transit-by-house list, but this chunk's text is truncated at the 4th house -- never reaches 11th. |
| 7 | `Deva-keralam_p147_c1` | off-topic | Saturn transiting Nakshatras (lunar mansions counted from Janma Nakshatra) -- a different classification system from houses-from-ascendant entirely. |
| 8 | `Deva-keralam_p202_c2` | off-topic | Worked example about Jupiter substituting for Saturn on a 2nd-house illustration; no mention of the 11th house. |

**Not an improvement in relevance, only in bloat.** The 2 on-topic results are the exact same 2 (Deva-keralam p59, c0/c2) that were already the "legitimate signal" pre-delete -- this delete didn't change which passages are genuinely on-topic, it just removed their duplicate copies. The TOC heading and the 12th-house passage are *still* in the top-8 (held over, never duplicates, so untouched by this delete). The 3 newly-surfaced slots freed up by dedup were filled with comparably off-topic content (a nakshatra-based passage, a Jupiter/2nd-house example, a truncated house-list), not better content. This confirms the Session 22 finding stands: the delete fixed the **data layer** (duplicate pollution -- see Check 1, fully resolved), but the **retrieval layer**'s relevance problem (embedding similarity surfacing TOC headings and wrong-house passages above the two genuinely on-topic ones) is untouched and remains exactly as broken as the spike found it.

## Book distribution of post-delete top-8

- Deva-keralam: 7
- Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri: 1

