# Model

The feature contract and the reference predictor. **No fitted weights are published in this
repository.**

| File | What it is |
|---|---|
| `contract.json` | The authoritative 283-column feature specification, the category vocabularies, the condition medians and the conformal calibration |
| `predict.py` | The reference predictor exported with the deployment bundle |

---

## No weights here

The fitted artefacts — the serialised forest, the scaler, the descriptor imputer and the four
categorical encoders — are **not included**. The run's `tuned_classical.joblib` is 124 MB,
above GitHub's 100 MB file limit, and publishing model binaries was not within the scope
chosen for this repository.

What is published is enough to **audit** the model completely: the exact feature vector it
consumes, in order, with every category vocabulary and every imputation value, plus the
reference code that assembles it.

To obtain a prediction:

- **Use the service** at [inhibiepredict.com](http://inhibiepredict.com), which serves this
  exact model and returns the point estimate, the conformal interval, an
  applicability-domain verdict and a per-prediction feature attribution.
- **Refit from the archive.** `data/master_table.csv` and `data/fold_indices.npy` are
  published, and `docs/MODELS.md` gives the configuration — a random forest of 250 trees at
  maximum depth 31. Rebuilding the descriptor matrix is notebook §3.5.
- **Request the artefacts** from the author for verification purposes.

---

## `contract.json`

| Key | Contents |
|---|---|
| `model_name` | the served estimator |
| `hyperparameters` | `n_estimators: 250`, `max_depth: 31` |
| `n_features` | `283` |
| **`feature_names`** | **the 283 column names, in order — the single source of truth** |
| `descriptor_names_all` | all 217 RDKit descriptors as computed |
| `descriptor_names_kept` | the 211 surviving the zero-variance filter |
| `condition_numeric_names` | the seven numeric conditions |
| `condition_numeric_medians` | the training-fold medians used for imputation |
| `block_layout` | where each block begins and ends |
| `categories` | the fitted vocabularies for metal, alloy, methodology and pH provenance |
| `conformal` | `alpha: 0.1`, `half_width: 38.61`, `empirical_coverage: 0.9258` |
| `training` | rows, molecules, target, seed, build timestamp, library versions, source run |
| `applicability_domain` | the thresholds behind the per-request verdict |
| `honest_performance_grouped_by_molecule` | the figures the service is permitted to quote |

### The feature vector

| Block | Columns | Contents |
|---|---|---|
| Physicochemical descriptors | 211 | of 217 RDKit descriptors; six zero-variance |
| Numeric conditions | 7 | `temperature_K`, `inv_T`, `duration_h`, `log10_duration_h`, `log10_conc_mM`, `pH`, `log10_salt_M` |
| Was-missing indicators | 7 | one per numeric condition |
| Base metal | 4 | `Al`, `Cu`, `Fe`, `Mg` |
| Alloy designation | 38 | grades with ≥ 30 corpus rows; remainder `other_alloy` |
| Measurement methodology | 11 | techniques with ≥ 25 rows; remainder `other_method` |
| pH provenance | 4 | `banded`, `derived`, `measured`, `missing` |
| Synergist | 1 | binary |

```python
import json
c = json.load(open("model/contract.json"))
assert len(c["feature_names"]) == c["n_features"] == 283
print(c["conformal"])     # {'alpha': 0.1, 'half_width': 38.61, 'empirical_coverage': 0.9258}
print(c["training"])      # source_run: run_20260923_134752, seed: 42
```

---

## Four things that will bite anyone rebuilding this

**1. Column order comes from `feature_names`, never from an offset written in code.** A
feature vector built one column out of step **raises nothing**. The forest returns a
confident, wrong number. Build the vector by name and assert its width.

**2. Out-of-vocabulary categoricals must be pooled, not zeroed.** The encoders were fitted
with `handle_unknown="ignore"`, so an unrecognised alloy silently becomes an all-zero block
and yields a confident prediction with nothing to warn on. Training pooled thin-support grades
into `other_alloy` and thin-support techniques into `other_method`, and an unknown value at
inference must be routed the same way. `predict.py` as exported does **not** do this; the
served implementation does, and the two diverge by up to 14 efficiency points on the small
fraction of inputs it affects.

**3. The imputer sees all 217 descriptors, then the variance mask selects 211.** In that
order, and **even when nothing is missing** — the imputer was fitted on 217 columns, and
transforming a 211-wide array through it would not fail loudly.

**4. The library pins are load-bearing.** `contract.json → training` records
`sklearn_version: 1.8.0` and `numpy_version: 2.4.4` for the serialised artefacts, against the
notebook's 1.6.1 and 2.0.2 — same run, different serialisation environment. Unpickling across
a minor version is not guaranteed. Descriptors require **RDKit 2026.03.6**: definitions change
between releases, descriptors are resolved by name, nothing raises, and predictions simply
drift.

Clipping floors are applied **before** each logarithm — a zero concentration would otherwise
become negative infinity.

---

## `predict.py`

The reference predictor as exported with the deployment bundle, published so the featurisation
path is readable rather than described. It expects the fitted artefacts alongside it, which
are not in this repository, so it will not run as-is.

Two differences from the served implementation are worth knowing:

- it does not pool out-of-vocabulary categoricals (point 2 above);
- it computes descriptors from the SMILES as supplied rather than from the canonical,
  salt-stripped form, so it agrees with the training path only on input that is already
  canonical.

---

## Performance this model is entitled to claim

| Scheme | R² | MAE | Applies to |
|---|---|---|---|
| **Grouped by molecule** | **0.461** | **15.65** | a compound absent from training |
| **Scaffold** | **0.398** | 17.32 | a compound whose Bemis–Murcko framework is absent too |
| Row-wise | 0.817 | 7.77 | **nothing — a leakage control, 94.5 % of its test molecules were in training** |

Every prediction carries a **90 % conformal interval of ±38.6 efficiency points** at 92.6 %
empirical coverage. Two independent laboratory measurements of the same experiment differ by
about **8.8** points, so the model's error is 1.77× the reproducibility floor of the data it
learned from.

Subgroups where it should not be trusted are named in
[`../docs/LIMITATIONS.md`](../docs/LIMITATIONS.md) §6.
