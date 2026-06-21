# Path (c) Q&A Validation

**Generated:** 2026-06-21 17:37:24 UTC  
**Collection:** `astro_chunks` @ `data/chroma_db` (post-dedup, 7,743 chunks)  
**Model:** `gpt-4o-mini`, temperature=0 (matches spikes/interpretive_text_saturn_11th.py step3/step4)  
**Read-only on ChromaDB** -- one `search()` call (embed + `.query()`) and one chat completion per question, no retries, no chained calls.

## 1. Parent paragraph

**PDF page reference: NOT AVAILABLE.** No `Sheridan_Kundli.pdf` (or any file with "Sheridan" in its name) exists anywhere in this repository -- confirmed via a full-tree glob. `data/pdfs/` holds only two personal AstroSage exports, and both belong to other reference-chart subjects (`VedicReport5-24-202610-01-26PM.pdf` is Sulabh's, `Wife_VedicReport.pdf` is Surbhi's), not Sheridan's. The paragraph below is therefore sourced from `spikes/interpretive_text_saturn_11th.py`'s `ASTROSAGE_PARA` constant, confirmed byte-identical (diffed) against Section A of the saved Session 22 artifact `spikes/saturn_11th_comparison.md` -- i.e. it IS verified to be "the exact paragraph that Output A in the Session 22 spike used," but its original PDF page cannot be cited because the source PDF is not in this repository. Not fabricated.

> SATURN is in Pisces in your 11th House. Physically as well as mentally you will be very courageous during this period. This is a good phase for your relatives. Go for attempts in your career life as the success is assured. Gain of material things is also indicated. You will purchase land and machinery during this period. Substantial gains in your business and trades are assured. Your enemies will not be able to plunk before you. You will come into contact with people from far off places. This period is also very good as far as love life is concerned. You will receive full support from your family members.

## 2. Per-query results

### Q1 (definitional)

**Question:** What does the 11th house from ascendant classically signify?

**Top-5 retrieved chunks:**

| # | chunk_id | source | page | score |
|---|---|---|---|---|
| 1 | `BPHS - 1 RSanthanam_p191_c0` | BPHS - 1 RSanthanam | 191 | 0.6581 |
| 2 | `BPHS - 1 RSanthanam_p400_c1` | BPHS - 1 RSanthanam | 400 | 0.6485 |
| 3 | `BPHS - 1 RSanthanam_p182_c1` | BPHS - 1 RSanthanam | 182 | 0.6416 |
| 4 | `Saravali of Kalyana Varma Santhanam R. (Astrology)_p42_c1` | Saravali of Kalyana Varma Santhanam R. (Astrology) | 42 | 0.6364 |
| 5 | `Deva-keralam_p25_c1` | Deva-keralam | 25 | 0.6017 |

**Q&A output (verbatim):**

> The 11th house from the ascendant classically signifies gains, friendships, and aspirations. According to Brihat Parasara Hora Shastra (BPHS, p. 191), if the ascendant lord is in the 11th house, the native will be endowed with gains, good qualities, and fame. Additionally, Saravali states that the 11th house is associated with happiness and prosperity (Saravali, p. 42). Thus, it is a house of material and social benefits, enhancing one's overall well-being.

**Rubric scores:**

