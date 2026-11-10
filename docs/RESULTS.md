# Results

Every result from run `run_20260923_134752`, with the archive file each is drawn from.

**Reading convention.** Each model was scored under three partitioning schemes, and the three
answer different questions. The **row-wise** scheme is an experimental control; its scores are
reported but are not valid estimates of predictive skill, for the reason established in §1.
The **grouped-by-molecule** scheme answers how a model performs on a compound it has never
seen, and carries the headline results. The **scaffold** scheme answers the stricter question
of how it performs on a chemical family it has never seen.

---

## 1. Quantification of information leakage

The first result concerns the evaluation protocol rather than any model, because it determines
how every subsequent number is to be interpreted.

**Table 1. Structural overlap between training and validation partitions**

| Scheme | Validation rows | Distinct validation molecules | Already seen in training | % seen |
|---|---|---|---|---|
| Row-wise (control) | 1,671.8 | 670.0 | 633.0 | **94.5** |
| Grouped by molecule | 1,671.8 | 210.0 | 0.0 | 0.0 |
| Scaffold | 1,671.8 | 210.0 | 0.0 | 0.0 |

Means across five folds. Per-fold values under the row-wise scheme range from 93.3 % to
96.0 %. *(`metrics/split_leakage_audit.csv`)*

The consequence is direct. **A score obtained under the row-wise scheme substantially measures
the recall of memorised structures rather than the prediction of unmeasured ones**, and it
does not answer the question a corrosion scientist brings to such a model.

Because the same models were run under all three schemes, the size of the effect can be
measured rather than merely asserted. Across the twelve models evaluated under both, moving
from the row-wise control to the grouped scheme **reduced R² by a mean of 0.310**. The
reduction was not uniform: largest for the feedforward network at 0.461 and the H2 hybrid at
0.380, smallest for the SVR at 0.206 and the fine-tuned transformer at 0.208. **Models that
lost the most were those best able to memorise a molecule from its descriptor vector.**

*Figure: `figures/fig_split_leakage.png`*

---

## 2. The unified benchmark

**Table 2. Coefficient of determination by model and partitioning scheme**

| Family | Model | Row-wise (control) | **Grouped by molecule** | Scaffold |
|---|---|---|---|---|
| Classical | XGBoost | 0.812 | **0.464** | 0.398 |
| Classical | Random forest | 0.817 | **0.461** | 0.398 |
| Hybrid | H1, graph encoder → boosting | 0.774 | **0.451** | 0.247 |
| Classical | Gradient boosting | 0.679 | 0.443 | 0.331 |
| Classical | SVR (RBF) | 0.617 | 0.411 | 0.323 |
| Hybrid | H2, transformer embedding → boosting | 0.791 | 0.411 | 0.350 |
| Transformer | ChemBERTa, fine-tuned | 0.572 | 0.364 | 0.253 |
| Graph | GAT with condition fusion | 0.624 | 0.362 | 0.109 |
| Hybrid | H3, three-branch fusion | 0.663 | 0.337 | 0.155 |
| Graph | MPNN with condition fusion | 0.670 | 0.335 | 0.057 |
| Neural | Feedforward MLP | 0.764 | 0.303 | 0.094 |
| Classical | Ridge | 0.534 | 0.256 | −0.407 |
| Classical | Random forest, structure only | not run | 0.167 | 0.107 |
| Classical | XGBoost, structure only | not run | 0.153 | 0.105 |
| Baseline | Mean predictor | −0.000 | −0.014 | −0.071 |

*(`metrics/benchmark_full.csv`)*

**Table 3. Full metrics on the grouped-by-molecule scheme**

