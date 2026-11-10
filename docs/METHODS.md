# Methods

The pipeline, the representations, the partitioning schemes and the evaluation protocol.

---

## 1. The framework

Seven stages, executed as a linear pipeline.

```
three public databases
        │  load and audit for schema, completeness, internal consistency
        ▼
  harmonisation          units unified, vocabularies controlled, 15-field schema
        │
        ▼
  pH recovery            derived from the recorded medium by solution equilibria,
        │                every value carrying a provenance flag
        ▼
  deduplication          composite key over structure AND conditions → master table
        │
        ▼
  representation         four parallel views of each measurement:
        │                descriptors · fingerprints · graphs · condition block
        ▼
  partitioning           three schemes, fold indices generated once and shared
        │
        ▼
  fifteen models         five families, identical folds, identical inputs
        │
        ▼
  analysis               ablation · bias · calibration · explainability · kinetics
                         → leading model persisted for deployment
```

Data assembly is documented in [`DATA.md`](DATA.md); this document picks up at
representation.

---

## 2. Representations

Four parallel representations of each measurement were constructed, because the model families
compared consume different kinds of input: tree ensembles require a fixed-length numeric
vector, graph networks an explicit connectivity structure, the chemistry transformer a token
sequence. Building all four from the same master table guaranteed they describe the same 8,359
measurements **in the same row order**.

### 2.1 Physicochemical descriptors

**217 descriptors** computed for every canonical structure with the RDKit descriptor
calculator: constitutional (molecular weight, atom counts), topological (the Chi and Kappa
families), electronic and surface (topological polar surface area, Crippen partition
coefficient), and counts of hydrogen-bond donors and acceptors, rotatable bonds, aromatic
rings and heteroatoms.

These are the conventional descriptor basis of corrosion-inhibition QSPR, because inhibitor
adsorption is governed by electron-donating capacity, by the availability of heteroatom lone
pairs and π systems for coordination to the metal surface, and by the molecular area available
to shield that surface.

Three implementation details carry real risk:

- **Descriptors are resolved by name, never by position.** `Descriptors.descList` changes
  length between RDKit releases; positional indexing would silently shift every column.
- **A descriptor that raises becomes NaN and is then imputed.** The BCUT2D family raises on
  molecules RDKit cannot assign Gasteiger charges to. This is caught per descriptor.
- **Descriptors are computed from the canonical, salt-stripped SMILES.** Six of the 217 are
  zero-variance across the corpus and are removed, leaving **211**.

### 2.2 Structural fingerprints

Morgan circular fingerprints of radius 2, folded to **2,048 bits** — the extended-connectivity
representation (Rogers & Hahn, 2010). Fingerprints encode the presence or absence of local
atom environments rather than aggregate physical properties, and were included so the ablation
could establish whether substructure presence adds information beyond the descriptor set. It
does not, materially: see [`RESULTS.md`](RESULTS.md) §4.

### 2.3 Molecular graphs

Each molecule converted to an attributed graph with atoms as nodes and bonds as edges. Node
features span **eighteen dimensions**: element identity over a one-hot vocabulary, degree,
formal charge, hybridisation state, aromaticity, attached-hydrogen count and ring membership.
Edge features span **three**: bond order, aromaticity, ring membership. All 8,359 graph objects
were built once and reused across every graph experiment.

### 2.4 The experimental condition block

**72 features**, constructed from the harmonised fields.

| Group | Count | Contents |
|---|---|---|
| Numeric conditions | 7 | temperature (K), 1/T, duration (h), log₁₀ duration, log₁₀ concentration, pH, log₁₀ salt concentration |
| Missingness indicators | 7 | one binary flag per numeric condition |
| Base metal | 4 | Fe, Al, Mg, Cu |
| Alloy designation | 38 | ≥ 30 supporting rows; remainder pooled |
| Measurement methodology | 11 | after vocabulary control |
| pH provenance | 4 | measured, derived, banded, missing |
| Synergist present | 1 | binary |

