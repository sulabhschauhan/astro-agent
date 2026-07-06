# PyJHora Ashtakavarga (BAV/SAV) Sign-Indexing — Read-Only Diagnostic
Date: 2026-07-06
Scope: `PyJHora-main/src/jhora/` (local copy). Read-only — no files modified.

## Step 1 — Module location

Core computation: `PyJHora-main/src/jhora/horoscope/chart/ashtakavarga.py`
(this is the module actually imported by the GUI — see Step 3).

A second file, `PyJHora-main/src/jhora/horoscope/dhasa/graha/ashtaka_varga.py`,
also matches the search terms but implements Ashtakavarga **dasha** (a
timing/dhasa system that consumes BAV/SAV numbers), not the BAV/SAV
computation itself. Not analyzed further — out of scope for the
sign-indexing question.

## Step 2 — Core BAV computation: index convention

File: `PyJHora-main/src/jhora/horoscope/chart/ashtakavarga.py`, function
`get_ashtaka_varga`, lines 27–58.

Docstring (lines 28–36), verbatim:
```
    """
        get binna, samudhaya and prastara varga from the given horoscope chart
        @param house_to_planet_list: 1-D array [0..11] with planets in each raasi
            Example: ['','','','','2','7','1/5','0','3/4','L','','6/8']
        @return: 
            binna_ashtaka_varga - 2-D List [0..7][0..7] 0=Sun..7=Lagnam
            samudhaya ashtaka varga - 1D List [0..11] 0=Aries 11=Pisces
            prastara ashtaka varga - 3D List [0..7][0..7][0..11]
    """
```

The bindu-assignment loop, lines 42–54, verbatim:
```
    for key in const.ashtaka_varga_dict.keys():
        p = int(key)
        #planet = planet_list[p]
        planet_raasi_list = const.ashtaka_varga_dict[key]
        for op,other_planet in enumerate(planet_raasi_list):
            pr = p_to_h[op]
            if op == 7: #Lagnam
                pr = p_to_h[const._ascendant_symbol]
            for raasi in other_planet:
                r = (raasi-1+pr) % 12
                raasi_ashtaka[p][r] +=1
                prastara_ashtaka_varga[p][op][r] = 1
                prastara_ashtaka_varga[p][-1][r] += 1
```

**Finding:** `r = (raasi-1+pr) % 12` computes an absolute rasi number by
adding the classical Ashtakavarga table's house-count offset (`raasi-1`,
counted from each contributing planet's own occupied sign) to that
planet's absolute occupied-sign index (`pr`, itself the array position
where `p_to_h` found the planet in `house_to_planet_list`, which is
built Aries-first — see `get_planet_to_house_dict_from_chart` in
`utils.py`, not reproduced here as it is a straightforward positional
scan of the 0=Aries-indexed input list). The result `r` is stored
directly as the array index into `raasi_ashtaka[p]`.