| Model | R² | SD across folds | RMSE | MAE | Spearman ρ |
|---|---|---|---|---|---|
| XGBoost | 0.464 | 0.125 | 21.42 | 15.67 | 0.685 |
| Random forest | 0.461 | 0.157 | 21.45 | 15.65 | 0.687 |
| H1, graph encoder → boosting | 0.451 | 0.082 | 21.72 | 15.83 | 0.689 |
| Gradient boosting | 0.443 | 0.094 | 21.89 | 16.58 | 0.659 |
| SVR (RBF) | 0.411 | 0.104 | 22.49 | 16.50 | 0.645 |
| H2, transformer embedding → boosting | 0.411 | 0.138 | 22.43 | 16.82 | 0.641 |
| ChemBERTa, fine-tuned | 0.364 | 0.077 | 23.40 | 17.22 | 0.637 |
| GAT with condition fusion | 0.362 | 0.087 | 23.39 | 16.81 | 0.640 |

RMSE and MAE are in percentage points of inhibition efficiency.

### Three observations

**Tree ensembles led on the honest scheme.** XGBoost and the random forest reached 0.464 and
0.461, explaining approximately forty-six per cent of the variance for molecules the models
had never seen. This is consistent with the data regime: a heterogeneous tabular matrix of 283
columns mixing continuous physical quantities, logarithmic transforms, binary indicators and
high-cardinality categorical encodings, across 8,359 rows. Tree ensembles are close to optimal
there; the deep architectures are not, because they require substantially more data to learn
representations the descriptor set already supplies.

**The ordering changes between schemes.** Under the row-wise control the random forest leads
at 0.817 with the feedforward network fifth at 0.764. Under grouping the feedforward network
falls to eleventh at 0.303. **A leaderboard built on the row-wise scheme would have
recommended a different model** — the practical consequence of §1.

**The scaffold column exposes a distinction the grouped column does not.** The graph networks
and the H1 hybrid, competitive under grouping, degrade sharply when required to generalise to
an unseen chemical framework — the MPNN falls from 0.335 to 0.057. The tree ensembles hold at
0.398. Ridge becomes actively harmful at −0.407, predicting worse than the training-fold mean.

*Figures: `fig_benchmark.png`, `fig_parity_grid.png`, `fig_pred_vs_actual.png`*

---

## 3. Statistical significance of the ranking

A leaderboard produces an ordering whether or not the ordering is meaningful.

**Table 4. Paired comparison of absolute errors, grouped scheme**

| Model A | Model B | MAE A | MAE B | p | Significant at 0.05 |
|---|---|---|---|---|---|
| XGBoost | Random forest | 15.67 | 15.65 | 0.201 | No |
| XGBoost | H1 graph → boosting | 15.67 | 15.83 | 0.641 | No |
| Random forest | H1 graph → boosting | 15.65 | 15.83 | 0.725 | No |
| XGBoost | Gradient boosting | 15.67 | 16.58 | < 0.001 | **Yes** |
| XGBoost | SVR | 15.67 | 16.50 | < 0.001 | **Yes** |
| XGBoost | H2 transformer → boosting | 15.67 | 16.82 | < 0.001 | **Yes** |
| Random forest | Gradient boosting | 15.65 | 16.58 | < 0.001 | **Yes** |
| H1 graph → boosting | Gradient boosting | 15.83 | 16.58 | < 0.001 | **Yes** |
| Gradient boosting | SVR | 16.58 | 16.50 | 0.507 | No |
| Gradient boosting | H2 transformer → boosting | 16.58 | 16.82 | 0.480 | No |
| SVR | H2 transformer → boosting | 16.50 | 16.82 | 0.113 | No |

Wilcoxon signed-rank on out-of-fold absolute errors. *(`metrics/significance.csv`)*

**The six models resolve into two tiers rather than six ranks.** XGBoost, the random forest
and H1 form a leading tier within which no pair differs significantly. Gradient boosting, the
SVR and H2 form a second, likewise internally indistinguishable. Every cross-tier comparison
is significant at p < 0.001.

**The correct statement is that three models share the lead, not that XGBoost won.** The 0.003
separating XGBoost from the random forest is smaller than the fold-to-fold standard deviation
of either, and reporting it as a ranking would overstate what the data supports.

---

