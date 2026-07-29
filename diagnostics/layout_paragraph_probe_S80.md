# LAYOUT-BASED PARAGRAPH RECOVERY PROBE — S80 U1c — Cheiro only

Read-only, diagnostics-only. No repair, no boundary-seeder logic, no ChromaDB writes, no re-ingestion. Method: `page.extract_text_lines()` (NOT `extract_words()` directly — see module docstring for why). See scripts/layout_paragraph_probe_S80.py for full reuse/method detail.

## Line-grouping tolerance derivation

Sampled 3 clean pages (page_index [155, 99, 213]) via `extract_words()`. Observed same-line word-to-word `top` delta ceiling: **1.566pt**. Observed smallest cross-line gap: **13.920pt**. Derived tolerance: **3.0pt** (margin above same-line ceiling: 1.434pt; margin below cross-line floor: 10.920pt).

| page_index | word_count | extract_text_lines() line count |
|---|---|---|
| 155 | 323 | 30 |
| 99 | 287 | 27 |
| 213 | 323 | 26 |

---

## Self-checks

| Assertion | Expected | Observed | Status |
|---|---|---|---|
| Cheiro page count == 310 | 310 | 310 | PASS |
| Cheiro p157 native contains "Plate XVIII" | present | present | PASS |
| Cheiro p158 native char_count == 0 | 0 | 0 | PASS |
| Cheiro p156 native contains "CHAPTER X" | present | present | PASS |
| Cheiro p156 live chunk count == 3 | 3 | 3 | PASS |

---

## Cohort membership

- A (14 overlap pages): [13, 19, 20, 39, 68, 135, 146, 150, 155, 187, 214, 216, 219, 302]
- B (page 125, worst coverage): [124]
- C (5 highest-native_char_count zero-chunk pages): [2, 190, 307, 308, 1]
- D (4 anchor pages, page_index): [138, 144, 158, 162]
- E (3 control pages, highest coverage): [10, 12, 14]

No page appears in more than one cohort group — confirmed, not assumed.

---

## PROVISIONAL, NOT RATIFIED indent cut: 14.0pt

