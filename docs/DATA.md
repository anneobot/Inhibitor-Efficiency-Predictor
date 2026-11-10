# Data

How the corpus was assembled, what was changed and why, and what the resulting table contains.

---

## 1. Provenance

No new corrosion measurements were generated for the modelling component of this study. The
corpus was assembled entirely from published, publicly accessible data, on the reasoning that
a model intended to generalise across inhibitor chemistries, substrate metals and electrolytes
needs a breadth of coverage no single laboratory campaign could supply within the period of
the research.

### CORDATA

An open data-management web application for the selection of corrosion inhibitors, aggregating
inhibition-efficiency measurements drawn from more than one hundred and twenty primary
publications. Each record carries the inhibitor identity and SMILES string, the substrate
metal and alloy designation, the measured efficiency, exposure duration, temperature,
inhibitor concentration, supporting-salt concentration, measurement methodology, pH where
reported, the identity of any synergistic additive, and a citation to the originating
publication. The export used was the multi-metal release covering aluminium, copper, iron,
magnesium and zinc: **5,000 rows across seventeen fields**.

> Galvão, T. L. P., Ferreira, I., Kuznetsova, A., Rocha, A. B., Tedim, J., & Ferreira, M. G. S.
> (2022). CORDATA: An open data management web application to select corrosion inhibitors.
> *npj Materials Degradation, 6*, 48. https://doi.org/10.1038/s41529-022-00259-9

### ExCorr

An interactive corrosion-inhibitor database maintained by the Helmholtz-Zentrum Hereon. The
export used contained **4,616 rows across thirty-five fields**, including inhibitor name,
canonical SMILES, substrate metal and alloy, the aggressive component of the electrolyte,
exposure duration in hours, temperature in degrees Celsius, inhibitor concentration in
millimolar, measurement method and reported efficiency.

> Würger, T. (n.d.). *ExCorr: An interactive corrosion inhibitor database* [Web application].
> Helmholtz-Zentrum Hereon. https://excorr.web.app

### Inhibitor 1368

A curated dataset of organic corrosion inhibitors for carbon steel in hydrochloric acid,
supplied as a tabulation of molecular properties, quantum-chemical parameters and measured
efficiencies. **1,364 usable rows across thirty fields.** It is distinguished from the other
two by carrying density-functional-theory frontier-orbital descriptors — the energies of the
highest occupied and lowest unoccupied molecular orbitals, and quantities derived from them —
for a subset of its molecules.

> Gong, H., Fu, Z., Ma, L., & Zhang, D. (2024). Inhibitor_Mol_VAE: A variational autoencoder
> approach for generating corrosion inhibitor molecules. *npj Materials Degradation, 8*(1),
> 102.

### Comparison

| Attribute | CORDATA | ExCorr | Inhibitor 1368 |
|---|---|---|---|
| Rows in the export | 5,000 | 4,616 | 1,364 |
| Fields in the export | 17 | 35 | 30 |
| Substrate metals | Al, Cu, Fe, Mg, Zn | Al, Cu, Fe, Mg, Zn | Fe (carbon steel) |
| Electrolyte recorded as | salt concentration and medium | aggressive component | 1 M HCl throughout |
| pH reported | on usable rows | on 21.8 % of rows | not reported |
| Exposure duration | yes, hours | yes, hours | not reported |
| Measurement method | yes | yes | not reported |
| Quantum descriptors | no | no | yes, on a subset |

**The raw source exports are not redistributed in this repository.** Obtain them from the
databases above. What is published here is the harmonised, deduplicated derivative described
below.

---

## 2. Structural validation

Every SMILES string was parsed with RDKit and converted to canonical form. Canonicalisation
was necessary because the same molecule is frequently written in different but chemically
equivalent notations across sources and even within one source, and because the canonical
string is subsequently the grouping key for both deduplication and partitioning. Without it,
two spellings of one compound would have been treated as two compounds, **silently defeating
the leakage control that is the point of the study**.

Records whose SMILES could not be parsed were removed, as were inorganic species, counterion
salts and records describing mixtures rather than single organic compounds. This follows
established practice in the data-driven corrosion inhibition literature, where inorganic and
mixed systems are modelled separately because their inhibition mechanisms, adsorption
behaviour and descriptor spaces differ. Retaining them would have introduced records for which
the molecular descriptors carry a different physical meaning.