## 4. The contribution of the experimental conditions

The structure-only controls isolate the contribution of the conditions with the estimator, the
folds and the metric held fixed.

**Table 5. Effect of supplying the experimental conditions**

| Scheme | Structure only | Structure with conditions | Gain |
|---|---|---|---|
| Grouped by molecule | 0.167 | 0.461 | **+0.293** |
| Scaffold | 0.107 | 0.398 | **+0.291** |

Random forest in both columns, identical folds, identical metric.

Supplying temperature, exposure duration, inhibitor concentration, pH, substrate and
measurement methodology raised explained variance by 0.293 under grouping and 0.291 under
scaffolding. **The consistency of the gain across two different partitioning schemes indicates
it is attributable to the information and not to an artefact of one partition.**

The magnitude carries a practical implication. **A model given only the molecular structure
explains under seventeen per cent of the variance** — which is to say the molecule alone does
not determine how well it will inhibit. The conditions account for more of the outcome than
the structure does. This is chemically unsurprising, since the same inhibitor at different
concentrations in different acids on different alloys will perform differently, but it has a
consequence for deployment: **a prediction is meaningful only when the service conditions are
specified alongside the structure.**

*Figure: `fig_context_contribution.png`*

### Cumulative ablation

**Table 6. Cumulative ablation, grouped-by-molecule scheme**

| Step | Features | R² | Marginal gain |
|---|---|---|---|
| Structure (descriptors) | 211 | 0.161 | +0.161 |
| + conditions | 226 | 0.395 | **+0.234** |
| + pH provenance | 230 | 0.390 | **−0.005** |
| + substrate | 272 | 0.446 | +0.056 |
| + methodology | 283 | 0.456 | +0.010 |
| + fingerprints | 2,331 | 0.465 | +0.010 |

*(`metrics/ablation.csv`)* The scaffold scheme gives the same ordering, rising from 0.096 to
0.413.

The condition block is by a wide margin the largest single contributor at +0.234, followed by
substrate at +0.056. Methodology adds +0.010 — small, but not negligible given that
measurement technique shifts reported efficiency by tens of points across the corpus.

**Two negative findings are worth stating explicitly.**

The **pH provenance flags contributed −0.005**, indistinguishable from zero. Their inclusion is
justified on grounds of transparency, since they record how each pH value was established,
rather than on predictive grounds.

The **fingerprint block added +0.010 while increasing the feature count from 283 to 2,331**, a
factor of eight. Substructure presence adds almost nothing beyond what the 211 physicochemical
descriptors already encode. The 283-column matrix was accordingly retained as the standard
input and the fingerprint representation was not carried forward.

*Figure: `fig_ablation.png`*

---

## 5. The quantum-chemical descriptors

Evaluated on the 2,895 rows for which they were available — 34.6 % of the corpus — with and
without the quantum block **on identical rows**.

**Table 7. Effect of the quantum-chemical block on its supporting subset**

| Variant | Features | R² | SD across folds | MAE |
|---|---|---|---|---|
| Without quantum | 283 | 0.264 | 0.539 | 10.49 |
| With quantum | 295 | 0.167 | 0.725 | 10.99 |

*(`metrics/quantum_ablation.csv`)*

**Adding the quantum block reduced explained variance by 0.097 and increased the mean absolute
error.** The fold-to-fold standard deviation is large in both variants, reflecting the reduced
sample, so the difference should be read as **an absence of benefit rather than a precisely
measured harm**.

The direction is nonetheless consistent with the source study, whose own random forest falls
from 0.685 on molecular descriptors alone to 0.484 when quantum parameters are added alongside
them. Two plausible explanations exist. The frontier-orbital quantities are strongly correlated
with descriptors already present, so they add collinear columns rather than new information;
and they are computed on the isolated molecule in the gas phase or in an implicit solvent,
which is a poor proxy for the electronic state of a molecule adsorbed on a charged metal
surface in concentrated acid.

