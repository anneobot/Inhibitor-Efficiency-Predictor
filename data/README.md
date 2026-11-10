# Data

The harmonised corpus and the shared cross-validation partition. Full provenance, the
harmonisation rules and the pH recovery procedure are in [`../docs/DATA.md`](../docs/DATA.md).

| File | Size | What it is |
|---|---|---|
| `master_table.csv` | 1.3 MB | 8,393 deduplicated measurements × 17 fields |
| `fold_indices.npy` | 364 KB | the five-fold partition under all three schemes |
| `descriptor_names.json` | 3.6 KB | the 217 RDKit descriptors, in computed order |
| `preprocessing_audit.csv` | 120 B | per-source row counts and clipping record |

---

## `master_table.csv`

8,393 rows. Filter to `metal ∈ {Fe, Al, Mg, Cu}` for the **8,359-row modelling corpus**; the
remainder is 33 zinc rows and one unresolved row, excluded because thirty-three measurements
across thirty-one molecules cannot support a fold structure in which each validation fold must
contain molecules absent from training.

| Column | Type | Notes |
|---|---|---|
| `canonical_smiles` | text | RDKit canonical form. **The grouping key for deduplication and for partitioning** |
| `metal` | text | Normalised base metal: `Fe`, `Al`, `Mg`, `Cu` (plus excluded `Zn`) |
| `alloy` | text | Grade designation. Case- and whitespace-normalised only; no semantic merging |
| `IE_percent` | float | **Target.** Inhibition efficiency, 0–100. Mean where a group was collapsed |
| `IE_percent_std` | float | Within-group standard deviation where `n_measurements` > 1 |
| `n_measurements` | int | Contributing measurements. The basis of the noise-floor estimate |
| `sources` | text | Which of the three databases contributed |
| `inhibitor_name` | text | As recorded in the source |
| `electrolyte` | text | Medium description as recorded. The input to pH derivation |
| `temperature_K` | float | Kelvin. Celsius converted by +273.15; `RT`/`ambient` → 298.15 |
| `duration_h` | float | Hours. **Null where never recorded — 33 % of rows** |
| `concentration_mM` | float | Millimolar |
| `pH` | float | Measured, derived or banded according to `ph_source` |
| `ph_source` | text | `measured` 4,055 · `derived` 2,902 · `banded` 1,359 · `missing` 43 |
| `methodology` | text | One of eleven, after vocabulary control from twenty-nine raw labels |
| `salt_concentration_M` | float | mol/L. Null where not recorded |
| `synergist_present` | int | 0 or 1 |

```python
import pandas as pd

m = pd.read_csv("data/master_table.csv")
corpus = m[m.metal.isin(["Fe", "Al", "Mg", "Cu"])]
print(corpus.shape, corpus.canonical_smiles.nunique())   # (8359, 17)  1050
```

**Nulls are meaningful.** A null in `duration_h` or `salt_concentration_M` means *not
recorded*, which is a first-class state in this corpus rather than an error. The model was
trained with a was-missing indicator for each numeric condition, so it can learn a different
response to an imputed value than to a measured one. Do not fill them silently.

---

## `fold_indices.npy`

The fold assignment for every row under each of the three partitioning schemes — row-wise,
grouped by molecule, and Bemis–Murcko scaffold.

**This file is what makes the benchmark a benchmark.** It was generated once and read by every
one of the fifteen model configurations, so every model in [`../docs/RESULTS.md`](../docs/RESULTS.md)
was scored on identical rows. Reusing it is the only way to compare a new model against the
published leaderboard on equal terms.

---

## `descriptor_names.json`

The 217 RDKit descriptors in the order the pipeline computed them. Six are zero-variance
across the corpus and are dropped by the variance filter, leaving the 211 that enter the
feature matrix.

**Descriptors are resolved by name, never by position.** `Descriptors.descList` changes length
between RDKit releases, and positional indexing would silently shift every column. The
authoritative column order for the full 283-column matrix is
[`../model/contract.json`](../model/contract.json) → `feature_names`.

---

## `preprocessing_audit.csv`

| Source | Rows entering | Surviving target parsing | Clipped to [0, 100] |
|---|---|---|---|
| `inhibitor1368` | 1,364 | 1,364 | 0 |
| `datacor_al` (CORDATA) | 5,000 | 4,224 | 0 |
| `excorr` | 4,616 | 4,609 | 359 |

Out-of-range efficiencies were **clipped rather than discarded**, because the accompanying
structural and condition information remains valid and because discarding would introduce a
selection effect at the top of the range, where the best inhibitors sit. Logging every
clipping operation is what prevents the model from being credited with learning behaviour that
preprocessing imposed.

---

## Not published here

| File | Size | Why |
|---|---|---|
| `descriptors.npy` | 14 MB | Deterministic function of `canonical_smiles` under RDKit 2026.03.6. Regenerate with notebook §3.5 |
| `fingerprints.npy` | 131 MB | As above, and exceeds GitHub's 100 MB file limit |
| The three source exports | — | Not ours to redistribute. Obtain from the databases cited below |

---

## Licence and citation

The harmonised table is released under [CC BY 4.0](../LICENSE-DATA) as a **derived work**.
The measurements in it belong to the three source databases and, through them, to the primary
publications those databases compile. **Please cite the sources, not only this repository.**

> Galvão, T. L. P., Ferreira, I., Kuznetsova, A., Rocha, A. B., Tedim, J., & Ferreira, M. G. S.
> (2022). CORDATA: An open data management web application to select corrosion inhibitors.
> *npj Materials Degradation, 6*, 48. https://doi.org/10.1038/s41529-022-00259-9
>
> Würger, T. (n.d.). *ExCorr: An interactive corrosion inhibitor database* [Web application].
> Helmholtz-Zentrum Hereon. https://excorr.web.app
>
> Gong, H., Fu, Z., Ma, L., & Zhang, D. (2024). Inhibitor_Mol_VAE: A variational autoencoder
> approach for generating corrosion inhibitor molecules. *npj Materials Degradation, 8*(1),
> 102.
