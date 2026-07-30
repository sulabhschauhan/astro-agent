# S82 Prompt 4 — Live Cheiro Feature Page-Range Census

Diagnostics only. Reports numbers; makes no range-change recommendation. Threshold cited: `_N_RESULTS_PER_FEATURE` (imported, currently 3) -- the production per-feature retrieval gate. Scope: palm-feature retrieval, Cheiro book only.

## Step 1 — page_ref metadata type check

- First 5 page_ref values (type, value): [('int', 1), ('int', 1), ('int', 1), ('int', 7), ('int', 7)]
- Result: page_ref is `int` (example: 1). Proceeding.

## Step 2 — per-feature census (production `_build_where` clause)

| feature | range | chunk count | distinct page_refs present | pages in range with zero chunks |
|---|---|---|---|---|
| life line | 133-139 | 23 | [133, 134, 135, 136, 137, 138, 139] | [] |
| head line | 145-155 | 30 | [145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155] | [] |
| heart line | 156-161 | 12 | [156, 159, 160, 161] | [157, 158] |
| fate line | 162-165 | 14 | [162, 163, 164, 165] | [] |
| sun line | 166-170 | 8 | [166, 169, 170] | [167, 168] |
| thumb | 85-92 | 14 | [85, 86, 87, 88, 89, 90] | [91, 92] |
| fingers | 93-97 | 11 | [93, 94, 95, 96, 97] | [] |
| mount of venus | 111-113 | 7 | [111, 112, 113] | [] |
| mount of jupiter | 111-113 | 7 | [111, 112, 113] | [] |

## Step 3 — direct id lookup for the six named chunks

Note: these six were reconciled against the PRE-correction 85-94/95-97 thumb/fingers split. A mismatch on thumb/fingers range containment is expected and is not a defect.

| chunk_id | found | page_ref | containing feature range(s) |
|---|---|---|---|
| cheiroslanguageo00chei_1_p165_c2 | yes | 165 | fate line (162-165) |
| cheiroslanguageo00chei_1_p163_c1 | yes | 163 | fate line (162-165) |
| cheiroslanguageo00chei_1_p145_c0 | yes | 145 | head line (145-155) |
| cheiroslanguageo00chei_1_p160_c3 | yes | 160 | heart line (156-161) |
| cheiroslanguageo00chei_1_p159_c2 | yes | 159 | heart line (156-161) |
| cheiroslanguageo00chei_1_p160_c1 | yes | 160 | heart line (156-161) |

## Step 4 — blocking / thin features (report only, no fix proposed)

- Blocking (0 chunks): none
- Thin (1-2 chunks, < _N_RESULTS_PER_FEATURE=3): none

## Decision-branch placement

**Branch: viable, full width.** Every non-null range holds >= 3 chunks. The flag flip is viable.

## Failures

Total failures during this census: **0**