Holding the block out of the pooled feature matrix is therefore a defensible modelling
decision rather than a compromise forced by incomplete coverage.

*Figure: `fig_quantum_ablation.png`*

---

## 6. Disaggregated performance and systematic bias

Aggregate scores conceal subgroup failure. The leading model was disaggregated across chemical
regime, base metal, alloy grade and measurement technique, on out-of-fold predictions under
the grouped scheme. **Bias is the mean signed residual, positive where the model
over-predicts.**

**Table 8. Performance by chemical regime** *(`metrics/performance_by_medium.csv`)*

| Regime | n | Mean IE | R² | RMSE | MAE | Bias |
|---|---|---|---|---|---|---|
| Acidic | 4,726 | 72.4 | 0.304 | 18.88 | 12.71 | +1.68 |
| Near-neutral | 3,052 | 48.9 | 0.391 | 25.38 | 20.13 | +0.55 |
| Alkaline | 538 | 42.0 | 0.408 | 20.60 | 16.15 | −3.16 |
| Unknown | 43 | 74.1 | −0.276 | 24.34 | 18.45 | +1.21 |

**Table 9. Performance by base metal** *(`metrics/performance_by_metal.csv`)*

| Metal | n | Mean IE | R² | RMSE | MAE | Bias |
|---|---|---|---|---|---|---|
| Fe | 3,514 | 78.3 | **−0.057** | 19.67 | **12.56** | +2.57 |
| Al | 2,783 | 53.0 | 0.415 | 21.02 | 16.40 | +0.36 |
| Mg | 1,631 | 38.5 | 0.289 | 26.04 | 20.92 | −0.86 |
| Cu | 431 | 73.4 | 0.137 | 21.96 | 16.43 | −1.50 |

**Table 10. Performance by measurement technique** *(`metrics/performance_by_method.csv`)*

| Technique | n | Mean IE | R² | MAE | Bias |
|---|---|---|---|---|---|
| Potentiodynamic polarisation | 1,879 | 76.0 | 0.461 | 10.55 | +0.08 |
| Gravimetric | 1,730 | 62.6 | **−0.045** | 19.78 | +2.86 |
| Hydrogen evolution | 1,710 | 38.1 | 0.273 | 20.61 | −0.72 |
| Not stated | 1,389 | 80.0 | 0.397 | 9.27 | +0.94 |
| Optical | 679 | 33.6 | 0.213 | 15.97 | −3.72 |
| Polarisation resistance | 437 | 69.8 | **−0.085** | 22.12 | +5.86 |
| Impedance spectroscopy | 236 | 71.2 | 0.214 | 15.93 | +1.38 |
| Current density | 138 | 72.7 | **−0.421** | 16.31 | +8.13 |
| Frequency modulation | 115 | 56.5 | 0.442 | 14.89 | +9.63 |
| Cyclic voltammetry | 25 | 80.1 | 0.313 | 11.34 | +1.10 |

Alloy-level results are in `metrics/performance_by_alloy.csv`.

### Four findings

**The model is not strongly biased by chemical regime.** Signed residuals are +1.68 in acid,
+0.55 in near-neutral solution and −3.16 in alkali, all small relative to a mean absolute
error of 15.7 points. The concern that a corpus dominated by acid would produce a model
systematically wrong outside acid is not supported on the alkaline records that exist —
explained variance is in fact highest in alkali at 0.408. **Read this with the sample sizes in
view**: 538 alkaline rows against 4,726 acidic. The model is not demonstrably biased against
alkaline conditions, but neither has it been tested there at a scale that would establish
reliability, and the corpus contains no atmospheric or microbiologically influenced corrosion
at all.

**Iron is the notable weakness, and also a lesson in reading R².** Explained variance on iron
is −0.057, meaning the model predicts iron no better than the training-fold mean, despite iron
being the best-supported metal at 3,514 rows. Yet **the mean absolute error on iron is the
lowest of the four metals at 12.56**. The explanation lies in the variance structure rather
than in model failure: iron records carry a high mean efficiency of 78.3 with comparatively
little spread, so there is little variance available to explain, and R² is small even though
the absolute error is small. This is why R² is reported here alongside the error in the units
of the target, and never alone.

