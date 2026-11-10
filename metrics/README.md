# Metrics

Every result table written by run `run_20260923_134752`, unaltered. The narrative reading of
these files is [`../docs/RESULTS.md`](../docs/RESULTS.md).

| File | Contents |
|---|---|
| `benchmark_full.csv` | **The leaderboard.** Every model × every scheme × five metrics, with fold-to-fold SD |
| `final_results.csv` | The same ledger as written at the end of the run |
| `classical_results.csv` | Classical estimators only, retained from the earlier pipeline section |
| `leaderboard.csv` | The consolidated view used to build Table 2 |
| `significance.csv` | Pairwise Wilcoxon signed-rank tests on out-of-fold absolute errors |
| `ablation.csv` | Cumulative ablation over the six feature blocks, both honest schemes |
| `quantum_ablation.csv` | The DFT block, evaluated on its own 2,895-row support |
| `split_leakage_audit.csv` | Per-fold molecule overlap under each scheme — **the central measurement** |
| `performance_by_metal.csv` | Disaggregation by base metal |
| `performance_by_alloy.csv` | Disaggregation by alloy designation |
| `performance_by_medium.csv` | Disaggregation by chemical regime |
| `performance_by_method.csv` | Disaggregation by measurement technique |
| `feature_importance.csv` | Mutual information and ensemble importance per descriptor |
| `predicted_vs_actual.csv` | Out-of-fold predictions against observed values |
| `published_reproduction.csv` | Reproduction of Gong et al. (2024), and its regrouping |
| `literature_comparison.csv` | This study beside published work, protocol by protocol |
| `classical_tuning.json` | The Optuna search outcome for the deployed configuration |

---

## ⚠ `benchmark_full.csv` contains repeated rows

The results ledger is append-only, and some models were scored more than once during the run.
The row-wise entries for `ridge` and `random_forest` appear more than once **with identical
values**. No number is affected, but any aggregation must deduplicate first:

```python
import pandas as pd
bench = pd.read_csv("metrics/benchmark_full.csv").drop_duplicates()
```

The file ships unaltered because it is the archived artefact and
[`../provenance/manifest.json`](../provenance/manifest.json) records its hash. Editing it
would break that chain for no gain.

---

## Reading the leaderboard

```python
import pandas as pd

bench = pd.read_csv("metrics/benchmark_full.csv").drop_duplicates()

# The headline: performance on molecules never seen in training
print(bench[bench.split == "grouped_molecule"]
      .sort_values("r2", ascending=False)
      [["model", "family", "representation", "r2", "r2_std", "rmse", "mae", "spearman"]]
      .to_string(index=False))
```

**`split` takes three values.**

| Value | Meaning |
|---|---|
| `naive_row` | The row-wise **control**. Not a valid estimate of predictive skill |
| `grouped_molecule` | Performance on a molecule absent from training. **The headline** |
| `scaffold` | Performance on a Bemis–Murcko framework absent from training |

**`naive_row` scores are not performance claims.** 94.5 % of the molecules in each row-wise
validation fold had already been seen in training — see `split_leakage_audit.csv`. The
row-wise column exists to measure how much that convention overstates the outcome, which it
does by a mean of 0.310 R² across twelve models.

```python
# What the convention costs
leak = pd.read_csv("metrics/split_leakage_audit.csv")
print(leak.groupby("scheme").pct_seen.agg(["mean", "min", "max"]))
```

---

## Conventions across these files

- **R² is reported as explained variance, never as accuracy.** Accuracy is a classification
  quantity; this is regression on a continuous response.
- **RMSE and MAE are in percentage points of inhibition efficiency**, so they are directly
  interpretable against the 0–100 target and against the 8.8-point measurement reproducibility
  floor.
- **Every mean carries its fold-to-fold standard deviation** (`*_std`). A mean R² without its
  spread conceals whether an ordering is stable or an artefact of one favourable fold. The
  0.003 separating the top two models is smaller than either model's SD.
- **`bias` in the `performance_by_*` files is the mean signed residual**, positive where the
  model over-predicts. It is the diagnostic for systematic displacement, as distinct from
  error magnitude.
- A **negative R²** means the model predicts that subgroup worse than the training-fold mean
  would. Several subgroups do; they are named in [`../docs/LIMITATIONS.md`](../docs/LIMITATIONS.md) §6.

---

## What is not in these files

**The conformal interval.** The half width printed by the run's Cell 9.3 — ±18.67 points at
97.4 % coverage — was calibrated on a row-wise partition and is superseded. The honest,
molecule-disjoint figure is **±38.6 points at 92.6 % empirical coverage**, recorded in
[`../model/contract.json`](../model/contract.json) → `conformal`. See
[`../docs/LIMITATIONS.md`](../docs/LIMITATIONS.md) §1.

**Nested cross-validation results.** The procedure was implemented but not executed, so every
figure attributed to the *tuned* model is optimistic by an unmeasured margin. The untuned
benchmark in `benchmark_full.csv` is unaffected and carries the comparative conclusions.