---

## 3. Target cleaning

Inhibition efficiency was standardised to a percentage on [0, 100]. Inhibitor 1368 reports
efficiency as a fraction and was multiplied by 100; the other two report percentages directly.

A small number of records carried values outside the physically meaningful range. These arise
in the primary literature from experimental scatter near the extremes, from rounding in
secondary compilation, and occasionally from transcription. **They were clipped to the
boundaries rather than discarded**, because the accompanying structural and condition
information remains valid, and because discarding them would have introduced a selection
effect at the top of the range — exactly where the best inhibitors sit and where the model
most needs training signal.

Every clipping operation was logged. [`../data/preprocessing_audit.csv`](../data/preprocessing_audit.csv):

| Source | Rows entering | Surviving target parsing | Clipped to range |
|---|---|---|---|
| Inhibitor 1368 | 1,364 | 1,364 | 0 |
| CORDATA | 5,000 | 4,224 | 0 |
| ExCorr | 4,616 | 4,609 | 359 |

This audit serves two purposes. It provides traceability, so any individual prediction can be
traced back through the pipeline to its source record. And it constrains non-physical
extrapolation, because an explicit record of which values were moved to the boundary prevents
the model from being credited with learning behaviour that preprocessing imposed.

---

## 4. Harmonisation

A common schema of fifteen fields was defined, and a dedicated harmonisation function written
for each source: source identifier, inhibitor name, canonical SMILES, inhibition efficiency,
base metal, alloy designation, electrolyte, temperature, exposure duration, inhibitor
concentration, pH, pH provenance flag, measurement methodology, supporting-salt concentration,
synergist indicator.

**Units.** Temperature to kelvin throughout, with Celsius values converted by addition of
273.15 and textual entries such as `RT` and `ambient` mapped to 298.15 K, the convention in
the corrosion literature for unreported room-temperature work. Concentration to millimolar,
with molar values multiplied by one thousand. Duration to hours — a choice confirmed against
the data by the presence of the characteristic values 24, 168 and 672, being one day, one week
and four weeks.

**Methodology vocabulary.** The field contained twenty-nine distinct labels across the three
sources, many naming the same technique: gravimetric measurement appeared as *weight loss*,
*mass loss*, *gravimetry* and *gravimetric*; hydrogen evolution as *H2 evolution*, *hydrogen
evolution* and *gasometry*; potentiodynamic polarisation under both British and American
spellings and also as *Tafel polarization* and *Tafel extrapolation*. Left uncontrolled, one
technique would occupy several categories, splitting its statistical support and rendering any
disaggregated analysis unreadable. A canonical mapping reduced twenty-nine labels to **eleven
techniques**, merging spelling, language and naming variants **only**. Techniques that differ
physically were kept apart: linear polarisation resistance was not merged with potentiodynamic
polarisation, and impedance spectroscopy was not merged with frequency modulation.

**Alloy vocabulary.** Treated more conservatively. Case and whitespace variants were
normalised, so *Carbon steel* and *Carbon Steel* merged, but **no semantic merging of distinct
grades was performed**. AA2024 and AA7075 differ in copper content and corrosion behaviour and
were kept separate, as were mild steel, carbon steel, cold rolled steel and stainless steel.
**Seventy-seven designations** survived.

**Substrate representation.** An earlier iteration had collapsed the substrate to a few
pseudo-metals, losing alloy information and creating a spurious category by treating carbon
steel and iron as different metals. The substrate is now represented on two levels: the base
metal, normalised so every ferrous designation resolves to `Fe`, every aluminium alloy to `Al`
and so on; and the alloy designation retained in parallel, carrying the full grade. Both enter
the feature matrix — the metal as a four-category encoding, the alloy as an indicator encoding
restricted to the **38 designations supported by at least thirty rows**, the remainder pooled
into a single residual category.

---

## 5. Recovery of solution pH

### Why

Solution pH governs the corrosion reaction. It determines which cathodic reaction dominates,
controls the surface charge of the metal and therefore the electrostatic component of
adsorption, and governs the protonation state of the inhibitor, which determines whether the
molecule approaches the surface neutral or as a cation. **A model of inhibition efficiency
that does not know the pH is missing the variable that most directly couples the molecule to
the surface.**