**Measurement technique is the strongest axis of variation.** Explained variance ranges from
0.461 on potentiodynamic polarisation to −0.421 on current density, and MAE from 9.27 to
22.12. Two of the larger techniques — gravimetric measurement and polarisation resistance —
return negative explained variance. Gravimetric measurement is the slowest and least
controlled technique in the corpus and carries the widest scatter in the underlying
literature, which places a ceiling on how well any model can predict it. **This vindicates the
decision to carry methodology as a feature rather than average across techniques.**

**A small number of alloy grades show severe bias.** Cold rolled steel (160 rows) is
over-predicted by **30.0** percentage points, stainless steel (48 rows) by **22.5**, and the
designation recorded simply as `Fe` (99 rows) by **16.1**, while the designation recorded as
`Steel` (66 rows) is **under**-predicted by 18.8. These are the grades where the model should
not be trusted, and **their identification is the practical value of the disaggregation**. The
pattern is consistent with sparse support combined with inconsistent labelling in the source
data, where the same physical material may be recorded as *carbon steel* in one publication
and as *Steel* or *Fe* in another.

*Figure: `fig_bias_imbalance.png`*

---

## 7. Calibration of prediction intervals

Split conformal prediction at a nominal ninety per cent level.

| Calibration partition | Half width | Empirical coverage |
|---|---|---|
| **Disjoint by molecule** — the figure this repository quotes | **±38.6 points** | **92.6 %** |
| Row-wise — superseded, see below | ±18.67 points | 97.4 % |

**The molecule-disjoint figure is the one that applies to a new compound**, and it is what the
deployed service returns and what the thesis reports. At ±38.6 points with 92.6 % empirical
coverage against a 90 % nominal level, the interval is **wide but honestly calibrated**.

> **A correction worth stating plainly.** The published run's Cell 9.3 calibrated on a random
> row permutation rather than a molecule-disjoint partition. Because almost every molecule
> appears several times in the corpus, that calibration set shares molecules with the fitting
> set, and the interval it produced — ±18.67 points at 97.4 % coverage — is less than half the
> honest width. The archived figure `figures/fig10_conformal_intervals.png` plots that
> superseded version. See [`LIMITATIONS.md`](LIMITATIONS.md) §1.

For a screening application a wide interval is the preferable direction of error: an interval
that is too narrow gives a user false confidence in a candidate, while one that is too wide
costs only precision. **With a ±38.6-point band, the instrument's value lies in ranking
candidates, not in guaranteeing an efficiency.**

---

## 8. The measurement reproducibility floor

**878 groups of records** were identified in which the molecule, the metal, the alloy and every
experimental condition agreed, so that the only difference within a group is the measurement
itself.

**Table 11. Reproducibility of the underlying measurement**

| Quantity | Value |
|---|---|
| Condition-matched replicate groups | 878 |
| Median within-group standard deviation | 4.32 efficiency points |
| Mean within-group standard deviation | 7.83 efficiency points |
| **Implied mean absolute difference between two independent measurements** | **8.8 efficiency points** |
| Model mean absolute error on unseen molecules | 15.67 efficiency points |
| **Ratio of model error to measurement floor** | **1.77** |

Two independent laboratory measurements of the same inhibitor, on the same metal, in the same
medium, at the same concentration, differ from one another by 8.8 percentage points on
average. **This is the reproducibility of the published experimental record, and no model
trained on that record can be expected to predict it more precisely than it predicts itself.**

The model's error of 15.67 points is therefore **1.77 times the noise floor**, not 15.67 times
some implicit ideal of zero. The remaining headroom is the difference between those two
numbers rather than the whole of the error. This reframes the interpretation of every error
figure in this document, and sets a realistic target for further work: an error approaching
nine points would represent a model performing at the limit of what the data can support.