**Three numeric conditions are carried in transformed as well as raw form, and the reason is
chemistry rather than convenience.** Temperature is accompanied by its reciprocal, because the
Arrhenius dependence of a rate process is linear in inverse absolute temperature rather than
in temperature. Duration and concentration are accompanied by their base-ten logarithms,
because both span several orders of magnitude in this corpus and because the adsorption
isotherms governing inhibitor coverage are linear in log C. Supplying these transforms
explicitly lets a linear model represent the correct functional form, and shortens the path a
non-linear model must travel to find it.

Clipping floors are applied **before** each logarithm — a zero concentration would otherwise
become negative infinity.

### 2.5 Composite matrices

| Matrix | Columns | Use |
|---|---|---|
| Descriptors alone | 211 | structure-only controls |
| **Descriptors + conditions** | **283** | **the standard input for the flat benchmark** |
| Fingerprints + conditions | 2,120 | ablation only |
| Graph + condition vector | — | fused inside the network (§3.3) |

Six named blocks were defined for the ablation: **structure** (descriptors), **conditions**
(numeric plus indicators), **pH provenance**, **substrate** (metal and alloy), **method**
(methodology encoding) and **quantum** (the DFT parameters available on the Inhibitor 1368
subset).

The column order of the 283-column matrix is recorded in
[`../model/contract.json`](../model/contract.json) → `feature_names` and is the single source
of truth. A feature vector built one column out of step raises nothing; it returns a confident
wrong number.

---

## 3. Models

Fifteen configurations across five families. Every model received the same 283-column matrix,
or its graph or sequence equivalent carrying the **identical** 72-column condition block, and
every model was evaluated on the same fold indices under all three schemes. Full
hyperparameters are in [`MODELS.md`](MODELS.md).

### 3.1 Classical

Ridge (L2 penalty 1.0) as a linear reference against which any non-linear gain is measured; a
random forest of 300 trees and a gradient-boosting regressor of 300 stages, giving two tree
ensembles with different bias–variance characteristics; XGBoost at 500 rounds, learning rate
0.05, depth 7, row and column subsampling 0.85; and an SVR with RBF kernel, C = 10.0, scaled γ.

Tree ensembles were the primary classical candidates because the input is a heterogeneous
tabular matrix mixing continuous physical quantities, logarithmic transforms, binary
indicators and high-cardinality categorical encodings — a regime in which tree ensembles handle
the mixture, and the interactions among its parts, without the practitioner specifying
interaction terms in advance.

**Two structure-only controls** — a random forest and an XGBoost given the descriptor matrix
without the condition block — isolate the contribution of the conditions with the estimator,
folds and metric all held constant.

### 3.2 Feedforward network

256 → 128 → 128 → 1, with batch normalisation, ReLU and dropout 0.15 on the first two hidden
layers. AdamW at 1 × 10⁻³, weight decay 1 × 10⁻⁴, batch 128, up to 150 epochs, early stopping
on validation loss with patience 15.

### 3.3 Graph networks with condition fusion

A **message-passing network** in the formulation of Gilmer et al. (2017), implemented with
edge-conditioned convolution: an initial linear projection of the eighteen node features to
hidden width 96, three message-passing steps updating each node from its neighbours through a
bond-conditioned weight matrix generated from the three edge features, then pooling to a
graph-level vector by concatenating mean and sum pooling.

A **graph attention network** (Veličković et al., 2018) with two attention layers, the first
using four heads at hidden width 96 and the second collapsing to one, dropout 0.15 within the
attention mechanism.

**In both, the graph-level vector is concatenated with a 64-dimensional projection of the
72-dimensional condition vector before the regression head.** This corrects a specific defect
in the earlier pipeline, where the graph networks received the structure alone while the
classical models additionally received the conditions. Under that arrangement the graph
networks were asked to predict an efficiency that depends on temperature, concentration and
acidity without being told any of them, and their weak performance measured that handicap
rather than the capacity of the architecture.

### 3.4 Hybrids

Constructed in direct response to methodological review, which raised the absence of any
hybridised approach as a gap. Each couples a learned molecular representation to a tabular
learner, on the reasoning that the two sources of information have different statistical
character.