Derived from the histogram below: the first empty 2pt bucket after the zero-cluster, confirmed to have real occupied buckets beyond it (i.e. a genuine gap between two clusters, not just the distribution's tail). **This cut is provisional and used only to produce the numbers in this report — it is not a ratified threshold.**

---

## (a) GATE NUMBER — agreement on control (E) + anchor (D) pages

Each detected opening's first 1-3 words are located as a literal subsequence inside the SAME page's `census._tokenize(extract_text())` native-token list (both extractions read the same underlying PDF text objects, just grouped differently), giving a native-token index directly comparable to U1's `span_start` values.

| page_index | cohort | detected openings | existing chunk count | existing span_starts | within 5 native tokens of a span_start |
|---|---|---|---|---|---|
| 10 | E | 4 | 3 | [0, 137, 257] | 3 |
| 12 | E | 8 | 3 | [0, 212, 347] | 3 |
| 14 | E | 1 | 2 | [0, 139] | 1 |
| 138 | D | 5 | 3 | [0, 110, 369] | 3 |
| 144 | D | 10 | 3 | [0, 142, 268] | 2 |
| 158 | D | 6 | 4 | [0, 120, 271, 381] | 3 |
| 162 | D | 11 | 4 | [0, 145, 280, 403] | 4 |

**GATE NUMBER: 19 / 45 detected openings on the 3 control + 4 anchor pages fall within 5 native tokens of an existing chunk span_start.**

<details><summary>Per-opening detail (click to expand)</summary>

| page_index | opening text (first 60 chars) | native_index | within_5_tokens |
|---|---|---|---|
| 10 | To believe is to perceive—either by the senses or the soul.  | 1 | True |
| 10 | In placing the following work before the public, though deep | 67 | False |
| 10 | A trifle is concealed immensity—the atom is equal to the who | 137 | True |
| 10 | In the accompanying Defense of Cheiromancy I have endeavored | 257 | True |
| 12 | vn | 1 | True |
| 12 | Nothing has been more removed from my thoughts than the inte | 97 | False |
| 12 | In conclusion, I wish to say that, in my present tour round  | 212 | True |
| 12 | Cheiro. | 261 | False |
| 12 | The first edition of five thousand copies having been exhaus | 264 | False |
| 12 | In revising it and producing a second edition, I have endeav | 297 | False |
| 12 | The hand of Austin Chamberlain has been placed next to that  | 347 | True |
| 12 | Cheiro. | 394 | False |
| 14 | page | 1 | True |
| 138 | The Line of Life. 85 | 0 | True |
| 138 | When the line of life sweeps far out into the hand, thus all | 77 | False |
| 138 | When, on the contrary, it lies very close to the Mount of Ve | 110 | True |
| 138 | That the line of life does not always show the exact age at  | 143 | False |
| 138 | In addition to the information I have given here concerning  | 369 | True |
| 144 | “ To know is power”—let ustlien be wise, | 6 | False |
| 144 | And use our brains with every good intent, | 14 | False |
| 144 | That at the end we come with tired eyes | 22 | False |
| 144 | And give to Nature more than what she lent. | 31 | False |
| 144 | Cheiro. | 40 | False |
| 144 | The line of head (Plate XIII.) relates principally to the me | 41 | False |
| 144 | It is of extreme importance in connection with this line tha | 79 | False |
| 144 | The line of head can rise from three different points—from t | 142 | True |
| 144 | Rising from Jupiter (c-c, Plate XX.) and yet touching the li | 178 | False |
| 144 | There is a variation of this which is almost equally strong. | 268 | True |
| 158 | The Line of Heart. 99 | 0 | True |
| 158 | The line rising between the first and second fingers gives a | 120 | True |
| 158 | With the line of heart rising from Saturn, the subject will  | 170 | False |
| 158 | When the line of heart is itself in excess, namely, lying ri | 271 | True |
| 158 | When the line of heart is much fretted by a crowd of little  | 330 | False |
| 158 | A line of heart from Saturn, chained and broad, gives an utt | 362 | False |
| 162 | . | None | False |
| 162 | The Line of Fate 103 | 0 | True |
| 162 | The strange and mysterious thing to note is that the possess | 28 | False |
| 162 | Before the student goes farther I would recommend him, once  | 75 | False |
| 162 | The line of fate, properly speaking, relates to all worldly  | 98 | False |
| 162 | The line of fate may rise from the line of life, the wrist,  | 145 | True |
| 162 | If the fate-line rise from the line of life and from that po | 172 | False |
| 162 | When the line of fate rises from the wrist and proceeds stra | 247 | False |
| 162 | Rising from the Mount of Luna, fate and success will be more | 280 | True |
| 162 | If the line of fate be straight and a branch run in and join | 314 | False |
| 162 | If the line of fate in its course to the Mount of Saturn sen | 403 | True |

</details>

Agreement on pages already believed correct (control + anchor) is the only thing that validates the method — a low agreement rate here would mean the layout signal does not reliably locate the SAME boundaries this project's existing chunking already got right, independent of whether those existing boundaries are themselves complete.

---

## (b) Indent distribution across the cohort

n = 944, min = -498.64, p25 = -0.44, median = 0.28, p75 = 29.72, max = 519.84

| Bucket (pt) | Count |
|---|---|
| -500--498 | 1 |
| -498--496 | 1 |
| -496--494 | 0 |
| -494--492 | 0 |
| -492--490 | 0 |
| -490--488 | 0 |
| -488--486 | 0 |
| -486--484 | 0 |
| -484--482 | 0 |
| -482--480 | 0 |
| -480--478 | 0 |
| -478--476 | 0 |
| -476--474 | 0 |
| -474--472 | 0 |
| -472--470 | 0 |
| -470--468 | 0 |
| -468--466 | 0 |
| -466--464 | 0 |
| -464--462 | 0 |
| -462--460 | 0 |
| -460--458 | 0 |
| -458--456 | 0 |
| -456--454 | 0 |
| -454--452 | 0 |
| -452--450 | 0 |
| -450--448 | 0 |
| -448--446 | 0 |
| -446--444 | 0 |
| -444--442 | 0 |
| -442--440 | 0 |
| -440--438 | 0 |
| -438--436 | 0 |
| -436--434 | 0 |
| -434--432 | 0 |
| -432--430 | 0 |
| -430--428 | 0 |
| -428--426 | 0 |
| -426--424 | 0 |
| -424--422 | 0 |
| -422--420 | 0 |
| -420--418 | 0 |
| -418--416 | 1 |
| -416--414 | 0 |
| -414--412 | 0 |
| -412--410 | 0 |
| -410--408 | 0 |
| -408--406 | 1 |
| -406--404 | 0 |
| -404--402 | 0 |
| -402--400 | 0 |
| -400--398 | 0 |
| -398--396 | 0 |
| -396--394 | 0 |
| -394--392 | 0 |
| -392--390 | 0 |
| -390--388 | 0 |
| -388--386 | 0 |
| -386--384 | 0 |
| -384--382 | 0 |
| -382--380 | 0 |
| -380--378 | 0 |
| -378--376 | 0 |
| -376--374 | 0 |
| -374--372 | 0 |
| -372--370 | 0 |
| -370--368 | 0 |
| -368--366 | 0 |
| -366--364 | 0 |
| -364--362 | 0 |
| -362--360 | 0 |
| -360--358 | 0 |
| -358--356 | 0 |
| -356--354 | 0 |
| -354--352 | 0 |
| -352--350 | 0 |
| -350--348 | 0 |
| -348--346 | 0 |
| -346--344 | 0 |
| -344--342 | 0 |
| -342--340 | 0 |
| -340--338 | 0 |
| -338--336 | 1 |
| -336--334 | 0 |
| -334--332 | 0 |
| -332--330 | 0 |
| -330--328 | 0 |
| -328--326 | 0 |
| -326--324 | 0 |
| -324--322 | 0 |
| -322--320 | 0 |
| -320--318 | 0 |
| -318--316 | 0 |
| -316--314 | 0 |
| -314--312 | 0 |
| -312--310 | 0 |
| -310--308 | 0 |
| -308--306 | 0 |
| -306--304 | 0 |
| -304--302 | 0 |
| -302--300 | 0 |
| -300--298 | 0 |
| -298--296 | 0 |
| -296--294 | 0 |
| -294--292 | 0 |
| -292--290 | 0 |
| -290--288 | 0 |
| -288--286 | 0 |
| -286--284 | 0 |
| -284--282 | 0 |
| -282--280 | 0 |
| -280--278 | 0 |
| -278--276 | 0 |
| -276--274 | 0 |
| -274--272 | 0 |
| -272--270 | 0 |
| -270--268 | 0 |
| -268--266 | 0 |
| -266--264 | 0 |
| -264--262 | 0 |
| -262--260 | 0 |
| -260--258 | 0 |
| -258--256 | 0 |
| -256--254 | 0 |
| -254--252 | 0 |
| -252--250 | 0 |
| -250--248 | 0 |
| -248--246 | 0 |
| -246--244 | 0 |
| -244--242 | 0 |
| -242--240 | 0 |
| -240--238 | 0 |
| -238--236 | 0 |
| -236--234 | 0 |
| -234--232 | 0 |
| -232--230 | 0 |
| -230--228 | 0 |
| -228--226 | 0 |
| -226--224 | 0 |
| -224--222 | 0 |
| -222--220 | 0 |
| -220--218 | 0 |
| -218--216 | 0 |
| -216--214 | 0 |
| -214--212 | 2 |
| -212--210 | 0 |
| -210--208 | 0 |
| -208--206 | 0 |
| -206--204 | 0 |
| -204--202 | 0 |
| -202--200 | 0 |
| -200--198 | 0 |
| -198--196 | 0 |
| -196--194 | 0 |
| -194--192 | 0 |
| -192--190 | 0 |
| -190--188 | 0 |
| -188--186 | 0 |
| -186--184 | 0 |
| -184--182 | 0 |
| -182--180 | 0 |
| -180--178 | 0 |
| -178--176 | 0 |
| -176--174 | 0 |
| -174--172 | 0 |
| -172--170 | 0 |
| -170--168 | 0 |
| -168--166 | 0 |
| -166--164 | 0 |
| -164--162 | 0 |
| -162--160 | 0 |
| -160--158 | 0 |
| -158--156 | 0 |
| -156--154 | 0 |
| -154--152 | 0 |
| -152--150 | 0 |
| -150--148 | 0 |
| -148--146 | 0 |
| -146--144 | 0 |
| -144--142 | 0 |
| -142--140 | 0 |
| -140--138 | 2 |
| -138--136 | 4 |
| -136--134 | 2 |
| -134--132 | 1 |
| -132--130 | 0 |
| -130--128 | 0 |
| -128--126 | 0 |
| -126--124 | 0 |
| -124--122 | 0 |
| -122--120 | 0 |
| -120--118 | 0 |
| -118--116 | 0 |
| -116--114 | 1 |
| -114--112 | 3 |
| -112--110 | 2 |
| -110--108 | 2 |
| -108--106 | 4 |
| -106--104 | 1 |
| -104--102 | 4 |
| -102--100 | 3 |
| -100--98 | 6 |
| -98--96 | 3 |
| -96--94 | 5 |
| -94--92 | 3 |
| -92--90 | 1 |
| -90--88 | 6 |
| -88--86 | 1 |
| -86--84 | 1 |
| -84--82 | 2 |
| -82--80 | 1 |
| -80--78 | 0 |
| -78--76 | 1 |
| -76--74 | 0 |
| -74--72 | 0 |
| -72--70 | 1 |
| -70--68 | 0 |
| -68--66 | 0 |
| -66--64 | 0 |
| -64--62 | 0 |
| -62--60 | 0 |
| -60--58 | 0 |
| -58--56 | 0 |
| -56--54 | 0 |
| -54--52 | 0 |
| -52--50 | 0 |
| -50--48 | 0 |
| -48--46 | 0 |
| -46--44 | 0 |
| -44--42 | 0 |
| -42--40 | 0 |
| -40--38 | 0 |
| -38--36 | 1 |
| -36--34 | 2 |
| -34--32 | 0 |
| -32--30 | 0 |
| -30--28 | 0 |
| -28--26 | 0 |
| -26--24 | 0 |
| -24--22 | 0 |
| -22--20 | 0 |
| -20--18 | 0 |
| -18--16 | 0 |
| -16--14 | 0 |
| -14--12 | 0 |
| -12--10 | 1 |
| -10--8 | 1 |
| -8--6 | 1 |
| -6--4 | 0 |
| -4--2 | 23 |
| -2-0 | 257 |
| 0-2 | 210 |
| 2-4 | 17 |
| 4-6 | 11 |
| 6-8 | 5 |
| 8-10 | 7 |
| 10-12 | 5 |
| 12-14 | 2 |
| 14-16 | 0 |
| 16-18 | 5 |
| 18-20 | 3 |
| 20-22 | 4 |
| 22-24 | 8 |
| 24-26 | 7 |
| 26-28 | 14 |
| 28-30 | 62 |
| 30-32 | 11 |
| 32-34 | 8 |
| 34-36 | 5 |
| 36-38 | 2 |
| 38-40 | 2 |
| 40-42 | 6 |
| 42-44 | 3 |
| 44-46 | 0 |
| 46-48 | 2 |
| 48-50 | 2 |
| 50-52 | 2 |
| 52-54 | 2 |
| 54-56 | 0 |
| 56-58 | 0 |
| 58-60 | 3 |
| 60-62 | 1 |
| 62-64 | 1 |
| 64-66 | 3 |
| 66-68 | 0 |
| 68-70 | 2 |
| 70-72 | 1 |
| 72-74 | 2 |
| 74-76 | 2 |
| 76-78 | 1 |
| 78-80 | 0 |
| 80-82 | 0 |
| 82-84 | 3 |
| 84-86 | 2 |
| 86-88 | 0 |
| 88-90 | 1 |
| 90-92 | 2 |
| 92-94 | 0 |
| 94-96 | 1 |
| 96-98 | 2 |
| 98-100 | 3 |
| 100-102 | 1 |
| 102-104 | 2 |
| 104-106 | 2 |
| 106-108 | 1 |
| 108-110 | 4 |
| 110-112 | 2 |
| 112-114 | 0 |
| 114-116 | 1 |
| 116-118 | 1 |
| 118-120 | 1 |
| 120-122 | 0 |
| 122-124 | 3 |
| 124-126 | 3 |
| 126-128 | 1 |
| 128-130 | 0 |
| 130-132 | 1 |
| 132-134 | 0 |
| 134-136 | 4 |
| 136-138 | 0 |
| 138-140 | 4 |
| 140-142 | 0 |
| 142-144 | 0 |
| 144-146 | 2 |
| 146-148 | 0 |
| 148-150 | 3 |
| 150-152 | 3 |
| 152-154 | 3 |
| 154-156 | 1 |
| 156-158 | 0 |
| 158-160 | 0 |
| 160-162 | 2 |
| 162-164 | 0 |
| 164-166 | 1 |
| 166-168 | 3 |
| 168-170 | 0 |
| 170-172 | 1 |
| 172-174 | 1 |
| 174-176 | 2 |
| 176-178 | 2 |
| 178-180 | 0 |
| 180-182 | 1 |
| 182-184 | 0 |
| 184-186 | 0 |
| 186-188 | 0 |
| 188-190 | 0 |
| 190-192 | 1 |
| 192-194 | 1 |
| 194-196 | 0 |
| 196-198 | 2 |
| 198-200 | 1 |
| 200-202 | 2 |
| 202-204 | 1 |
| 204-206 | 0 |
| 206-208 | 0 |
| 208-210 | 0 |
| 210-212 | 1 |
| 212-214 | 0 |
| 214-216 | 0 |
| 216-218 | 0 |
| 218-220 | 1 |
| 220-222 | 0 |
| 222-224 | 0 |
| 224-226 | 0 |
| 226-228 | 0 |
| 228-230 | 0 |
| 230-232 | 0 |
| 232-234 | 1 |
| 234-236 | 0 |
| 236-238 | 1 |
| 238-240 | 0 |
| 240-242 | 0 |
| 242-244 | 1 |
| 244-246 | 2 |
| 246-248 | 1 |
| 248-250 | 2 |
| 250-252 | 1 |
| 252-254 | 0 |
| 254-256 | 0 |
| 256-258 | 1 |
| 258-260 | 0 |
| 260-262 | 0 |
| 262-264 | 0 |
| 264-266 | 0 |
| 266-268 | 2 |
| 268-270 | 0 |
| 270-272 | 0 |
| 272-274 | 0 |
| 274-276 | 0 |
| 276-278 | 1 |
| 278-280 | 0 |
| 280-282 | 1 |
| 282-284 | 0 |
| 284-286 | 1 |
| 286-288 | 1 |
| 288-290 | 0 |
| 290-292 | 1 |
| 292-294 | 0 |
| 294-296 | 0 |
| 296-298 | 0 |
| 298-300 | 1 |
| 300-302 | 0 |
| 302-304 | 0 |
| 304-306 | 1 |
| 306-308 | 0 |
| 308-310 | 1 |
| 310-312 | 1 |
| 312-314 | 0 |
| 314-316 | 1 |
| 316-318 | 0 |
| 318-320 | 1 |
| 320-322 | 2 |
| 322-324 | 2 |
| 324-326 | 1 |
| 326-328 | 0 |
| 328-330 | 0 |
| 330-332 | 1 |
| 332-334 | 1 |
| 334-336 | 0 |
| 336-338 | 0 |
| 338-340 | 1 |
| 340-342 | 1 |
| 342-344 | 0 |
| 344-346 | 0 |
| 346-348 | 1 |
| 348-350 | 2 |
| 350-352 | 1 |
| 352-354 | 0 |
| 354-356 | 0 |
| 356-358 | 0 |
| 358-360 | 1 |
| 360-362 | 2 |
| 362-364 | 1 |
| 364-366 | 1 |
| 366-368 | 2 |
| 368-370 | 2 |
| 370-372 | 1 |
| 372-374 | 0 |
| 374-376 | 0 |
| 376-378 | 2 |
| 378-380 | 0 |
| 380-382 | 1 |
| 382-384 | 2 |
| 384-386 | 0 |
| 386-388 | 0 |
| 388-390 | 0 |
| 390-392 | 0 |
| 392-394 | 2 |
| 394-396 | 0 |
| 396-398 | 0 |
| 398-400 | 1 |
| 400-402 | 1 |
| 402-404 | 0 |
| 404-406 | 1 |
| 406-408 | 1 |
| 408-410 | 0 |
| 410-412 | 0 |
| 412-414 | 2 |
| 414-416 | 0 |
| 416-418 | 1 |
| 418-420 | 0 |
| 420-422 | 0 |
| 422-424 | 1 |
| 424-426 | 0 |
| 426-428 | 1 |
| 428-430 | 3 |
| 430-432 | 0 |
| 432-434 | 1 |
| 434-436 | 0 |
| 436-438 | 0 |
| 438-440 | 0 |
| 440-442 | 0 |
| 442-444 | 0 |
| 444-446 | 0 |
| 446-448 | 0 |
| 448-450 | 0 |
| 450-452 | 1 |
| 452-454 | 0 |
| 454-456 | 1 |
| 456-458 | 0 |
| 458-460 | 1 |
| 460-462 | 1 |
| 462-464 | 1 |
| 464-466 | 0 |
| 466-468 | 0 |
| 468-470 | 1 |
| 470-472 | 0 |
| 472-474 | 0 |
| 474-476 | 1 |
| 476-478 | 0 |
| 478-480 | 2 |
| 480-482 | 1 |
| 482-484 | 1 |
| 484-486 | 1 |
| 486-488 | 0 |
| 488-490 | 0 |
| 490-492 | 2 |
| 492-494 | 1 |
| 494-496 | 1 |
| 496-498 | 0 |
| 498-500 | 2 |
| 500-502 | 0 |
| 502-504 | 2 |
| 504-506 | 2 |
| 506-508 | 0 |
| 508-510 | 0 |
| 510-512 | 1 |
| 512-514 | 0 |
| 514-516 | 0 |
| 516-518 | 0 |
| 518-520 | 1 |

This distribution is the DERIVED input for an indentation threshold. **No threshold is ratified here** — the provisional cut above exists only to produce this report's other numbers; the real threshold is a design-chat ruling, with its own scope guard and tuning note.

---

## (c) Per-page table

| page_index | cohort | line_count | modal_left_margin | detected_openings | centred | chapter_heading | running_head | folio_number | verse_block |
|---|---|---|---|---|---|---|---|---|---|
| 1 | C | 68 | 0 | 35 | 0 | 12 | 0 | 0 | 2 |
| 2 | C | 103 | 0 | 69 | 3 | 10 | 0 | 0 | 8 |
| 10 | E | 28 | 42 | 4 | 0 | 1 | 0 | 0 | 0 |
| 12 | E | 36 | 44 | 8 | 1 | 1 | 0 | 0 | 0 |
| 13 | A | 37 | 196 | 2 | 0 | 3 | 0 | 0 | 0 |
| 14 | E | 34 | 158 | 1 | 0 | 4 | 0 | 0 | 0 |
| 19 | A | 44 | 149 | 2 | 0 | 3 | 0 | 0 | 0 |
| 20 | A | 12 | 68 | 4 | 0 | 1 | 0 | 0 | 0 |
| 39 | A | 36 | 65 | 6 | 0 | 0 | 0 | 0 | 0 |
| 68 | A | 29 | 57 | 2 | 1 | 2 | 0 | 0 | 0 |
| 124 | B | 8 | 580 | 0 | 0 | 0 | 0 | 0 | 0 |
| 135 | A | 35 | 51 | 5 | 0 | 1 | 0 | 0 | 2 |
| 138 | D | 33 | 47 | 5 | 0 | 0 | 0 | 0 | 0 |
| 144 | D | 29 | 34 | 10 | 1 | 2 | 0 | 0 | 0 |
| 146 | A | 36 | 36 | 12 | 0 | 0 | 0 | 0 | 5 |
| 150 | A | 32 | 50 | 6 | 0 | 0 | 0 | 0 | 0 |
| 155 | A | 30 | 52 | 5 | 3 | 2 | 0 | 0 | 3 |
| 158 | D | 35 | 22 | 6 | 0 | 0 | 0 | 0 | 3 |
| 162 | D | 36 | 41 | 11 | 0 | 0 | 0 | 0 | 0 |
| 187 | A | 31 | 48 | 4 | 2 | 0 | 1 | 0 | 0 |
| 190 | C | 28 | 44 | 6 | 1 | 2 | 0 | 0 | 0 |
| 214 | A | 35 | 51 | 3 | 0 | 0 | 0 | 0 | 0 |
| 216 | A | 29 | 43 | 5 | 1 | 1 | 0 | 0 | 0 |
| 219 | A | 36 | 60 | 6 | 0 | 0 | 0 | 0 | 2 |
| 302 | A | 38 | 46 | 12 | 1 | 0 | 0 | 0 | 0 |
| 307 | C | 54 | 3 | 34 | 1 | 2 | 0 | 0 | 6 |
| 308 | C | 65 | 0 | 38 | 1 | 8 | 0 | 1 | 2 |

---

## (d) Detected paragraph structure — page 125 + 3 overlap pages

### page_index=124

(zero candidate openings detected on this page)

### page_index=13

| line_no | first 8 words |
|---|---|
| 18 | Madame Melba, |
| 34 | 949 Broadway, New York, London, TV, |

### page_index=19

| line_no | first 8 words |
|---|---|
| 0 | . |
| 1 | List of Illustrations |

### page_index=20

| line_no | first 8 words |
|---|---|
| 0 | List of Illustrations. xv |
| 7 | L. The Hand of Lord Charles Beresford. 211 |
| 8 | LI. The Hand of Mr. William Whiteley. 213 |
| 9 | LII. The Hand of Gen. Sir Redvers Buller, |

---

## (e) Pages with ZERO detected openings

| page_index | cohort | line_count | false_positive_counts | judgment |
|---|---|---|---|---|
| 124 | B | 8 | {'body_continuation': 8} | genuinely single-paragraph (all lines flush-left, no indented opening — plausible for a page that continues mid-paragraph from the prior page) |

---

## (f) Stated limitations

- **The text-to-native-token-index bridge is a literal-subsequence search, not a full alignment.** Section (a)'s bridge locates an opening line's first 1-3 words as an exact match inside the native token list — it can fail to find a genuine match if OCR/PDF-extraction noise differs between `extract_text_lines()` and `extract_text()` for that specific span (rare, since both read the same text objects, but not impossible), and it does not attempt a fuzzy or partial match when the exact 1-3 word key is absent.
- **Indentation convention pages.** Any page where the printer did not consistently first-line-indent new paragraphs (title pages, tables of contents, dedication pages) will not show the signal this method looks for — cohort C's zero-chunk pages include exactly this kind of apparatus page.
- **Tables and multi-column layout.** `extract_text_lines()` assumes a single reading column; a page with a genuine table or side-by-side columns would have its cells' x0 values conflated into one modal-margin computation, producing meaningless indents.
- **Plate captions and illustration pages.** Pages with `extract_text_lines() count == 0` have nothing for this method to work with at all — they are plates, not text pages, regardless of what a boundary seeder does with them.
- **The false-positive taxonomy itself is heuristic, not exhaustive.** `chapter_heading`'s "<=6 words, all-caps" rule and `centred`'s 10pt symmetry tolerance are stated, reasoned cuts, not empirically validated against a negative-control set the way U0.5's support-score floor was.

---

## (g) Recommendation

**None made.** No ruling on the indent threshold, seeder design, or whether to adopt layout-based derivation at all — report only, per instruction.
