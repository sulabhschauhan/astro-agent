# Head Line — Reconciliation Audit (book ↔ rules ↔ descriptor)

**Scope:** Line of Head only. Source: Cheiro pp.145–155 (`cheiroslanguageo00chei_1.json`).
Cross-checked against `palm_rules_head_heart_v1.json` (H_001–H_025) and the vision
descriptor's actual head-line output (Athira run 2026-08-07T10:55).
**Method:** enumerate every "when X → means Y" statement in the book, then ask two
questions of each: (1) does a rule exist for it? (2) can the descriptor produce the
token that rule needs? A configuration only produces a reading if all three align.

---

## The three vocabularies (and how far apart they are)

- **Book doctrine** (rich): keys on line *topology* — where it starts (Jupiter / life
  line / Mars), where it ends (which mount), whether it forks/branches, its slope, its
  height relative to the heart line, its continuity, its length.
- **Rule antecedents** (medium): `Starting_Point`, `Position` (high / under-mount /
  terminating-on-mount / running-through-square), `Branching`, `Proximity`,
  `Continuity`, `Length`, `Direction`, `Breadth`, `Depth`.
- **Descriptor tokens** (narrow): only **Depth, Length, Width, Slope, Continuity**.

The descriptor is the bottleneck. It reports how the line *looks* (deep, long, narrow,
sloping, unbroken) but almost nothing about its *topology* (where it starts, ends,
forks). Most rules are built on topology. So most rules can never fire — not for a
lack of the right hand, but because the descriptor never emits the token they need.

---

## Reconciliation table

Status legend: **FIREABLE** (doctrine + rule + descriptor all align) ·
**AUTHORING GAP** (doctrine exists, no rule) · **MISMATCH** (rule exists, descriptor
token mismaps by attribute/value name) · **DEAD RULE** (rule exists, descriptor cannot
produce its token on any hand).

| # | Doctrine (Cheiro) | Page | Rule? | Descriptor can produce token? | Status |
|---|---|---|---|---|---|
| 1 | Straight, clear, even → practical common sense | p146 | H_004 (`Direction=straight`) | Descriptor emits `Slope`, not `Direction` | **MISMATCH** (attribute name) |
| 2 | Slightly sloping (after straight start) → balanced, level-headed | p146 | none | `Slope=downward` ✔ | **AUTHORING GAP** |
| 3 | Whole line slight slope → imaginative leaning (type-dependent) | p146 | none | `Slope=downward` ✔ | **AUTHORING GAP** (hand-type caveat) |
| 4 | Very sloping → romance, idealism, Bohemianism | p146 | none | `Slope` yes, but no *degree* value ("very") | **AUTHORING GAP** + value-granularity |
| 5 | Sloping + fork on Luna → literary imaginative talent | p146 | none | no fork / no mount-termination token | **AUTHORING GAP** + **DEAD** |
| 6 | Rises from life line / connected → caution, sensitivity | p145–146 | H_002 (`Starting_Point=rising_from_Line_of_Life`), H_001 (`Proximity=touching_Line_of_Life`) | "originates close to life line" mismaps to Position/Slope | **MISMATCH** (real claim dropped) |
| 7 | Rises from Mount of Jupiter | p145 | rule exists (`Starting_Point=rising_from_Mount_of_Jupiter`) | no `Starting_Point` token | **DEAD RULE** |
| 8 | Rises from Mount of Mars within life line | p146 | H_003 (`Starting_Point=rising_from_Mount_of_Mars`) | no `Starting_Point` token | **DEAD RULE** |
| 9 | Short → material nature, lacks imagination | p147 | H_005/H_006 (`Length=short`) | `Length` ✔ | **FIREABLE** |
| 10 | Linked/chained → indecision | p147 | H_008 (`Continuity=chained`) | `Continuity` ✔ | **FIREABLE** |
| 11 | Islands/hairlines → brain disease | p147 | H_009/H_012 (`Continuity=islanded`) | `Continuity` ✔ | **FIREABLE** |
| 12 | Broken (both hands) → head injury | p148 | H_011 (`Continuity=broken`) | `Continuity` ✔ | **FIREABLE** but H_011 over-fires (no hand_side, S81) |
| 13 | Broken under Saturn → sudden death | p147 | H_007 (`Continuity=broken` + `Position=under_Mount_of_Saturn`) | no `Position=under_mount` token | **DEAD RULE** (position half) |
| 14 | High (narrow space to heart) → head rules heart | p147 | H_021/H_010 (`Position=high`) | no `Position=high` token | **DEAD RULE** |
| 15 | Turns at end / branch to a mount → partakes of that mount | p147–148 | H_013/H_023/H_024 (`Branching` + `terminating_on_Mount…`) | no branching / termination token | **DEAD RULE** |
| 16 | Double line → brain power | p147 | H_025 (`Branching=doubled`) | no `Branching` token | **DEAD RULE** |
| 17 | Runs through a square → preserved from accident | p148 | H_015 (`Position=running_through_Square`) | no `Position` token | **DEAD RULE** |
| 18 | Head–life space medium → energy/self-confidence; wide → foolhardiness; tightly connected+low → no self-confidence | p148 | none (only touching / rising-from covered) | descriptor gives "close", not space-width | **AUTHORING GAP** |
| 19 | Hairlines branch up to heart → fascination not love | p148 | none | no branching token | **AUTHORING GAP** + **DEAD** |
| 20 | Extremely long + straight to percussion → intellectual power | p146 | none (no long+straight rule) | `Length`+`Slope` ✔ | **AUTHORING GAP** |