- **H1** — train the message-passing encoder on the training fold, freeze it, extract the
  graph-level embedding for every molecule, concatenate with the condition block, fit XGBoost
  at 400 rounds. The graph network performs representation learning; the boosted ensemble
  performs the regression.
- **H2** — as H1 but with the pretrained chemistry language model in place of the graph
  encoder. 384-dimensional sequence embeddings computed **once per distinct structure** rather
  than once per row, since the embedding depends only on the molecule.
- **H3** — an end-to-end three-branch fusion network. Sequence, graph and tabular branches
  trained jointly, outputs concatenated at 128, 128 and 64 dimensions and passed through a
  shared head. AdamW with a plateau scheduler reducing by 0.5 at patience 6.

### 3.5 Chemistry transformer

ChemBERTa in the `77M-MTR` variant — a RoBERTa architecture of three transformer layers at
hidden width 384, pretrained by multi-task regression on a large corpus of molecular
structures — loaded as a bare encoder with its pretraining head discarded. The regression head
pools token representations by mask-weighted mean, concatenates a 64-dimensional projection of
the condition block, and passes the result through a two-layer head. Tokenisation uses the
model's own tokeniser at a maximum of 128 tokens.

**A discriminative learning rate** updates the pretrained encoder at 3 × 10⁻⁵ while the
randomly initialised condition branch and head, which have no pretrained knowledge to
preserve, update ten times faster at 3 × 10⁻⁴. Smooth L1 loss, batch 16, six epochs per fold.

**Critically, the transformer was fine-tuned across all five folds of all three schemes** —
fifteen independent runs, each beginning from the pretrained weights rather than inheriting
the previous fold's adaptation. The earlier pipeline fine-tuned a single fold for reasons of
time budget and reported the resulting score alongside five-fold baselines. That evaluation
discrepancy is what this study exists to remove, and it was removed by expending the compute.

---

## 4. Partitioning and the control of information leakage

**This is the methodological core of the study.**

### 4.1 Three schemes

Because the corpus contains on average almost eight measurements of each molecule, the choice
of partitioning unit determines what the resulting score *measures*. Three schemes were
constructed and all three carried through the entire study.

| Scheme | Unit | Question it answers |
|---|---|---|
| **Row-wise** | row | *An experimental control, not an estimate of skill.* The convention used in almost all published corrosion-inhibition ML work |
| **Grouped by molecule** | canonical SMILES | How does the model perform on a compound it has never seen? **The headline.** |
| **Scaffold** | Bemis–Murcko framework | How does it perform on a chemical family it has never seen? |

Grouping used `GroupKFold` on the canonical SMILES, so every measurement of a molecule is
assigned to the same fold and a molecule appearing in validation is guaranteed absent from
training **in every one of its measured conditions**. The scaffold scheme decomposes each
molecule to its Bemis–Murcko framework — the ring system with linkers retained and side chains
stripped — and groups by that. It is stricter, requiring generalisation to an unseen chemical
class rather than merely to a new substitution pattern on a familiar one.

**Fold indices were generated once, saved to disk, and read by every subsequent model.** That
single shared partition object, published as
[`../data/fold_indices.npy`](../data/fold_indices.npy), is the mechanism that makes the
leaderboard a benchmark.

### 4.2 Quantifying the leakage

Overlap was measured directly for each scheme by counting, in every fold, the distinct
validation molecules that also appear somewhere in the corresponding training partition.

| Scheme | Mean validation rows | Mean distinct molecules | Mean already seen | % seen |
|---|---|---|---|---|
| Row-wise (control) | 1,671.8 | 670.0 | 633.0 | **94.5** |
| Grouped by molecule | 1,671.8 | 210.0 | 0.0 | 0.0 |
| Scaffold | 1,671.8 | 210.0 | 0.0 | 0.0 |

Per-fold values under the row-wise scheme range from 93.3 % to 96.0 %.
([`../metrics/split_leakage_audit.csv`](../metrics/split_leakage_audit.csv))