**Index 0 of the output = Aries absolute, index 11 = Pisces absolute.**
This is stated explicitly in the docstring (`0=Aries 11=Pisces`, line
34) and is structurally confirmed by the modulo-12 arithmetic, which
has no lagna-relative rotation applied anywhere in the function — `pr`
(the reference point for each planet's own contribution) is itself an
absolute sign index, not a rotated/relative one. `binna_ashtaka_varga`
(line 55) and `samudhaya_ashtaka_varga` (line 57, `.sum(axis=0)` over
`binna_ashtaka_varga`) inherit this same absolute indexing since they
are sliced/summed directly from `raasi_ashtaka` without any rotation
step.

## Step 3 — GUI/chart-rendering code: corner-to-index mapping

Caller: `PyJHora-main/src/jhora/ui/horo_chart_tabs.py`,
`_update_ashtaka_varga_tab_information`, lines 5738–5765.

```python
5738	        chart_1d = self._ashtaka_chart#self._horoscope_charts[t] #charts[t]
5739	        chart_1d = self._convert_language_chart_to_indices(chart_1d)
5740	        bav,sav, _ = ashtakavarga.get_ashtaka_varga(chart_1d)#_en)
5741	        ac = 0
5742	        for _ in range(3):
5743	            for _ in range(3):
5744	                if ac ==0:
5745	                    chart_data_1d = sav
5746	                    chart_title = 'SAV'
5747	                else:
5748	                    chart_data_1d = bav[ac-1]
5749	                    # Last value is Lagnam not Raghu
5750	                    chart_title = self.resources['ascendant_str'] if ac==8 else self._horo._get_planet_list()[0][ac-1]
5751	                if 'north' in self._chart_type.lower() or 'sudar' in self._chart_type.lower():
5752	                    #_ascendant = drik.ascendant(jd,place)
5753	                    asc_house = self._ashtaka_ascendant_house+1 # _ascendant[0]+1
5754	                    chart_data_north = chart_data_1d[asc_house:]+chart_data_1d[0:asc_house] # V4.7.5
5755	                    self._ashtaka_charts[ac].setData(chart_data_north,chart_title=chart_title,chart_title_font_size=ashtaka_chart_title_font_size)
5756	                elif 'east' in self._chart_type.lower():
5757	                    chart_data_2d = utils._convert_1d_house_data_to_2d(chart_data_1d,self._chart_type)
5758	                    row,col = const._asc_house_row_col__chart_map[self._ashtaka_ascendant_house]
5759	                    self._ashtaka_charts[ac]._asc_house = row*self._ashtaka_charts[ac].row_count+col
5760	                    self._ashtaka_charts[ac].setData(chart_data_2d,chart_title=chart_title,chart_title_font_size=ashtaka_chart_title_font_size)
5761	                else: # south indian
5762	                    chart_data_2d = utils._convert_1d_house_data_to_2d(chart_data_1d)
5763	                    row,col = const._asc_house_row_col__chart_map[self._ashtaka_ascendant_house]
5764	                    self._ashtaka_charts[ac]._asc_house = (row,col)
5765	                    self._ashtaka_charts[ac].setData(chart_data_2d,chart_title=chart_title,chart_title_font_size=ashtaka_chart_title_font_size)
```

This branches on **PyJHora's own chart display style setting**
(`self._chart_type`), not a single fixed layout. Three distinct
conventions coexist in this codebase:

### 3a. North Indian / Sudarshan Chakra style (diamond) — LAGNA-RELATIVE
Line 5754: `chart_data_north = chart_data_1d[asc_house:]+chart_data_1d[0:asc_house]`
— the Aries-absolute array **is rotated** so that array position 0
becomes the ascendant sign, before being handed to the diamond widget.

Cell layout for the rotated array is fixed geometric positions in
`PyJHora-main/src/jhora/ui/chart_styles.py`,
class `NorthIndianChart`, lines 1263–1265:
```
1263	    _north_label_positions = [(4/10,1.0/10),(1.5/10,0.5/10),(0.1/10,2.0/10),(1.5/10,4/10), 
1264	                     (0.1/10,7/10), (1.75/10,8.5/10), (3.5/10,7/10), (6.75/10,8.5/10),
1265	                     (8.5/10,7/10),(6.5/10,4/10),(8.35/10,2.0/10),(6.5/10,0.5/10)]
```
`self.label_positions` (assigned from this list, line 1306) is walked
in array order at draw time (`for l, pos in enumerate(self.label_positions):`,
line 1567 of the same file). Position index 0 = `(0.4, 0.1)`, the
top-center diamond cell — i.e. **array index 0 (which, after the
line-5754 rotation, is the ascendant/house-1) lands in the top-center
cell.** Walking the coordinate list in order (0→11) traces top-center →
top-left → left edge (upper→mid→lower) → bottom-left → bottom edge →
bottom-right → right edge (lower→mid→upper) → top-right → back to
top-center — i.e. **counter-clockwise** (leftward first from the top
cell) in standard screen coordinates (x right, y down). No comment in
the file states this direction explicitly for North Indian; this
reading is inferred from the (x,y) coordinate sequence, so treat the
direction (though not the index-0-is-ascendant fact, which is explicit
from line 5754/5750) as moderate- rather than high-confidence.

### 3b. East Indian style — ARIES-ABSOLUTE, direction stated explicitly in source
`utils._convert_1d_house_data_to_2d` (`PyJHora-main/src/jhora/utils.py`,
lines 1030–1039), east branch:
```python
1036	    elif 'east' in chart_type.lower():
1037	        row_count = 3
1038	        col_count = 3
1039	        map_to_2d = [['2'+separator+'1','0','11'+separator+'10'], ['3', "",'9' ], ['4'+separator+'5','6','7'+separator+'8']]
```
Here the map keys (`'0'`, `'1'`, ... `'11'`) are **absolute Aries-based
rasi numbers**, not rotated array positions — `chart_data_1d` (still
Aries-absolute, no rotation applied on this branch, line 5757) is
placed straight into these fixed cells by value-matching the index `p`
against the map string (line 1046-1047: `_index_containing_substring(row,str(p))`).
The class docstring for `EastIndianChart`
(`PyJHora-main/src/jhora/ui/chart_styles.py`, line 531) states
explicitly: `"East Indian chart is 3x3 goes anti-clockwise from top-middle"`.
Top-middle cell = `'0'` = Aries. The ascendant is NOT used to rotate
the array on this branch — it is only used (lines 5758–5759) to flag
which fixed cell should carry the ascendant marker, via
`const._asc_house_row_col__chart_map` (`PyJHora-main/src/jhora/const.py`,
line 811):
```
811	_asc_house_row_col__chart_map = [(0,1),(0,2),(0,3),(1,3),(2,3),(3,3),(3,2),(3,1),(3,0),(2,0),(1,0),(0,0)]
```
(indexed by absolute ascendant-sign number 0–11, returning the fixed
grid row/col of that sign — e.g. entry 0 → `(0,1)`, matching Aries's
fixed position in the South Indian `map_to_2d` below).

### 3c. South Indian style — ARIES-ABSOLUTE, fixed grid, clockwise
Same function, south branch (lines 1032–1035):
```python
1032	    if 'south' in chart_type.lower():
1033	        row_count = 4
1034	        col_count = 4
1035	        map_to_2d = [ [11,0,1,2], [10,"","",3], [9,"","",4], [8,7,6,5] ]
```
Also absolute Aries-indexed (integers, not strings, but same
principle): row 0 = `[Pisces(11), Aries(0), Taurus(1), Gemini(2)]`,
then reading the border clockwise — `2→3(row1col3,Cancer)→4(row2col3,Leo)
→5,6,7,8` along the bottom right-to-left → `8→9→10` up the left side
→ back to `11`. No rotation by ascendant is applied to the data
(`chart_data_2d = utils._convert_1d_house_data_to_2d(chart_data_1d)`,
line 5762, called with no chart_type argument, defaulting to
`'south_indian'`); the ascendant again only supplies a marker cell via
`_asc_house_row_col__chart_map` (lines 5763–5764), exactly as in the
East Indian branch.

## Step 4 — Do computation array and display array share one convention?

**No — they diverge, and the divergence is resolved (not ambiguous) by
branch:**

- The **computation output** (`get_ashtaka_varga`'s `binna_ashtaka_varga`
  / `samudhaya_ashtaka_varga`) is **always Aries-absolute** (index
  0 = Aries), unconditionally, regardless of what chart style the UI is
  set to.
- The **East and South Indian display branches** consume that array
  **unmodified** — same Aries-absolute convention, laid into a fixed
  (non-rotating) grid, with the ascendant marked separately by a
  lookup table rather than by rotating the data.
- The **North Indian / Sudarshan Chakra display branch is the only one
  that rotates the array** (`horo_chart_tabs.py` line 5754) before
  handing it to the widget, converting it from Aries-absolute to
  lagna-relative (index 0 = ascendant/house-1) at the point of display,
  not at the point of computation.

This is architecturally consistent (not a bug or unresolved ambiguity):
North Indian charts are drawn with the lagna fixed to one screen cell
and the rasis rotating around it, while South/East Indian charts are
drawn with the rasis fixed to screen cells and the lagna cell varying.
Any consumer of `get_ashtaka_varga()`'s raw return value should treat
it as Aries-absolute; only the North-Indian rendering path performs a
lagna rotation, and it does so on a local copy after calling the
function, not inside `ashtakavarga.py` itself.

**Caveat on Windows JHora vs. this PyJHora GUI:** everything in Step 3
is PyJHora's own PyQt GUI (`src/jhora/ui/*.py`), which per the module's
own header comments is a from-scratch Python reimplementation
("Downloaded from https://github.com/naturalstupid/PyJHora", modified
by a third party) — it is **not** the original Windows JHora
executable's source (that program is closed-source VB/Delphi and is
not present anywhere in this repository or the `PyJHora-main`
checkout). This diagnostic cannot confirm whether Windows JHora's own
diamond-chart screenshots use the same top-center/counter-clockwise
convention found in `NorthIndianChart` above — that would require the
original Windows JHora source or a labeled reference screenshot, neither
of which is in scope here. Treat the "matches JHora UI screenshots"
part of the task as **not resolved** — only PyJHora's own GUI
convention is established above.