*Figure: `fig_noise_floor.png`*

---

## 9. Feature importance and interpretation

The fifteen descriptors carrying the highest mutual information with inhibition efficiency
were dominated by two families. **BCUT2D descriptors**, which encode the distribution of
atomic properties weighted by molecular connectivity, occupied the first two positions at
0.630 and 0.621. **Partial-charge descriptors** — the minimum, maximum and absolute partial
charges on any atom — occupied four of the top eleven at approximately 0.61. Chi connectivity
indices, the Labute accessible surface area, molecular weight and the Crippen partition
coefficient completed the ranking. *(`metrics/feature_importance.csv`)*

**This ordering is chemically coherent.** Organic corrosion inhibitors function by adsorbing
onto the metal surface. Adsorption strength depends on the availability of electron density at
specific atoms, which is what the partial-charge descriptors measure, and on the area the
molecule can shield once adsorbed, which is what the surface-area and connectivity descriptors
measure. The partition coefficient enters because it governs partitioning of the molecule
between the bulk electrolyte and the metal interface.

The **Shapley** analysis of the tuned model confirmed this ordering and added directionality,
showing that the contribution of the partial-charge descriptors **changes sign across the
range of the descriptor** rather than acting monotonically. **Integrated-gradient**
attributions on the message-passing network localised the predicted contribution to
heteroatoms and aromatic systems, the recognised anchoring points for inhibitor adsorption.
**Attention rollout** on the fine-tuned transformer showed attention concentrated on
heteroatom tokens within the SMILES string.

**The three methods therefore agree, from three architecturally distinct models, that the
features controlling the prediction are those controlling adsorption. This convergence is the
principal evidence that the models have learned chemistry rather than an artefact of the
corpus.**

*Figures: `fig07_shap_summary.png`, `fig08_ig_atom_saliency.png`, `fig09_attention_rollout.png`*

---

## 10. Kinetics and the shape of the dose response

Within a given substrate the dose response rises steeply at low concentration and saturates,
which is the characteristic **Langmuir** form, and the fitted adsorption equilibrium constant
for iron was of order 10³.

**A confounding effect was identified and is reported because it bears directly on how such
data must be analysed.** Pooled across the whole corpus, inhibition efficiency appears to
*fall* with increasing inhibitor concentration — which is chemically backwards. The cause is
that high concentrations are applied predominantly to the substrate and electrolyte
combinations that resist inhibition, so the substrate confounds the pooled relationship.
**Conditioning on the metal recovers the expected rising and saturating shape.**

This is a concrete demonstration that corrosion inhibition data assembled from heterogeneous
sources cannot be analysed in the aggregate without stratification, and it provides part of
the justification for carrying substrate as an explicit feature rather than pooling across
metals.

Temperature dependence enters through the adsorption equilibrium and therefore follows
Arrhenius behaviour, which is the basis for supplying the reciprocal of absolute temperature
alongside temperature itself.

**Both relationships are non-linear** — the concentration response a saturating isotherm, the
temperature response exponential. A modelling strategy assuming linearity in the untransformed
variables would be misspecified from the outset, which is consistent with Ridge regression,
the only linear model in the benchmark, performing worst under grouping at 0.256 and failing
outright on the scaffold scheme at −0.407.

*Figure: `fig_kinetics.png`*

---

## 11. Reproduction of a published protocol

The protocol reported by the authors of the Inhibitor 1368 dataset was reimplemented on their
own data, using their features, their model family and their evaluation scheme.

**Table 12. Reproduction of a published protocol and its re-evaluation under grouping**

| Protocol | R² | RMSE | MAE |
|---|---|---|---|
| Published figures | 0.6439 | 0.1034 | 0.0708 |
| Reproduced in this study | 0.6570 | 0.1017 | 0.0708 |
| **Same model and data, grouped by molecule** | **0.3787** | 0.1355 | 0.0945 |

Targets are expressed as fractions in this comparison, following the source.
*(`metrics/published_reproduction.csv`)*

