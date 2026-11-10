# Reproducibility

The environment, the controls, what can be recomputed from this repository, and three errata
in the notebook's own narrative.

---

## 1. The run

Everything in this repository comes from a single pipeline execution, archived as
**`run_20260923_134752`**. Fifteen model configurations were trained and evaluated on
identical cross-validation folds with identical inputs, in one session of approximately six
hours.

Every execution of the pipeline creates a timestamped run directory with subdirectories for
data, figures, models, metrics, attributions and logs, together with a machine-readable
manifest recording every artefact written, its type and a note describing its provenance.
That manifest is published here as
[`../provenance/manifest.json`](../provenance/manifest.json).

---

## 2. Environment

Recorded **programmatically at run time** rather than transcribed afterwards, so the reported
results carry their own environment record. Published verbatim as
[`../provenance/runtime_spec.json`](../provenance/runtime_spec.json).

### Hardware

| Component | Specification |
|---|---|
| Platform | Kaggle Notebooks, accelerated session |
| Graphics processors | 2 × NVIDIA Tesla T4, 15.6 GB each, compute capability 7.5, 40 SMs |
| Graphics driver | 580.159.04 |
| Logical processor cores | 4 |
| System memory | 33.7 GB total, 31.8 GB available |
| Operating system | Linux 6.12.90, x86_64, glibc 2.35 |
| Total session wall time | approximately 6 hours for the complete pipeline |

Kaggle was selected because the institutional computing facility available to the researchers
provided no graphics hardware, and because the sustained training time required by the graph
and transformer models exceeded the free-tier allowance of comparable notebook services.

### Software

| Package | Version | Role |
|---|---|---|
| Python | 3.12.13 | the entire pipeline |
| RDKit | 2026.03.6 | canonicalisation, descriptors, fingerprints, scaffold decomposition |
| NumPy | 2.0.2 | numerical arrays |
| pandas | 2.3.3 | tabular handling, harmonisation, deduplication |
| SciPy | 1.16.3 | statistics and the Wilcoxon signed-rank test |
| scikit-learn | 1.6.1 | classical estimators, preprocessing, CV utilities, metrics |
| XGBoost | 3.2.0 | extreme gradient boosting |
| PyTorch | 2.10.0 + CUDA 12.8 | tensor computation and network training |
| PyTorch Geometric | 2.8.0 | graph layers and batched graph loading |
| Transformers | 5.0.0 | loading and fine-tuning ChemBERTa |
| Optuna | 4.9.0 | Bayesian hyperparameter optimisation |
| SHAP | 0.51.0 | Shapley additive explanation values |
| Matplotlib | 3.10.0 | figure generation |
| seaborn | 0.13.2 | statistical graphics |
| cuDNN | 9.10.02 | accelerated network primitives |

> **The RDKit pin is load-bearing, not cosmetic.** Descriptor definitions change between
> releases — `NumHAcceptors`, for one, changed definition in an earlier version — and
> descriptors are resolved by name, so nothing raises when a definition shifts. The
> predictions simply drift. Reproduce with 2026.03.6.

> **The served artefacts were serialised under a different scikit-learn.** The deployment
> bundle records `sklearn_version: 1.8.0` and `numpy_version: 2.4.4` in
> [`../model/contract.json`](../model/contract.json) → `training`, against the notebook's
> 1.6.1 and 2.0.2. Same run and same fitted model; different serialisation environment.
> Unpickling an estimator across a minor version is not guaranteed, so a consumer of the
> fitted artefacts should match 1.8.0.

---

## 3. Reproducibility controls

Four controls were applied.

1. **A single global random seed of 42** was set for Python, NumPy and PyTorch at the start of
   the run, and every stochastic estimator was seeded from it.
2. **Fold indices were generated once and saved to disk**, then read by every model in the
   study, so every model was scored on identical rows. Published as
   [`../data/fold_indices.npy`](../data/fold_indices.npy).
3. **Library versions were recorded programmatically at run time**, not transcribed
   afterwards.