**Retaining the row-wise scheme alongside the other two converts a hazard into a
measurement.** The difference in score between the control and the grouped scheme, computed
with the model, the metric and the fold sizes all held fixed, is an estimate of the inflation
attributable to structural leakage, and it is reported as such.

### 4.3 Fold-local preprocessing

All preprocessing that learns a parameter from the data — the median imputer, the
zero-variance filter, the categorical encoder and the standard scaler — was fitted inside the
training partition of each fold and applied without refitting to the corresponding validation
partition. Never on the full matrix.

### 4.4 Treatment of missing conditions

Exposure duration is absent from every Inhibitor 1368 record and from 38 % of ExCorr records;
across the corpus it is present on 67 % of rows. It was retained rather than discarded for two
reasons.

The first is chemical: efficiency measured after six hours and after seven days are not the
same quantity, because the inhibitor film forms, matures and in some systems breaks down over
the exposure period. Removing the variable would force the model to treat measurements from
very different points on that time course as interchangeable.

The second is that **the missingness is not random**. It is almost perfectly predicted by the
source, and therefore carries information about which experimental tradition a record came
from.

Two mechanisms handle the absent values without either discarding records or inventing
precision: median imputation **within the training fold**, and a companion binary indicator
recording whether the original value was present. The indicator lets the model distinguish an
imputed value from a measured one and learn a different response in each case, which a bare
imputation would not permit.

---

## 5. Hyperparameter optimisation and tuning leakage

Optimisation used the tree-structured Parzen estimator in Optuna (Akiba et al., 2019). The
strongest classical model on the scaffold partition — the random forest — was tuned over ten
trials, trees searched on [100, 500] and maximum depth on [4, 32]. **Selected: 250 trees at
maximum depth 31**, scaffold R² 0.3991.
([`../metrics/classical_tuning.json`](../metrics/classical_tuning.json))

Bayesian optimisation was preferred to grid search because the space is continuous in several
dimensions and a sequential optimiser concentrates evaluations where performance is good,
which matters when each evaluation costs a full five-fold cross-validation on a corpus of this
size.

**Tuning was performed against the scaffold partition**, the most demanding of the three, so
the selected configuration is the least likely to have been chosen for its ability to exploit
structural similarity between training and validation data.

> ### Tuning leakage: implemented, not executed
>
> A distinct hazard arises when the same cross-validation loop both selects hyperparameters
> and reports performance, because the reported score then reflects a configuration chosen
> with knowledge of the very folds it is scored on. This inflates the estimate even when the
> data partition is sound.
>
> The methodology provides for its removal through nested cross-validation, with an inner loop
> searching within each outer training partition and the outer loop reporting on data the
> search never saw. **The nested procedure was implemented in the pipeline (Cell 6.6b) but was
> not executed in the reported run** — its cost, about three hours of additional accelerated
> compute on top of the six-hour pipeline, exceeded the session allowance.
>
> **The tuned figures are therefore optimistic by an unmeasured margin.** The untuned
> benchmark figures, which are unaffected because no selection was performed against them,
> carry the principal comparative conclusions of this study. This is stated explicitly rather
> than left implicit.

---

## 6. Evaluation protocol

### 6.1 Metrics

Five quantities computed for every model, under every scheme, on every fold, reported as the
mean across folds **with the fold-to-fold standard deviation**.

- **R²** — the proportion of variance explained. Reported as *explained variance*, never as
  *accuracy*: accuracy is a classification quantity and this is regression on a continuous
  response.
- **RMSE** and **MAE** — the typical error magnitude in percentage points of inhibition
  efficiency. Reported together because they weight large errors differently.
- **Spearman ρ** — how well the model orders inhibitors. Included because the practical use of
  such a model is ranking candidates for screening, and a model that ranks correctly while
  being systematically displaced in absolute value remains useful for that.
- **Fold-to-fold standard deviation** — reported alongside every mean, because a mean R²
  without its spread conceals whether an ordering is stable or an artefact of one favourable
  fold.

### 6.2 The flat benchmark

