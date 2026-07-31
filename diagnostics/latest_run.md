Pulled all three from the authoritative record (SESSION_LOG + S81 diagnostics). One important caveat up front: there is no single clean "layer table" artifact file — the S81 rank tables that live in diagnostics/cheiro_retrieval_baseline_S81.md are the b1f7a79 ones, which S81's own retractions marked VOID (they conflated "absent from top-10" with "missing from corpus"). The valid layer assignment is the verdict distributed across the S81 log, built on the b51049e-onward numbers. So below is that verdict reassembled from the non-void source — not the void tables.

1. The S81 layer table (valid, b51049e-based)

Feature	Layer	Evidence (valid ranks)	Fix / status
fate line	RETRIEVAL	correct doctrine buried by cross-chapter near-misses — p163_c1 rank 3, p165_c2 rank 14; adjacent-rank gaps 0.016–0.034, no cliff	page-range filter (shipped S82). Corpus repair fixes it NOT
head line	PROMPT	retrieval delivers correct doctrine post-filter; defect is the S71 valence bug — neutral "strength OR weakness" labelled valence="supports"	belongs to S71 arc, still open (re-confirmed live S83). No retrieval work fixes it
heart line	RETRIEVAL	p159_c2 rank 5, p160_c1 rank 6, p160_c3 >20 — buried past the n=3 gate	S83 re-confirmed: correct doctrine at ranks 4–8, sliced by cutoff. Window-widen (parked)
p123_c0 nomenclature	DATA	attractor — rank 1 head, rank 7 heart (table-of-names)	contained by the gate; no live leak (S82/S83)
corpus repair (Path D)	DATA	—	fixes NEITHER fate nor head; palm corpus exonerated (all target chunks exist, zero empty text pages across doctrine range p133–182; the 9 empties are all diagram plates)

The one-line summary the log itself uses: fate → RETRIEVAL, head → PROMPT, corpus repair fixes neither.

2. Where the U-ladder stands

Completed: U0, U0.5, U0.6, U1, U1b, U1c (all in the S80 commit set, HEAD d2623ff). Those are the corruption-census / span-mapping / paragraph-recovery diagnostics.

U4 has not been reached, let alone passed. U4 is the hard gate: "IF RETRIEVAL DOES NOT IMPROVE AT U4, PATH D IS WRONG AND WE STOP." At this session's open I checked and the U4 pre-fix baseline never landed — S82 measured the palm page-range gate, which is a different question from the Path D chunking A/B that U4 is defined against. So everything Path-D is still gated behind U4, and by extension so are the two things queued after it (R2-threshold and E-3, both explicitly "post-U4").

The consequential shift, though: S81 exonerated palm ("Path D is not required for palm"). So the U-ladder / Path D is no longer a palm concern at all — its only remaining justification is the astrology corpus (the F4-damaged Phaladeepika/Saravali) and Hasta re-sourcing. U4 is an astrology-track gate now, not a palm one.

3. The quote-anchored E-3 design note

Recorded in the S79 rulings (SESSION_LOG), queued post-U4, in this order:

Quote-anchored extraction — Stage 1 emits a verbatim evidence_quote; the gate checks that span as a normalized substring; claim_text paraphrases freely. This retires the "Medium" vs "Medium relative" class with no threshold at all.
Then NLI entailment with a polarity check.
Explicitly not embedding cosine — cosine is topicality and would pass both p145_c0 and p139_c0 (i.e. it can't tell support from mere same-topic).

Context around it (the R2 split it sits inside): R2-structural (bigram needle not bare substring, a low_visibility third state in _is_absence, deterministic doctrinal-lexicon expansion — not HyDE, propagate validate_palm_image.quality into Stage 1) runs parallel with U0–U2 and is text-quality-independent; R2-threshold (the 0.30 floor re-derivation + NLI calibration) waits for U4; E-3 is the extraction-contract replacement queued after that.

Two honest flags on this so you brainstorm from solid ground: the E-3 note is a design intent recorded at S79 — I found no evidence any of it is built (it's all post-U4, and U4 isn't reached). And the polarity point is the crux worth dwelling on — it's the same failure the head-line valence bug is a live instance of: distinguishing "supports" from "same-topic-but-neutral-or-opposite" is exactly what cosine can't do and what E-3's quote-anchor + polarity check is meant to fix. So E-3 and the still-open S71 head-line defect are the same problem at two scales.