---

## The three lists

### A. Authoring gaps — doctrine in the book, no rule (verify + author)
- **Slope meanings (p146)** — the whole slope family: slightly-sloping → balanced/
  level-headed; very sloping → idealism/imagination. **Highest ROI**: this is the one
  place where rich doctrine *and* a descriptor token (`Slope`) both exist and only the
  rule is missing. Hand-type caveat (p145/p150/p151) applies — verifier judgment needed
  on which slope claims are hand-type-independent enough to author cleanly.
- Head–life **space width** (medium/wide/tight) → energy vs foolhardiness vs no
  self-confidence (p148).
- Long + straight to percussion → intellectual power (p146).
- Hairlines to heart → fascination not love (p148) — but descriptor-blocked (see C).

### B. Mismatch bugs — rule exists, descriptor token mismaps (fix mapping)
- **Slope vs Direction** — descriptor emits `Slope=downward`; rules use `Direction`.
  Same disease as Width/Thickness. Reconcile the attribute name (and value: "downward"
  vs "sloping") so slope rules can fire.
- **"originates close to life line" → `Starting_Point=rising_from_Line_of_Life`** —
  H_001/H_002 are real, verified rules being silently missed because the prose mismaps
  to Position/Slope. A genuine caution/sensitivity claim is being dropped.

### C. Dead rules — rule exists, descriptor can never produce its token
Everything keyed on `Starting_Point` (Jupiter/Mars), `Position` (high / under-mount /
terminating-on-mount / running-through-square), and `Branching` (branched/doubled/
fork). ~15 of ~25 head rules. These cannot fire on **any** hand until the descriptor is
widened to report line topology. Authoring more such rules is wasted effort until then.

---

## Headline finding & priority order

**The descriptor is the bottleneck, not the rule book.** The rule book is actually
*ahead* of the descriptor — it has rules for start-points, terminations, and branching
that the descriptor can't feed. So the priorities are:

1. **Fix the Slope↔Direction mismatch + author the slope rules (p146).** One move
   unlocks the single richest head signal the descriptor already captures. Verifier
   judgment on hand-type-clean slope claims.
2. **Fix "close to life line" → rising_from_Line_of_Life mapping.** Recovers H_001/H_002
   (real dropped claims) with no new authoring.
3. **Widen the descriptor to report topology** (start-point, termination mount,
   branching/fork, head–life space, position height). This is the big structural unlock
   — it resurrects ~15 dead rules and is prerequisite to authoring gap #18–#20. Scope as
   its own workstream; it touches the vision prompt + tokenizer, not the rules.
4. Only after (3): author the topology-dependent gaps (space-width, hairlines-to-heart).

**Do NOT** author more topology rules before (3) — they'll be born dead.

---

## Backlog (deferred, per this session)
- Heart line — same reconciliation, next pass.
- Sweep all other authored chapters (Fate/Sun/Health/Marriage/Mounts/Thumb/Fingers) in
  one batch once head+heart are done.