4. **All preprocessing that learns from data was confined within the training fold** — the
   median imputer, the zero-variance filter, the categorical encoder and the standard scaler
   were each fitted on the training partition and applied without refitting to the
   corresponding validation partition.

Because the fold indices are saved, any result can be recomputed on exactly the rows that
produced it. Because the preprocessing audit is saved, any individual prediction can be traced
back to its source record and to every transformation applied to it. **This is traceability by
construction rather than by assertion.**

A caveat that belongs here: **all results use a single seed.** Repeating the pipeline across
several seeds would give confidence intervals on the fold-to-fold spread reported alongside
every mean. That has not been done.

---

## 4. What you can reproduce from this repository alone

### Without running anything

The notebook is published **exactly as executed, with all stored outputs**, so every figure
and table can be traced to the cell that produced it.

```bash
git clone https://github.com/anneobot/Inhibitor-Efficiency-Predictor.git
cd Inhibitor-Efficiency-Predictor
jupyter lab notebook/corrosion-inhibitor-efficiency-qspr.ipynb
```

### From the archived metrics

Every table in [`RESULTS.md`](RESULTS.md) is recomputable from `metrics/`:

```python
import pandas as pd

bench = pd.read_csv("metrics/benchmark_full.csv").drop_duplicates()
grouped = (bench[bench.split == "grouped_molecule"]
           .sort_values("r2", ascending=False))
print(grouped[["model", "family", "r2", "r2_std", "rmse", "mae", "spearman"]])

# the leakage measurement
leak = pd.read_csv("metrics/split_leakage_audit.csv")
print(leak.groupby("scheme").pct_seen.mean())
```

> `benchmark_full.csv` is the run's append-only ledger and **contains repeated rows** — the
> row-wise entries for `ridge` and `random_forest` appear more than once with identical
> values. Call `.drop_duplicates()` as above. The file is shipped unaltered because it is the
> archived artefact.

### From the corpus

```python
import pandas as pd

m = pd.read_csv("data/master_table.csv")
print(m.shape)                                  # (8393, 17)
corpus = m[m.metal.isin(["Fe", "Al", "Mg", "Cu"])]
print(corpus.shape)                             # the 8,359-row modelling corpus
print(corpus.canonical_smiles.nunique())        # distinct structures
print(corpus.ph_source.value_counts())          # pH provenance
```

### Rebuilding the feature matrix

The descriptor and fingerprint arrays are not published — `fingerprints.npy` exceeds GitHub's
file-size limit and both are deterministic functions of `canonical_smiles` under the pinned
RDKit. Regenerate them with Section 3.5 of the notebook. The resulting 283-column layout must
match [`../model/contract.json`](../model/contract.json) → `feature_names` **exactly, in
order**; a vector built one column out of step raises nothing and returns a confident wrong
number.

### Re-running the pipeline end to end

Needs an accelerated session with two T4-class GPUs, about six hours, and the three source
exports, which are **not redistributed here**. Obtain them from the databases cited in
[`DATA.md`](DATA.md). Cell 1.4 of the notebook searches a list of candidate directories for
the three CSVs; point it at wherever you place them.

---

## 5. Errata in the notebook's narrative

The notebook is published verbatim. Three statements in its original prose were already out of
date when the run finished. They are corrected here and in a clearly-marked erratum cell at
the top of the notebook rather than silently edited in place, so that what was executed and
what is now known remain distinguishable.

### 5.1 pH is a model feature in this run

The notebook's title cell states that *"pH is retained for analysis but excluded from
training… it never enters any feature matrix, by design."* The same claim appears in the
`NOTE:` of Cell 3.6 and in the `Reminder:` printed by Cell 5.1.

**All three describe the previous iteration of the pipeline.** In this run pH is column 6 of
the 283-column matrix and carries its own four-column provenance block. Section 3.1b derives
it from the recorded aggressive medium, raising availability from 21.8 % to 99.5 %; Section 10
ablates it explicitly. The same run's own output contradicts the comments.