The reproduction **matched the published mean absolute error to four decimal places** and the
coefficient of determination to within 0.013, which establishes that the reimplementation is
faithful.

Under the published protocol, **84.9 % of the molecules in each test partition had already
appeared in training**. Regrouping the identical model and identical data by molecule reduced
R² from 0.657 to 0.379 — an inflation of **+0.278** attributable to structural leakage.

> **This is the most consequential result in the study.** The inflation of +0.278, measured on
> a different dataset, with different features, assembled by different authors, closely
> matches the mean inflation of +0.310 measured across the models of this study on its own
> corpus. **Two independent measurements of the same artefact now exist.** Molecule-level
> leakage is therefore a property of the evaluation convention prevailing in this field, not a
> property of any individual pipeline — and comparisons with published figures must be made
> protocol to protocol rather than number to number.

*Figure: `fig_published_reproduction.png`*

---

## 12. Comparison with published work

**Table 13. This study beside the published literature** *(`metrics/literature_comparison.csv`)*

| Study | Target | Corpus | Protocol | Model | R² |
|---|---|---|---|---|---|
| Gong et al. (2024) | IE % | 1,364 rows, 455 molecules, 1 metal | 5-fold, row-wise | Random forest | 0.644 |
| Gong et al. (2024), corrected here | IE % | 1,364 rows, 455 molecules, 1 metal | 5-fold, grouped | Random forest | 0.379 |
| Ekeocha et al. (2024) | IE % | 50 benzimidazoles | Cross-validation | Random forest | 0.512 |
| Ekeocha et al. (2024) | IE % | 50 benzimidazoles | Cross-validation | Gradient boosting | 0.591 |
| Dai et al. (2022) | IE | Inhibitor set | 10-fold, row-wise | Random forest | 0.340 |
| Dai et al. (2022) | IE | Inhibitor set | 10-fold, row-wise | DMPNN (graph) | 0.460 |
| Pham et al. (2024) | IE % | Not stated | Not stated | Ensemble | 0.720 |
| Schwaller et al. (2021) | Yield % | 3,955 plate reactions | 10 × random 70/30 | BERT regression | 0.951 |
| Schwaller et al. (2021) | Yield % | 500,000 patent reactions | Random split | BERT regression | 0.195 |
| Li et al. (2023) | Ratio | 1,558 in-house reactions | 5-fold, random | Communicative MPNN | 0.712 |
| **This study** | IE % | 8,359 rows, 1,050 molecules, 4 metals | 5-fold, row-wise *(control)* | XGBoost | 0.812 |
| **This study** | IE % | 8,359 rows, 1,050 molecules, 4 metals | **5-fold, grouped by molecule** | XGBoost | **0.464** |

**Read naively, the 0.464 obtained here is lower than several published figures and the study
appears to underperform. Read correctly, it is the only figure in the table obtained under a
protocol that excludes the test molecules from training.** The comparable published figures
are those in the row-wise rows, where this study reports 0.812 — higher than every corrosion
inhibition result in the table, and obtained on a corpus six times larger covering four metals
rather than one.

The two entries from reaction-yield prediction are instructive because that field has
encountered the same phenomenon. Schwaller et al. report 0.951 on a clean, systematically
generated high-throughput dataset and 0.195 on messy literature-compiled data **using the
identical architecture**. The corpus assembled for this study is literature-compiled, and its
results sit in the range that the yield-prediction field associates with such data.

---

## 13. Validation against experiment

### 13.1 Laboratory comparison

Two constituents of African Spiral Flag extracts, identified by GC-MS and measured by weight
loss on aluminium in 1 M HCl at 303 K over 10 h of immersion. Inhibition efficiency rose with
extract concentration, reaching 85 % at 1 g/L for the stem and 79 % for the leaf.

