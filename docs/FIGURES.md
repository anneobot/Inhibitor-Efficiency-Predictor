# Figures

All twenty-five figures from run `run_20260923_134752`, under their archive filenames, with
the figure number each carries in the thesis.

Figures are held once, under the name the pipeline wrote. Chapter Three presents all
twenty-five; Chapter Four re-presents fifteen of them under its own numbering. Both columns
are given so a reader of either chapter can find the file.

| File (`figures/`) | Ch. 3 | Ch. 4 | Caption |
|---|---|---|---|
| `fig_framework.png` | 3.1 | — | The revised modelling framework: the flow from three source databases through harmonisation, pH recovery, representation building and partitioning to five model families, and onward to the evaluation, interpretation and deployment layers. |
| `fig04_pipeline_architecture.png` | 3.2 | — | Pipeline architecture: the sequence of processing operations applied to each record, with the row counts surviving each stage. |
| `fig01_target_distributions_raw.png` | 3.3 | — | Distribution of reported inhibition efficiency in each source database **before** harmonisation, showing the differing scales and the concentration of values in the upper part of the range. |
| `fig02_missingness_inh1368.png` | 3.4 | — | Missingness map for the Inhibitor 1368 dataset: which quantum-chemical descriptor fields were populated and which were absent. |
| `fig03_target_distribution_harmonised.png` | 3.5 | — | Harmonised target distribution across the assembled corpus, with the four retained metals shown separately. |
| `fig_ph_validation.png` | 3.6 | — | Validation of the pH derivation. **A** derived against reported value on the 848 records carrying both. **B** distribution of the signed difference. **C** coverage gained in each source. |
| `fig_corpus_assembly.png` | 3.7 | — | Assembly of the corpus. **A** molecule overlap between the three sources. **B** row count surviving each processing stage. **C** contribution of each source. |
| `fig_condition_coverage.png` | 3.8 | — | Condition coverage across the corpus. Upper: joint distribution of chemical medium against base metal, and of measurement technique against base metal. Lower: mean inhibition efficiency within each regime. |
| `fig05_mutual_information.png` | 3.9 | — | Mutual information between each descriptor and inhibition efficiency, for the forty highest-ranking descriptors. |
| `fig06_descriptor_correlation.png` | 3.10 | — | Pairwise Pearson correlation among the highest-ranking descriptors, showing the collinear families within the descriptor set. |
| `fig_split_leakage.png` | 3.11 | **4.1** | Structural leakage by partitioning scheme. **A** percentage of validation molecules already present in training, per fold. **B** number of distinct validation molecules each scheme places in a fold. |
| `fig_benchmark.png` | 3.12 | **4.2** | Unified benchmark: mean R² for every model under each partitioning scheme, with error bars showing the fold-to-fold standard deviation. |
| `fig_parity_grid.png` | 3.13 | **4.3** | Predicted against observed inhibition efficiency for every model, on out-of-fold predictions under the grouped scheme, with the line of identity shown. |
| `fig_pred_vs_actual.png` | 3.14 | **4.4** | Predicted against observed values for the leading model, with the distribution of residuals. |
| `fig_context_contribution.png` | 3.15 | **4.5** | Contribution of the experimental conditions: explained variance for structure-only against structure-with-conditions, under both honest schemes. |
| `fig_ablation.png` | 3.16 | **4.6** | Cumulative ablation over the feature blocks, showing explained variance at each step and the marginal contribution of each block under both honest schemes. |
| `fig_quantum_ablation.png` | 3.17 | **4.7** | Effect of the quantum-chemical descriptor block, evaluated on the 2,895-row supporting subset. |
| `fig_bias_imbalance.png` | 3.19 | **4.8** | Imbalance and group-wise bias. Upper: distribution of rows across metals, media and methods. Lower: mean signed residual within each group. |
| `fig10_conformal_intervals.png` | 3.18 | **4.9** | Conformal prediction intervals at a nominal coverage of ninety per cent. Molecules ordered by predicted efficiency; the band gives the interval and the points the observed values. **⚠ See the note below — this figure plots a superseded calibration.** |
| `fig_noise_floor.png` | 3.20 | **4.10** | Replicate spread within condition-matched groups, with the model's mean absolute error shown against the reproducibility floor of the measurement. |
| `fig07_shap_summary.png` | 3.21 | **4.11** | Shapley additive explanation summary for the tuned model, showing the twenty most influential features and the direction of their effect. |
| `fig08_ig_atom_saliency.png` | 3.22 | **4.12** | Integrated-gradient atom-level saliency for representative inhibitor molecules under the message-passing network. |
| `fig09_attention_rollout.png` | 3.23 | **4.13** | Attention rollout for the fine-tuned chemistry transformer over the SMILES string. |
| `fig_kinetics.png` | 3.24 | **4.14** | Dose response and adsorption behaviour. **A** pooled relationship. **B** relationship conditioned on substrate. **C** Langmuir linearisation. **D** Arrhenius representation. |
| `fig_published_reproduction.png` | 3.25 | **4.15** | Reproduction of a published protocol. **A** reproduced result against published result. **B** the same model and data re-evaluated under molecule-grouped cross-validation. |

---

## ⚠ Correction to `fig10_conformal_intervals.png`

**This figure plots a conformal interval calibrated on a row-wise partition, and the band it
shows is less than half the honest width.**

The cell that produced it drew its calibration set by permuting rows at random. Because almost
every molecule in the corpus appears several times under different conditions, that
calibration set shares molecules with the fitting set, and the resulting interval — ±18.67
points at 97.4 % empirical coverage — is too narrow for the question the model is asked.

Recalibrated on a partition disjoint **at the level of the molecule**, the 90 % interval is
**±38.6 points at 92.6 % empirical coverage**. That is the figure quoted throughout this
repository, reported in the thesis, and returned by the deployed service.

The figure is retained unaltered because it is what the archived run produced, and altering an
archived artefact would break the provenance chain the manifest exists to protect. It should
not be read as the model's calibration. See [`LIMITATIONS.md`](LIMITATIONS.md) §1.

---

## Notes

**Numbering.** Chapter Four orders its figures by the section that discusses them, which is why
`fig_bias_imbalance.png` is Figure 3.19 but Figure 4.8, and `fig10_conformal_intervals.png` is
Figure 3.18 but Figure 4.9. The file is the same in both cases.

**The two attribution figures** — `fig08_ig_atom_saliency.png` and
`fig09_attention_rollout.png` — were written to `attributions/` in the run archive rather than
to `figures/`. They are held alongside the rest here; `provenance/manifest.json` records their
original paths.

**Reuse.** Figures are licensed [CC BY 4.0](../LICENSE-DATA). Please cite the thesis — see the
repository [README](../README.md).