Its measured marginal contribution is **−0.005** explained variance, so the honest statement
is that pH and its provenance are carried **for transparency about how each value was
established, not for predictive gain**.

### 5.2 The conformal interval printed by Cell 9.3 is superseded

Cell 9.3 draws its calibration set with `rng.permutation(len(y))` — a row-wise partition — and
prints a half width of 18.67 points at 97.4 % empirical coverage. Chapter Three describes the
calibration partition as disjoint from the training partition *at the level of the molecule*;
the code does not do that.

Because almost every molecule appears several times in the corpus, a row-wise calibration set
shares molecules with the fitting set, and the interval it yields is **less than half the
honest width**. Recalibrated on a molecule-disjoint partition, the 90 % interval is **±38.6
points at 92.6 % empirical coverage**.

The wider figure is what the thesis reports, what the deployed service returns, and what this
repository quotes throughout. `figures/fig10_conformal_intervals.png` plots the superseded
version. See [`LIMITATIONS.md`](LIMITATIONS.md) §1.

### 5.3 Nested cross-validation was implemented but not executed

Cell 6.6b contains the nested cross-validation procedure and was left unrun: its cost, about
three hours of additional accelerated compute on top of the six-hour pipeline, exceeded the
session allowance.

**The tuned figures are therefore optimistic by an unmeasured margin.** The untuned benchmark
figures, unaffected because no selection was performed against them, carry the principal
comparative conclusions. See [`METHODS.md`](METHODS.md) §5.

---

## 6. Counts that differ between sources

Small discrepancies exist between the notebook's printed summary and the written chapters.
None affects a reported result; they are listed so a reader who notices one is not left
wondering.

| Quantity | Notebook summary | Chapters | Resolution |
|---|---|---|---|
| Distinct molecules | 1,050 | 1,053 | 1,053 after deduplication; **1,050** after scoping to four metals |
| Alloy designations | 76 | 77 | 77 recorded; **38 encoded individually**, remainder pooled |
| Measurement techniques | 13 | 11 | 13 labels present; **11 encoded**, the thinnest pooled into `other_method` |
| Corpus rows | 8,359 | 8,359 | agree — from 8,393 deduplicated, less 33 zinc rows and one unresolved |

---

## 7. Provenance of the published files

| File | Origin in the run archive |
|---|---|
| `notebook/corrosion-inhibitor-efficiency-qspr.ipynb` | the executed notebook, plus one erratum cell |

**The two changes made to the published notebook**, both recorded here so that what was
executed and what is published remain distinguishable:

1. A markdown **erratum cell was prepended**, carrying the three corrections in §5 above. No
   existing cell was altered and all 131 stored outputs are intact.
2. **One unused candidate search path was removed** from the list in Cell 1.4. It pointed at a
   local directory on a machine unrelated to the training run, was never the directory the
   source files were found in, and has no effect on execution — Cell 1.4 simply has one fewer
   location to check before resolving the three CSVs under `/kaggle/input`.

No code that computes a result was changed.

| `data/master_table.csv` | `data/master_table.csv` |
| `data/fold_indices.npy` | `data/fold_indices.npy` |
| `data/descriptor_names.json` | `data/descriptor_names.json` |
| `data/preprocessing_audit.csv` | `data/preprocessing_audit.csv` |
| `metrics/*.csv`, `metrics/classical_tuning.json` | `metrics/` |
| `figures/*.png` | `figures/` and `attributions/` |
| `model/contract.json`, `model/predict.py` | the deployment bundle exported from this run |
| `provenance/manifest.json` | `manifest.json` |
| `provenance/runtime_spec.json` | `logs/runtime_spec.json` |

**Not published:** `models/tuned_classical.joblib` (124 MB) and `models/scaler.joblib`, the
fitted artefacts; `data/descriptors.npy` (14 MB) and `data/fingerprints.npy` (131 MB), both
regenerable. See [`../model/README.md`](../model/README.md).