An earlier iteration excluded pH. That was defensible on the information then available — it
was reported on about a fifth of records, and listwise deletion would have reduced the corpus
to a few hundred rows. Methodological review identified the exclusion as a substantive
weakness and raised the possibility of recovering pH from the corrodent concentration. That
suggestion is chemically correct and is the basis of the procedure below.

### Rules

| Class of medium | Expression | Worked example |
|---|---|---|
| Strong acid (HCl, HNO₃, HClO₄, H₂SO₄ first dissociation) | pH = −log₁₀ C | 1 M HCl → pH 0.0 |
| Strong base (NaOH, KOH) | pH = 14 + log₁₀ C | 0.1 M NaOH → pH 13.0 |
| Weak acid | pH = ½(pKₐ − log₁₀ C) | 1.0 M CH₃COOH, pKₐ 4.76 → pH 2.38 |
| Neutral salt (NaCl, Na₂SO₄, KCl) | pH = 7.0 | 3.5 % NaCl → pH 7.0 |
| Mixed neutral salts | pH = 7.0 | 0.6 M NaCl + 0.02 M Na₂SO₄ → pH 7.0 |
| Natural waters | tabulated | seawater → pH 8.1 |

C is the molar concentration of the dissolved species. Percentage concentrations were
converted using the formula weight and an assumed solution density of 1.0 g cm⁻³.

Inhibitor 1368 reports no medium field; its protocol is documented as carbon steel in 1 M HCl.
A single constant would have asserted a precision the record does not support, and would have
handed the model one repeated value on which it could key the entire source. **A value was
therefore drawn from U(−0.2, 0.4)**, which brackets the pH of 1 M HCl under the applicable
activity corrections, and every such value was flagged `banded`.

### Validation

Checked on the 848 ExCorr records carrying **both** a reported pH and a derivable medium.

| Quantity | Value |
|---|---|
| Records with both | 848 |
| Median absolute difference | 1.00 pH unit |
| Agreeing within one unit | 62.7 % |
| Agreeing within two units | 70.8 % |
| Mean signed difference | **+0.46**, reported value higher |

**The direction and magnitude both support the derivation.** A reported pH is in most
protocols measured in the working solution, often after immersion has begun, by which point
the cathodic reaction has consumed hydrogen ions and metal dissolution has raised the local
pH. The derived value returns the nominal pH of the make-up solution before any metal was
introduced. A systematic offset of roughly half a unit to one unit in that direction is the
signature of exactly this effect. Had the derived values been systematically *lower*, or the
deviation unsigned and scattered, the derivation would be suspect.

Applying it raised pH availability from **21.8 % to 99.5 %** of rows.

### The provenance flag

A pH inferred from the medium is not evidentially equivalent to one measured with an
electrode, and the model was not permitted to treat them as equivalent. Every record carries a
categorical provenance field, entering the matrix as a four-column indicator encoding, so the
model can learn a different relationship between pH and efficiency according to how the pH was
established — and so that any reader can see how much of the pH signal rests on inference.

| Flag | Rows | Meaning |
|---|---|---|
| `measured` | 4,055 | The source reported the value |
| `derived` | 2,902 | Computed from the medium by the rules above |
| `banded` | 1,359 | Drawn from a documented interval |
| `missing` | 43 | Neither route available |

The provenance block's measured contribution to explained variance is **−0.005**. It is
carried for transparency, not for predictive gain. See [`LIMITATIONS.md`](LIMITATIONS.md).

---

## 6. Deduplication

Concatenating the three harmonised frames gave **10,197 rows**. The sources overlap — 445
molecules common to ExCorr and Inhibitor 1368, 98 to CORDATA and ExCorr — so deduplication was
required.

The composite key is the canonical SMILES, base metal, alloy designation, rounded temperature,
rounded exposure duration, rounded concentration and rounded pH. Records agreeing on every
element describe the same measurement under the same conditions and were collapsed to a single
row, with efficiency averaged and the **number of contributing measurements retained as a
field**. That retained count is what later made the measurement-reproducibility floor
computable.

**The key deliberately includes the experimental conditions, not merely the structure.** Two
measurements of the same molecule at different temperatures are two distinct observations;
collapsing them would destroy the condition response the model exists to learn.