Every model was scored through a single shared evaluation harness which read the same fold
indices, computed the same five metrics by the same code path, and wrote to a single ledger.
Out-of-fold predictions were retained for every model, so later analyses operate on
predictions never seen during that model's training.

**Uniformity was enforced on three axes simultaneously**: the same rows in the same folds, the
same information in the feature matrix, and the same metric computed by the same function.
This is what makes the leaderboard a benchmark rather than a collection of separately obtained
numbers.

### 6.3 Paired significance testing

A leaderboard produces an ordering whether or not the ordering is meaningful. Absolute errors
from the retained out-of-fold predictions were compared pairwise between the six leading
models using the **Wilcoxon signed-rank test** (Wilcoxon, 1945), a non-parametric paired test
appropriate for error distributions that are not normal. **Pairs failing to reach significance
at the 0.05 level are reported as ties, not as an ordering.**

---

## 7. Ablation

A cumulative ablation attributes performance to the individual feature blocks. Starting from
structure alone, the condition block, pH provenance, substrate, methodology and fingerprint
blocks were added in turn, with the model refitted and rescored at each step under **both**
honest schemes. The marginal contribution of each block is the change in explained variance on
its addition.

The quantum block was handled separately. Because the DFT parameters are available for only
2,895 of the 8,359 rows, adding them to the pooled matrix would have required either
discarding two-thirds of the corpus or imputing quantum-chemical quantities — neither
defensible. **The block was therefore evaluated on its own supporting subset, with and without
the quantum columns, so the comparison is made on identical rows.**

---

## 8. Bias, calibration and the noise floor

### 8.1 Disaggregation

A model that performs well on average may perform badly on an identifiable subgroup, and an
aggregate score conceals this. Performance was disaggregated across **base metal, alloy
designation, chemical regime and measurement methodology**, computing within each group the
explained variance, RMSE, MAE and **mean signed residual** on out-of-fold predictions.

The mean signed residual is the diagnostic for bias. A group whose residuals average to
approximately zero is predicted without systematic displacement; a group whose residuals are
consistently positive or negative is systematically over- or under-predicted, which is the
operational definition of a biased model.

### 8.2 Imbalance

The data is not balanced — 4,726 rows in acidic media against 3,052 near-neutral and 538
alkaline, and a dominance of iron and aluminium substrates. **This was measured and reported
rather than corrected.** Resampling would have distorted the marginal distribution of a corpus
assembled from the published record, and the imbalance is itself a finding about the state of
that record. A model trained predominantly on acid data should be expected to perform
differently in alkaline service, and the disaggregated results make the size of that
difference visible.

### 8.3 Calibrated prediction intervals

Point predictions are supplemented with intervals obtained by **split conformal prediction**
(Vovk et al., 2005; Lei et al., 2018). Absolute residuals are computed on a calibration
partition, the empirical quantile at the nominal 90 % level is taken, and the resulting half
width applied symmetrically around each point prediction.

Conformal prediction was selected because it is distribution-free, requiring no assumption of
normality in the residuals, and because its coverage guarantee holds in finite samples under
exchangeability. For a screening application this matters more than the point prediction
alone: a practitioner needs to know the interval within which the true efficiency is expected
to fall before committing laboratory time.

> **The calibration partition must be disjoint at the level of the molecule, and in the
> published run it was not.** Notebook Cell 9.3 calibrates on a random row permutation, which
> shares molecules between the fitting and calibration sets and yields an interval that is too
> narrow. Recalibrated on a molecule-disjoint partition, the 90 % interval is **±38.6 points
> at 92.6 % empirical coverage**, against the ±18.67 at 97.4 % that the row-wise calibration
> produced. The wider figure is the one quoted throughout this repository and returned by the
> deployed service. See [`LIMITATIONS.md`](LIMITATIONS.md) §1.

### 8.4 The measurement noise floor

A model's error is conventionally reported against an implicit target of zero, which presumes
the measurements it is trained on are exact. That does not hold for efficiencies compiled from
the primary literature, where the same molecule tested on the same metal in the same medium at
the same concentration by different laboratories will not return the same number.