| Sample | Principal constituent | Conc. | Experimental IE | Predicted IE | Residual | Absolute error |
|---|---|---|---|---|---|---|
| Stem | (Z)-13-octadecenal (14.39 % of GC-MS total) | 3.75 mM | 85.0 % | 88.1 % | −3.1 | 3.1 |
| Leaf | 11-octadecenoic acid, methyl ester | 3.37 mM | 79.0 % | 86.9 % | −7.9 | 7.9 |

The consistent negative difference indicates the model **over-predicted** in both cases. The
comparison is encouraging as an initial check, because absolute errors of 3.1 and 7.9 points
are smaller than the ≈15.7-point MAE obtained for unseen molecules under grouped validation.
The stem extract, the more effective inhibitor experimentally, was also predicted the more
effective.

> **Two observations cannot establish broad external validity**, quantify prediction-interval
> coverage, or demonstrate that the positive residual represents a persistent model bias. The
> study states this plainly and so does this repository.

### 13.2 Correlation against the published record

Predictions for 30 compounds drawn from published studies, under their reported experimental
conditions:

| Analysis | Coefficient | p | n |
|---|---|---|---|
| Pearson's r | **+0.496** | 0.0053 | 30 |
| Spearman's ρ | **+0.373** | 0.0417 | 30 |

A moderate positive linear and a weak positive monotonic relationship, **both statistically
significant** at α = 0.05.

### 13.3 Correlation with quantum-chemical reactivity

For 20 compounds, frontier-orbital energies were computed by DFT and the HOMO–LUMO gap ΔE
correlated against the model's predicted efficiency:

| Analysis | Coefficient | p | n |
|---|---|---|---|
| Pearson's r | −0.4172 | 0.0672 | 20 |
| Spearman's ρ | −0.3761 | 0.1022 | 20 |

The negative coefficients indicate a general tendency for compounds with smaller ΔE to have
higher predicted efficiency, which is the chemically expected direction. **Neither correlation
is statistically significant at α = 0.05.** The absence of significance means the inverse
relationship should not be interpreted as evidence that ΔE alone determines inhibition
efficiency — which is consistent with the study's central finding that structure-derived
quantities alone, quantum or otherwise, do not determine the outcome.

---

## 14. Summary of findings

**On the evaluation protocol.** Under the row-wise convention used in the corrosion-inhibition
machine-learning literature, 94.5 % of test molecules have already been seen in training.
Correcting this reduces explained variance by a mean of 0.310 across twelve models. The same
correction applied to a published study on its own data reduced its reported figure from 0.657
to 0.379, an inflation of 0.278.

**On model selection.** XGBoost, the random forest and the H1 graph hybrid share the lead at
approximately 0.46 explained variance on unseen molecules, with no statistically significant
difference among them. Tree ensembles outperform graph networks, the fine-tuned transformer
and the feedforward network in this data regime.

**On what drives prediction.** The experimental conditions contribute +0.293 explained variance
over molecular structure alone — more than the structure itself contributes. Substrate adds
+0.056 and methodology +0.010. Structural fingerprints add +0.010 for an eightfold increase in
dimensionality and were not retained. Quantum-chemical descriptors reduced performance on
their supporting subset.

**On reliability.** The model is not strongly biased by chemical regime. It performs poorly on
iron measured by explained variance, though well measured by absolute error, and poorly on
gravimetric and polarisation-resistance measurements. Four sparsely supported alloy
designations show severe over- or under-prediction and should be treated as outside the
working domain. Prediction intervals calibrated disjointly by molecule are ±38.6 points at
92.6 % empirical coverage.

**On the limit of what is achievable.** The measurement itself is reproducible only to 8.8
efficiency points. The model's error of 15.7 points is 1.77 times that floor, which is the
quantity further work should seek to reduce.

**On the chemistry.** Inhibition is non-linear in both concentration and temperature,
following Langmuir adsorption and Arrhenius behaviour respectively. Three independent
interpretation methods applied to three architecturally distinct models converge on partial
charge, molecular surface area and heteroatom position as the controlling features — the
properties that govern adsorption onto a metal surface.