Deduplication gave **8,393 rows covering 1,053 distinct structures**.

A residual limitation: because duration participates in the key, and because Inhibitor 1368
never reports duration while its ExCorr counterparts frequently do, some near-duplicate pairs
were separated by duration being present on one side and absent on the other. **This affects
the row-wise control partition only** — under grouping and scaffolding, every copy of a
molecule goes to the same fold by construction.

---

## 7. Metal scope

| Metal | Rows | Retained |
|---|---|---|
| Fe | 3,514 | yes |
| Al | 2,783 | yes |
| Mg | 1,631 | yes |
| Cu | 431 | yes |
| Zn | 33 | **no** |
| unresolved | 1 | **no** |

Zinc was excluded because thirty-three measurements across thirty-one molecules cannot support
a fold structure in which each of five validation folds must contain molecules absent from
training. **No metal was excluded for being merely inconvenient**, and the imbalance among the
four retained metals was measured and reported rather than removed — resampling would have
distorted the marginal distribution of a corpus assembled from the published record, and the
imbalance is itself a finding about that record.

The scoped modelling corpus is **8,359 rows**.

---

## 8. The published files

### `data/master_table.csv`

8,393 rows × 17 columns — the full deduplicated table, before metal scoping. Filter to
`metal ∈ {Fe, Al, Mg, Cu}` to obtain the 8,359-row modelling corpus.

| Column | Type | Notes |
|---|---|---|
| `canonical_smiles` | text | RDKit canonical form; the grouping key for partitioning |
| `metal` | text | Normalised base metal |
| `alloy` | text | Grade designation, case- and whitespace-normalised only |
| `IE_percent` | float | Target, [0, 100]; mean where a group was collapsed |
| `IE_percent_std` | float | Within-group standard deviation where more than one measurement |
| `n_measurements` | int | Contributing measurements; the basis of the noise-floor estimate |
| `sources` | text | Which of the three databases contributed |
| `inhibitor_name` | text | As recorded in the source |
| `electrolyte` | text | Medium description as recorded; the input to pH derivation |
| `temperature_K` | float | Kelvin |
| `duration_h` | float | Hours; null where never recorded |
| `concentration_mM` | float | Millimolar |
| `pH` | float | Measured, derived or banded per `ph_source` |
| `ph_source` | text | `measured` / `derived` / `banded` / `missing` |
| `methodology` | text | One of eleven, after vocabulary control |
| `salt_concentration_M` | float | mol/L; null where not recorded |
| `synergist_present` | int | 0 or 1 |

### `data/fold_indices.npy`

The fold assignment for every row under each of the three partitioning schemes, generated once
and read by every model in the study. **This file is what makes the benchmark a benchmark**
rather than a collection of separately obtained numbers.

### `data/descriptor_names.json`

The 217 RDKit descriptors in the order computed. Descriptors are resolved **by name**, never
by position, because `Descriptors.descList` changes length between RDKit releases and
positional indexing would silently shift every column.

### `data/preprocessing_audit.csv`

The per-source clipping audit reproduced in §3.

### Not published

`descriptors.npy` (14 MB) and `fingerprints.npy` (131 MB) are not included — the latter
exceeds GitHub's file-size limit, and both are deterministic functions of
`canonical_smiles` under the pinned RDKit version. Regenerate them with Section 3.5 of the
notebook.

---

## 9. Corpus at a glance

| Property | Value |
|---|---|
| Rows after harmonisation | 10,197 |
| Rows after deduplication | 8,393 |
| Rows in the modelling corpus | 8,359 |
| Distinct canonical structures | 1,053 (1,050 after metal scoping) |
| Base metals retained | Fe 3,514 · Al 2,783 · Mg 1,631 · Cu 431 |
| Alloy designations | 77 recorded, 38 encoded individually |
| Measurement methodologies | 11 after vocabulary control |
| Mean measurements per molecule | 7.9 |
| pH availability | 99.5 % |
| Target range | 0–100 % inhibition efficiency |

**That mean of 7.9 measurements per molecule is the defining property of this corpus**, and it
governs everything in [`METHODS.md`](METHODS.md): a partition that separates *rows* rather
than *molecules* will place near-copies of the same compound on both sides of the train/test
boundary.