The corpus permits this to be quantified. **878 groups of records were identified in which the
molecule, metal, alloy and every experimental condition agree**, so that the only difference
within a group is the measurement itself. The standard deviation of reported efficiency within
each group was computed, and from the median of those standard deviations the expected
absolute difference between two independent measurements was derived.

This is the reproducibility floor of the underlying experimental record, and it establishes
the error below which no model trained on that record can be expected to go.

---

## 9. Interpretation

Three complementary methods, one per principal model family, on the reasoning that a tree
ensemble, a graph network and a transformer expose their reasoning through different
mechanisms and no single method serves all three.

- **Shapley additive explanations** (Lundberg & Lee, 2017) for the tuned tree ensemble. The
  Shapley value attributes the model's deviation from its base prediction among the input
  features by a game-theoretic allocation satisfying local accuracy and consistency, giving
  both a global ranking and a per-prediction decomposition. Permutation importance was
  computed as a fallback where the Shapley computation was unavailable.
- **Integrated gradients** (Sundararajan et al., 2017) for the message-passing network,
  integrating the gradient of the output with respect to the input along a path from an
  uninformative baseline, yielding per-atom saliency.
- **Attention rollout** (Abnar & Zuidema, 2020) for the fine-tuned transformer, aggregating
  attention matrices across layers to indicate which SMILES tokens the model attended to.

---

## 10. Kinetic and mechanistic analysis

The modelling was supplemented with an analysis of the functional form of the dose response,
to establish whether the relationships the models learned are consistent with the accepted
physical chemistry of inhibitor adsorption rather than being merely statistically adequate.

Concentration dependence was examined against the **Langmuir adsorption isotherm** (Langmuir,
1918), under which surface coverage θ relates to bulk concentration C through
θ = KC / (1 + KC), with efficiency taken as proportional to coverage. The linearised form
— C/θ against C — was fitted to condition-matched subsets and the adsorption equilibrium
constant extracted. Temperature dependence was examined in **Arrhenius** form, the logarithm
of the residual corrosion rate against reciprocal absolute temperature.

**Corrosion inhibition is not a linear process.** The concentration response saturates in the
manner of an adsorption isotherm and the temperature response is exponential, so a modelling
strategy assuming linearity in the untransformed variables is misspecified from the outset.
This is the chemical justification both for the choice of non-linear estimators and for the
explicit logarithmic and reciprocal transforms in §2.4.

---

## 11. External validation against the published record

Two forms of comparison.

**A direct reproduction.** The protocol reported by the authors of the Inhibitor 1368 dataset
was reimplemented on their own data, using their feature set, their model family and their
evaluation scheme, and the resulting figures compared with the published ones. The identical
protocol was then rerun with **the single change** that cross-validation was grouped by
molecule rather than by row, and the difference recorded.

This is external validation of the leakage finding. If the inflation observed on this corpus
were an artefact of this corpus, of its assembly, or of these features, it would not reappear
on a different dataset with different features assembled by different authors. Observing it in
both places establishes it as a property of **the evaluation convention** rather than of any
one pipeline — and it means comparisons with published figures must be made protocol to
protocol, not number to number.

**A tabulated comparison** against published studies in the field, recording for each the
target, corpus size, evaluation protocol, model family and reported R². Two studies from the
adjacent field of reaction-yield prediction were included, because that field has already
encountered the same phenomenon and reports the same divergence between curated and
literature-compiled data.

---

## 12. Reproducibility controls

Four controls, documented in full in [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).

1. A single global random seed (42) for Python, NumPy and PyTorch, with every stochastic
   estimator seeded from it.
2. Fold indices generated once and reused by every model.
3. Library versions recorded **programmatically at run time** rather than transcribed
   afterwards, into [`../provenance/runtime_spec.json`](../provenance/runtime_spec.json).
4. All preprocessing that learns from data confined within the training fold.

Every execution created a timestamped run directory with subdirectories for data, figures,
models, metrics, attributions and logs, together with a machine-readable manifest recording
every artefact written, its type and a note describing its provenance
([`../provenance/manifest.json`](../provenance/manifest.json)).

