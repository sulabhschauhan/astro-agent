# Latest Run: collision_scan -- LLM-selector confusion candidates

Rules scanned (validated_candidates): 47
Collision pairs found: 19

Distinct rules involved in >=1 collision (candidates for a hard-prerequisite tag): 23
Rule ids: ['HL_004', 'HL_005', 'HL_006', 'HL_007', 'HL_008', 'HL_009', 'HL_010', 'HL_011', 'HL_013', 'HL_018', 'HL_020', 'HL_021', 'H_002', 'H_004', 'H_007', 'H_010a', 'H_010b', 'H_011', 'H_013', 'H_020', 'H_023', 'H_024', 'H_027']

## Method

- Shared token: literal (feature, attribute, value) per antecedent, PLUS a normalized (feature, ORIGIN_AT, target) token bridging Starting_Point='rising_from_X' and Proximity='touching' with relation_target=X (the exact H_027/H_002 vocabulary split -- see module docstring). No other equivalences are invented.

- Hard discriminator: literal (attribute, value_or_target) for Starting_Point / Position / Presence antecedents only (per task spec), no normalization.

- Flagged iff shared-token sets intersect AND discriminator-token sets differ (symmetric difference non-empty). All pairs across the full corpus are scanned, not just within-topic_group.

## Collision pairs

| rule_a | rule_b | shared | discriminator | gloss |
|---|---|---|---|---|
| HL_004 | HL_005 | Line of Heart touches/originates at Mount of Saturn; Line of Heart.Starting_Point=rising_from_Mount_of_Saturn | Position=high | HL_004 and HL_005 both key on [Line of Heart touches/originates at Mount of Saturn; Line of Heart.Starting_Point=rising_from_Mount_of_Saturn], but differ on [Position=high] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_005 | HL_006 | Line of Heart.Position=high | Starting_Point=rising_from_Mount_of_Saturn | HL_005 and HL_006 both key on [Line of Heart.Position=high], but differ on [Starting_Point=rising_from_Mount_of_Saturn] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_005 | HL_011 | Line of Heart.Position=high | Starting_Point=rising_from_Mount_of_Saturn | HL_005 and HL_011 both key on [Line of Heart.Position=high], but differ on [Starting_Point=rising_from_Mount_of_Saturn] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_005 | HL_018 | Line of Heart touches/originates at Mount of Saturn; Line of Heart.Starting_Point=rising_from_Mount_of_Saturn | Position=high | HL_005 and HL_018 both key on [Line of Heart touches/originates at Mount of Saturn; Line of Heart.Starting_Point=rising_from_Mount_of_Saturn], but differ on [Position=high] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_006 | HL_021 | Quadrangle.Breadth=narrow | Position=high; Position=low | HL_006 and HL_021 both key on [Quadrangle.Breadth=narrow], but differ on [Position=high; Position=low] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_007 | HL_008 | Line of Heart.Continuity=broken | Position=under_Mount_of_Saturn; Position=under_Mount_of_Sun | HL_007 and HL_008 both key on [Line of Heart.Continuity=broken], but differ on [Position=under_Mount_of_Saturn; Position=under_Mount_of_Sun] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_007 | HL_009 | Line of Heart.Continuity=broken | Position=under_Mount_of_Mercury; Position=under_Mount_of_Saturn | HL_007 and HL_009 both key on [Line of Heart.Continuity=broken], but differ on [Position=under_Mount_of_Mercury; Position=under_Mount_of_Saturn] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_008 | HL_009 | Line of Heart.Continuity=broken | Position=under_Mount_of_Mercury; Position=under_Mount_of_Sun | HL_008 and HL_009 both key on [Line of Heart.Continuity=broken], but differ on [Position=under_Mount_of_Mercury; Position=under_Mount_of_Sun] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_010 | HL_013 | Line of Heart.Continuity=forked | Starting_Point=rising_from_Mount_of_Jupiter | HL_010 and HL_013 both key on [Line of Heart.Continuity=forked], but differ on [Starting_Point=rising_from_Mount_of_Jupiter] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_013 | HL_018 | Line of Heart.Width=wide | Starting_Point=rising_from_Mount_of_Saturn | HL_013 and HL_018 both key on [Line of Heart.Width=wide], but differ on [Starting_Point=rising_from_Mount_of_Saturn] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| HL_018 | HL_020 | Line of Heart.Width=wide | Starting_Point=rising_from_Mount_of_Saturn | HL_018 and HL_020 both key on [Line of Heart.Width=wide], but differ on [Starting_Point=rising_from_Mount_of_Saturn] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| H_002 | H_027 | Line of Head touches/originates at Line of Life | Starting_Point=->Mount of Jupiter; Starting_Point=rising_from_Line_of_Life | H_002 and H_027 both key on [Line of Head touches/originates at Line of Life], but differ on [Starting_Point=->Mount of Jupiter; Starting_Point=rising_from_Line_of_Life] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| H_004 | H_020 | Line of Head.Direction=straight | Position=high | H_004 and H_020 both key on [Line of Head.Direction=straight], but differ on [Position=high] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| H_007 | H_011 | Line of Head.Continuity=broken | Position=under_Mount_of_Saturn | H_007 and H_011 both key on [Line of Head.Continuity=broken], but differ on [Position=under_Mount_of_Saturn] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| H_010a | HL_021 | Quadrangle.Breadth=narrow | Position=high; Position=low | H_010a and HL_021 both key on [Quadrangle.Breadth=narrow], but differ on [Position=high; Position=low] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| H_010b | HL_021 | Quadrangle.Breadth=narrow | Position=high; Position=low | H_010b and HL_021 both key on [Quadrangle.Breadth=narrow], but differ on [Position=high; Position=low] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| H_013 | H_023 | Line of Head.Branching=branched | Position=terminating_on_Mount; Position=terminating_on_Mount_of_Jupiter | H_013 and H_023 both key on [Line of Head.Branching=branched], but differ on [Position=terminating_on_Mount; Position=terminating_on_Mount_of_Jupiter] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| H_013 | H_024 | Line of Head.Branching=branched | Position=terminating_on_Mount_of_Jupiter; Position=terminating_on_Mount_of_Moon | H_013 and H_024 both key on [Line of Head.Branching=branched], but differ on [Position=terminating_on_Mount_of_Jupiter; Position=terminating_on_Mount_of_Moon] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
| H_023 | H_024 | Line of Head.Branching=branched | Position=terminating_on_Mount; Position=terminating_on_Mount_of_Moon | H_023 and H_024 both key on [Line of Head.Branching=branched], but differ on [Position=terminating_on_Mount; Position=terminating_on_Mount_of_Moon] -- an LLM given both could fire the wrong one for a hand missing the discriminator. |
