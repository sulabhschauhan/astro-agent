# Cheirognomy — Hand-Type Rubric & Finger-Forward Capture Schema

Source: Cheiro, *Language of the Hand*, Ch. I–XI. Page references are load-bearing — keep them.

## 1. Purpose & fidelity stance

- Cheirognomy rubric for hand-type classification plus the per-finger capture schema.
- Type is a **DISCLOSED, user-correctable ASSUMPTION**, never a silent input.
- No type-labeled palm dataset exists. Validation = a small self-labeled **consistency** set,
  **NOT a truth oracle** (fidelity-not-truth ceiling).
- The **modifier layer** (type reweighting other lines) is **NOT built** and is out of scope here.

## 2. The 7 types — closed menu, geometric criteria (verbatim from source)

| Type | Palm | Fingertips | Fingers/length | Joints | Nails | src |
|---|---|---|---|---|---|---|
| Elementary | large, thick, heavy | — | short, clumsy | — | short | p51 |
| Square | square at wrist + at finger-base | square | square | — | short/square | p52 |
| Spatulate | broad at wrist OR at finger-base (asymmetric) | spatula-flared/flattened | — | — | — | p58 |
| Philosophic | long, angular | — | bony | knotty/developed | long | p62 |
| Conic | medium, slightly tapering | conic/slightly pointed | full at base | smooth | rather long | p69 |
| Psychic | long, narrow | pointed (extreme) | extremely long, tapering | smooth | — | p72 |
| Mixed | different types on one hand / "cannot be classified" | — | — | — | — | p48 (FALLBACK ONLY) |

**Notes:**

- Spatulate sub-signal — broad-at-wrist → palm points to fingers; broad-at-base → slopes to
  wrist (capture as a secondary field).
- Conic ↔ psychic is a **proportion continuum**, not a clean boundary — expect most confusion there.
- Mixed = assigned only when **no single type dominates**.

## 3. Arm split — which arm reads what

- **MediaPipe (objective/deterministic):** finger-length-vs-palm ratio, palm width at-wrist vs
  at-base, overall long-narrow vs broad, inter-finger spacing.
- **VLM only (contour judgment, error-prone → confidence-flag):** fingertip form
  `{square, conic, spatulate, pointed, knotty}`, joint knottiness, nail length.
- **5 discriminating primitives:** `fingertip_form`, `palm_squareness`/`broad_point`,
  `finger_palm_ratio`, `joint_knottiness`, `nail_length`.

## 4. Capture schema (canonical shape)

Per-finger record **KEYED BY IDENTITY** (`jupiter` = 1st/index, `saturn` = 2nd/middle,
`apollo` = 3rd/ring, `mercury` = 4th/little). **THUMB and NAILS excluded** — own chapters
(Ch. IX / Ch. XIII); nails scoped out.

Populate `fingertip_form` **NOW**; all other per-finger fields are **RESERVED (null)** for the
future Fingers chapter (Ch. X/XI) — reserving them now avoids a schema migration later.

```json
{
  "hand_geometry": {
    "palm_squareness": null,
    "broad_point": null,
    "finger_palm_ratio": null,
    "overall_proportion": null,
    "inter_finger_spacing": {"1_2": null, "2_3": null, "3_4": null}
  },
  "fingers": {
    "jupiter": {"fingertip_form": null, "_reserved": {"length_abs": null, "length_relative": null, "thickness": null, "lean": null, "straightness": null, "flexibility": null, "base_shape": null, "phalanges": [null, null, null], "joints": {"upper": null, "lower": null}}},
    "saturn": {"fingertip_form": null, "_reserved": {"length_abs": null, "length_relative": null, "thickness": null, "lean": null, "straightness": null, "flexibility": null, "base_shape": null, "phalanges": [null, null, null], "joints": {"upper": null, "lower": null}}},
    "apollo": {"fingertip_form": null, "_reserved": {"length_abs": null, "length_relative": null, "thickness": null, "lean": null, "straightness": null, "flexibility": null, "base_shape": null, "phalanges": [null, null, null], "joints": {"upper": null, "lower": null}}},
    "mercury": {"fingertip_form": null, "_reserved": {"length_abs": null, "length_relative": null, "thickness": null, "lean": null, "straightness": null, "flexibility": null, "base_shape": null, "phalanges": [null, null, null], "joints": {"upper": null, "lower": null}}}
  },
  "_provenance": "every populated primitive carries {value, source_arm, confidence}"
}
```

Field annotations (kept out of the JSON so the block parses):

- `hand_geometry` — MediaPipe, objective.
- `hand_geometry.broad_point` — `{wrist, base}`; the spatulate sub-signal.
- `hand_geometry.inter_finger_spacing` — CAPTURED now, dual-use.
- **MULTI-VALUE slots** — `multi: palm, finger_character`. These two §2 columns tangle
  INDEPENDENT axes: a palm can be thick AND broad at once, and finger character is not one
  scale. So each holds a LIST of applicable §2 menu values rather than a single winner.
  Every other slot stays single-valued. A type's §2 criterion for a multi slot fires when
  ANY observed value equals it (OR-match). The menu WORDS are unchanged — this annotation
  changes cardinality only, never vocabulary.

## 5. Derive + disclose (deterministic, on top of capture)

Output: `{dominant_type, modifiers[], confidence, quality_flag, disclosed_assumption_text}`.

Per-finger primitives are **captured**; the WHOLE-HAND label is **DERIVED**, never captured
directly — "mixed" therefore means **"fingers disagree"**, a principled result, not a shrug.

## 6. Reconciliation rule (non-negotiable)

When MediaPipe and VLM disagree (e.g. VLM = conic tips, geometry = square proportions): do **NOT**
pick a silent winner. Lower `confidence`, set `quality_flag`, lean toward mixed/uncertain, and
surface the disagreement in `disclosed_assumption_text`.

Reference-arm doctrine: **disagreement → a flag, not a forced call.**

## 7. Capture pose (from Cheiro p95–96 + engineering)

Two shots:

- **(a) fingers naturally at rest** — spread IS a signal (tight = cautious/reserved,
  wide = independent, Cheiro p96).
- **(b) fingers extended + slightly separated, palm flat** — the MEASUREMENT pose (tips must be
  apart for fingertip form + clean MediaPipe tips).

Palmar + dorsal ideal.

## 8. Reserved-but-not-built (forward-compat, do not implement)

`skin_texture`, `hand_flexibility` (whole-hand), `hand_color`, `mount_fullness`.

## 9. Resources

- **yeonsumia/palmistry** (github) — MediaPipe-based principal-LINE detection + view-invariant
  rectification/warping. NOT type classification, but a useful reference if landmark/geometry
  work stalls later.