Because the fold indices are saved, any result can be recomputed on exactly the rows that
produced it. Because the preprocessing audit is saved, any individual prediction can be traced
back to its source record and to every transformation applied to it. **This is traceability by
construction rather than by assertion.**

---

## References

Abnar, S., & Zuidema, W. (2020). Quantifying attention flow in transformers. *Proceedings of
the 58th Annual Meeting of the ACL*, 4190–4197. https://doi.org/10.18653/v1/2020.acl-main.385

Akiba, T., Sano, S., Yanase, T., Ohta, T., & Koyama, M. (2019). Optuna: A next-generation
hyperparameter optimization framework. *KDD '19*, 2623–2631.
https://doi.org/10.1145/3292500.3330701

Bemis, G. W., & Murcko, M. A. (1996). The properties of known drugs. 1. Molecular frameworks.
*Journal of Medicinal Chemistry, 39*(15), 2887–2893. https://doi.org/10.1021/jm9602928

Breiman, L. (2001). Random forests. *Machine Learning, 45*(1), 5–32.
https://doi.org/10.1023/A:1010933404324

Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *KDD '16*, 785–794.
https://doi.org/10.1145/2939672.2939785

Chithrananda, S., Grand, G., & Ramsundar, B. (2020). *ChemBERTa: Large-scale self-supervised
pretraining for molecular property prediction* (arXiv:2010.09885).
https://arxiv.org/abs/2010.09885

Fey, M., & Lenssen, J. E. (2019). *Fast graph representation learning with PyTorch Geometric*
(arXiv:1903.02428). https://arxiv.org/abs/1903.02428

Gilmer, J., Schoenholz, S. S., Riley, P. F., Vinyals, O., & Dahl, G. E. (2017). Neural message
passing for quantum chemistry. *ICML 2017*, 1263–1272.

Kapoor, S., & Narayanan, A. (2023). Leakage and the reproducibility crisis in
machine-learning-based science. *Patterns, 4*(9), 100804.
https://doi.org/10.1016/j.patter.2023.100804

Landrum, G. (2026). *RDKit: Open-source cheminformatics* (Version 2026.03.6) [Computer
software]. https://www.rdkit.org

Langmuir, I. (1918). The adsorption of gases on plane surfaces of glass, mica and platinum.
*Journal of the American Chemical Society, 40*(9), 1361–1403.
https://doi.org/10.1021/ja02242a004

Lei, J., G'Sell, M., Rinaldo, A., Tibshirani, R. J., & Wasserman, L. (2018). Distribution-free
predictive inference for regression. *Journal of the American Statistical Association,
113*(523), 1094–1111. https://doi.org/10.1080/01621459.2017.1307116

Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions.
*NeurIPS, 30*, 4765–4774.

Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G., … Chintala, S. (2019).
PyTorch: An imperative style, high-performance deep learning library. *NeurIPS, 32*,
8024–8035.

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., … Duchesnay,
É. (2011). Scikit-learn: Machine learning in Python. *JMLR, 12*, 2825–2830.

Rogers, D., & Hahn, M. (2010). Extended-connectivity fingerprints. *Journal of Chemical
Information and Modeling, 50*(5), 742–754. https://doi.org/10.1021/ci100050t

Schwaller, P., Vaucher, A. C., Laino, T., & Reymond, J.-L. (2021). Prediction of chemical
reaction yields using deep learning. *Machine Learning: Science and Technology, 2*(1), 015016.
https://doi.org/10.1088/2632-2153/abc81d

Sundararajan, M., Taly, A., & Yan, Q. (2017). Axiomatic attribution for deep networks. *ICML
2017*, 3319–3328.

Veličković, P., Cucurull, G., Casanova, A., Romero, A., Liò, P., & Bengio, Y. (2018). Graph
attention networks. *ICLR*. https://arxiv.org/abs/1710.10903

Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic learning in a random world*.
Springer. https://doi.org/10.1007/b106715

Wilcoxon, F. (1945). Individual comparisons by ranking methods. *Biometrics Bulletin, 1*(6),
80–83. https://doi.org/10.2307/3001968