| Item | Score | Justification |
|---|---|---|
| R1 Citation present | Y | Names BPHS p.191 and Saravali p.42 -- both verified to match actually-retrieved chunks (#1 `BPHS - 1 RSanthanam_p191_c0`, #4 `Saravali..._p42_c1`). |
| R2 No contradiction | Y | Doesn't mention Saturn at all (general house-signification answer); fully consistent with the parent paragraph's gains/prosperity framing, nothing to contradict. |
| R3 Voice maintained | Y | Mostly classical-citation register ("the native will be endowed with..."); closing clause "enhancing one's overall well-being" drifts slightly toward generic-wellness phrasing but doesn't dominate the answer. |
| R4 Specificity | Y | Directly answers the definitional question with two named sources, not a generic non-answer. |

**Primary (R1+R2+R3): 3/3**

### Q2 (mechanism)

**Question:** Why does Saturn in the 11th house tend to give gains rather than restrictions?

**Top-5 retrieved chunks:**

| # | chunk_id | source | page | score |
|---|---|---|---|---|
| 1 | `Jyotish_Lal Kitab_B.M. Gosvami_p579_c0` | Jyotish_Lal Kitab_B.M. Gosvami | 579 | 0.6387 |
| 2 | `Jyotish_Lal Kitab_B.M. Gosvami_p129_c1` | Jyotish_Lal Kitab_B.M. Gosvami | 129 | 0.6369 |
| 3 | `Deva-keralam_p163_c0` | Deva-keralam | 163 | 0.6165 |
| 4 | `Jyotish_Lal Kitab_B.M. Gosvami_p554_c2` | Jyotish_Lal Kitab_B.M. Gosvami | 554 | 0.6068 |
| 5 | `Deva-keralam_p148_c0` | Deva-keralam | 148 | 0.6003 |

**Q&A output (verbatim):**

> Saturn in the 11th house is considered auspicious for gains because this house represents fortune, earnings, and the support of friends and networks. As noted in the *Lal Kitab* (p. 129), the 11th house is associated with lifelong earnings and the benefits derived from others, which aligns with the positive outcomes of Saturn when it is in a benefic condition. Additionally, Saturn's placement here can enhance one's ability to achieve material success and stability, as it governs the accumulation of wealth through hard work and perseverance. Thus, rather than restrictions, Saturn in this position often leads to substantial gains and support from one's social circle.

**Rubric scores:**

| Item | Score | Justification |
|---|---|---|
| R1 Citation present | Y | Names Lal Kitab p.129, matching retrieved chunk #2 (`Jyotish_Lal Kitab_B.M. Gosvami_p129_c1`). |
| R2 No contradiction | Y | "Gains," "support," "material success" all align with the parent paragraph's gains/family-support claims; nothing contradicted. |
| R3 Voice maintained | **N** | "Support of friends and **networks**," "**ability to achieve** material success and **stability**," "**hard work and perseverance**" -- this is generic self-help/career-coaching vocabulary, not classical-astrologer diction. No classical term (bhava, karaka, yoga) or source-text phrasing appears outside the one citation; the explanatory frame is modern-positivity, not Parashara's voice. |
| R4 Specificity | Y | Engages the actual "why gains not restrictions" mechanism (house signification + benefic condition), even though the explanation is shallow. |

**Primary (R1+R2+R3): 2/3 -- FAILS the 3/3 bar**

### Q3 (cross-placement)

**Question:** How does Saturn in the 11th differ in effect from Saturn in the 12th?

**Top-5 retrieved chunks:**

| # | chunk_id | source | page | score |
|---|---|---|---|---|
| 1 | `Deva-keralam_p59_c2` | Deva-keralam | 59 | 0.5849 |
| 2 | `Deva-keralam_p82_c3` | Deva-keralam | 82 | 0.5832 |
| 3 | `Deva-keralam_p153_c0` | Deva-keralam | 153 | 0.5685 |
| 4 | `Jyotish_Lal Kitab_B.M. Gosvami_p64_c1` | Jyotish_Lal Kitab_B.M. Gosvami | 64 | 0.5616 |
| 5 | `Jyotish_Lal Kitab_B.M. Gosvami_p554_c0` | Jyotish_Lal Kitab_B.M. Gosvami | 554 | 0.5609 |

**Q&A output (verbatim):**

> Saturn in the 11th house is associated with pleasures, wealth, and the support of friends and relatives, as indicated in Deva-keralam (p153). In contrast, Saturn in the 12th house brings about wandering, fear, and potential losses, leading to a more challenging period (Deva-keralam, p153). Thus, while Saturn in the 11th fosters material gains and social connections, its placement in the 12th can lead to isolation and difficulties. The effects of these placements highlight the contrasting nature of Saturn's influence in these houses.

**Rubric scores:**

| Item | Score | Justification |
|---|---|---|
| R1 Citation present | Y, **but verified mis-paginated** | Cites "Deva-keralam (p153)" for the "11th-pleasures/12th-wandering" claim. Fetched both chunks directly: that exact line ("11th - pleasures and wealth; 12th - wandering and fear") lives in retrieved chunk #1, `Deva-keralam_p59_c2`, NOT chunk #3 `Deva-keralam_p153_c0` (which only covers natal-Saturn houses 1st-4th and never reaches 11th/12th). Book name is right, the page is wrong -- a real citation hallucination, see Section 4. |
| R2 No contradiction | Y | Parent paragraph only discusses Saturn-in-11th; nothing here contradicts it (11th-pleasures/wealth is consistent), and the 12th-house claim is about a placement the parent never addresses. |
| R3 Voice maintained | Y | Closely paraphrases the source's terse house-by-house listing style; "social connections" and "isolation and difficulties" lean mildly modern but don't dominate. |
| R4 Specificity | Y | Directly contrasts the two placements as asked, with a clear directional claim for each. |

**Primary (R1+R2+R3): 3/3 on the literal binary, but flagged -- the citation is confidently wrong, not just imprecise (see Section 4).**

**Deeper issue beyond the binary rubric:** the source line itself (`Deva-keralam_p59_c2`) is explicitly a *natal-Saturn-relative* reference table ("information on effects of Saturn's transit with reference to concerned natal positions"), not the *ascendant-relative* transit table the question and parent paragraph are actually about (transit-from-Lagna). The model silently used the natal-Saturn-relative "11th/12th" labels as if they were ascendant-relative ones, on top of citing the wrong page. The conclusion happens to be directionally consistent with the correct ascendant-relative source (`Deva-keralam_p59_c0`'s "11th - gains" from the from-ascendant list), so this isn't a contradiction, but it is a frame-conflation the rubric's binary R1/R2 don't catch.

### Q4 (edge-case, documented corpus gap)

**Question:** What do classical texts say specifically about Saturn's transit through the 11th from ascendant when natal Moon is in Aries?

**Top-5 retrieved chunks:**

| # | chunk_id | source | page | score |
|---|---|---|---|---|
| 1 | `Deva-keralam_p59_c2` | Deva-keralam | 59 | 0.6655 |
| 2 | `Deva-keralam_p59_c0` | Deva-keralam | 59 | 0.6132 |
| 3 | `Deva-keralam_p147_c2` | Deva-keralam | 147 | 0.6028 |
| 4 | `Deva-keralam_p153_c0` | Deva-keralam | 153 | 0.6014 |
| 5 | `Deva-keralam_p59_c1` | Deva-keralam | 59 | 0.6006 |

**Q&A output (verbatim):**

> According to classical texts, specifically Deva-keralam (p59), when Saturn transits the 11th house from the ascendant, it is associated with gains and pleasures. This aligns with the positive indications of success and material acquisition mentioned in your parent paragraph. Additionally, the transit is said to bring wealth and fulfillment of desires, which further supports the favorable outcomes for career and relationships during this period. Thus, the transit of Saturn through the 11th house while the natal Moon is in Aries is indeed auspicious for gains and support from relatives.

**Rubric scores:**

**Q4 special-case check first:** does the output give the explicit "classical sources don't speak directly to this..." honest-gap answer the stress test was designed to elicit? **No.** The word "Aries" and the word "Moon" (as a natal placement) never appear anywhere in the output. None of the 5 retrieved passages address a natal-Moon-sign-conditional reading of this transit either (all 5 are generic Saturn-transit-by-house content with no Moon-sign branching) -- exactly the documented corpus gap the question was designed to probe. Rather than naming that gap, the model silently dropped the Moon-in-Aries clause and answered the easier, already-supported question ("Saturn transits 11th from ascendant = gains") as if it were the full question asked. This does not qualify for the Q4 honest-non-citation pass rule, so it is scored on the general rubric below, held to the question actually asked.

| Item | Score | Justification |
|---|---|---|
| R1 Citation present | Y | Cites Deva-keralam p.59, and this time the page is correct -- chunk #1 `Deva-keralam_p59_c2` does say "11th - pleasures and wealth." Accurate citation, unlike Q3. |
| R2 No contradiction | Y | Content doesn't contradict the parent paragraph. (The deeper problem is omission, not contradiction -- see below.) |
| R3 Voice maintained | **N** | "Aligns with the **positive indications of success and material acquisition** mentioned in your parent paragraph," "**favorable outcomes for career and relationships**" -- this reads as validating/restating the AstroSage paragraph's own generic-positivity register rather than speaking independently in classical diction. Closer to therapeutic affirmation than Parashara's voice. |
| R4 Specificity | **N** | Never engages the question's actual hard part (Moon-in-Aries). Answers a different, generic, easier question and presents it as if it fully answered the one asked -- a textbook "generic restatement" failure even though the prose is fluent. |

**Primary (R1+R2+R3): 2/3 -- FAILS the 3/3 bar.** This is the most important single result in this report: the deliberate stress test did not produce the hoped-for honest-gap answer. It produced a confident, well-cited, *non-hallucinated* answer to a question that was not the one asked, with no acknowledgment that the harder half of the question went unaddressed.

## 3. Aggregate scoring

### Per-query primary score (R1+R2+R3 out of 3)

| Query | R1 | R2 | R3 | Primary | 3/3? |
|---|---|---|---|---|---|
| Q1 (definitional) | Y | Y | Y | 3/3 | YES |
| Q2 (mechanism) | Y | Y | N | 2/3 | no |
| Q3 (cross-placement) | Y* | Y | Y | 3/3* | YES* |
| Q4 (edge-case) | Y | Y | N | 2/3 | no |

\* Q3's R1 passes the literal binary (a source+page is present) but the page is verified wrong -- see Section 2 and Section 4. Treating Q3 as a clean pass overstates citation reliability; if mis-paginated citations are scored as R1=N instead, Q3 drops to 2/3 and the pass bar is met by **0 of 4** questions, not 2.

### Pass bar: 3/3 on primary signals across all 4 questions

**Literal scoring: 2/4 (Q1, Q3) at 3/3.** Does not meet "3/3 across all 4 questions."
**Citation-accuracy-adjusted scoring (Q3's mis-paginated citation counted as a real R1 failure): 1/4 (Q1 only) at 3/3.**

Either way, the pass bar is **not met**.

### Secondary specificity tally (R4, informational, not gating)

| Query | R4 |
|---|---|
| Q1 | Y |
| Q2 | Y |
| Q3 | Y |
| Q4 | **N** |

**3/4 pass on R4.** The one R4 failure (Q4) is the most consequential of the four, since it's specifically the question designed to test whether the system handles a documented corpus gap honestly.

## 4. Honest verdict

**Did path (c) pass primary signals?** No. On the literal binary rubric, 2 of 4 questions (Q1, Q3) hit 3/3; on a citation-accuracy-adjusted reading that counts Q3's verified-wrong page citation as a real R1 failure, only 1 of 4 (Q1) hits 3/3. The task's own bar was "3/3 across all 4 questions" -- this run clears that bar on zero to two questions depending how strictly citation accuracy is weighed, not four. Path (c) does not pass cleanly as tested.

The failure pattern is consistent and structural, not random noise:
- **R3 (voice) failed on Q2 and Q4** -- both times the model drifted toward the AstroSage paragraph's own generic-positivity/self-help register ("networks," "ability to achieve... stability," "aligns with the positive indications... mentioned in your parent paragraph") rather than holding strict classical-citation diction. This is the same voice-degradation failure mode the Session 22 spike found in the *layered* generation path -- it is now showing up in the supposedly-safer *Q&A-only* path too, just less severely. Downscoping to Q&A-only reduced but did not eliminate this failure mode.
- **Citation accuracy is not free just because retrieval ran.** Q3 demonstrates the model can name a real, retrieved book correctly while attributing the cited content to the wrong page within that book's retrieved set -- and further, blended a natal-Saturn-relative reference table with an ascendant-relative transit question without flagging the difference. A citation that looks individually verifiable (real book, real page, both actually retrieved) but is wrong on inspection is arguably a worse failure mode for an "AI reviewing AI" product than an absent citation, because it's harder for a non-expert user to catch.
- **Q4, the deliberate stress test, failed in the worst available way.** It did not hallucinate a false claim about Moon-in-Aries -- but it also never said the retrieved passages don't address it, as the system prompt explicitly instructed it to do when retrieval doesn't cover the question. Instead it silently substituted an easier, generic, already-supported question for the one asked, and used confident, fluent, plausible-sounding language to do it. This is the one outcome the task explicitly hoped to avoid, and it's the most informative single result in this run: prompting an LLM to "say so explicitly" when retrieval falls short is not sufficient on its own to make it actually notice that retrieval fell short on a *sub-clause* of a compound question, as opposed to the whole question.

**Did specificity track retrieval quality?** Partially, and in the expected direction, but the one place it mattered most is where it broke. Q1-Q3 retrieved relevant on-topic chunks (BPHS/Saravali house-signification text for Q1; Lal Kitab/Deva-keralam Saturn-gains text for Q2; Deva-keralam's own house-by-house transit list for Q3) and produced specific, on-topic answers (R4=Y all three). Q4's retrieval returned the same Deva-keralam p.59/147/153 cluster already seen in the post-delete Saturn-11th retrieval check -- on-topic for "Saturn transit 11th" in general, but *structurally incapable* of covering the Moon-in-Aries clause, since nothing in the 7,743-chunk corpus indexes transit effects by natal Moon sign. Good retrieval of the wrong sub-question produced a confident answer to the wrong sub-question. This is a corpus-coverage gap (matches the Session 22 spike's documented Deva-keralam gap finding), not a retrieval-ranking gap -- no amount of re-ranking the existing chunks would have surfaced Moon-in-Aries-specific content, because none exists in the corpus.

**Anything surprising that warrants follow-up?**
1. **The Q3 mis-paginated citation is the single most important finding in this report.** It shows the citation-instruction compliance the prompt achieves ("cite a source by name and page") is necessary but not sufficient -- the model will confidently produce a citation that passes a naive "is there a page number" check while being factually wrong against the very chunks it was given. Any UI surfacing these citations to an end user needs to treat "model cited X" as no stronger a trust signal than "model said X" until/unless citations are programmatically verified against retrieved chunk content (a *deterministic* check, consistent with CLAUDE.md's NO ANCHORED JUDGMENT principle -- exactly the kind of Python-side verification that should gate citations before display, not another LLM call).
2. **Q4's failure mode (silent sub-clause dropping) is more dangerous than outright hallucination would have been**, because the output is fluent, well-cited (correctly, this time), and internally consistent -- nothing about reading it in isolation would tip off a non-expert reader that half the question was never addressed. A hallucinated specific claim about Moon-in-Aries would at least have been a checkable, falsifiable claim; silent omission dressed as a complete answer is harder to catch.
3. **Voice drift correlates with how far the question pulls the model away from chunk text it can closely paraphrase.** Q1 and Q3 (closest to retrieved phrasing, paraphrasing house-by-house lists) held voice; Q2 and Q4 (more abstract "why" and "what about this specific combination" framing) drifted toward generic-positivity register. This suggests the voice instruction alone is not robust to harder reasoning asks -- worth testing whether a stricter system-prompt constraint (e.g. explicitly forbidding words like "stability," "fulfillment," "favorable outcomes") helps, before concluding the architecture itself is unworkable.

**Net:** path (c) is not ready to ship as tested. The data-layer and retrieval-layer work from this session's earlier checks is sound and uncontaminated by this finding -- this is specifically an answer-generation-layer result. Per the task's explicit instruction, the calculation roadmap stays paused pending review of this report; no prompt tuning or retries have been applied to improve these numbers.

