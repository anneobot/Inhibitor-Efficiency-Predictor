# Limitations

What this work does not establish, and where the model should not be trusted.

This document is deliberately blunt. A screening instrument that overstates itself costs
laboratory time and credibility, and the central finding of this study is precisely that the
field's reported figures are inflated by a methodological convention. It would be incoherent
to publish that finding behind an optimistic account of our own result.

---

## 1. The published conformal interval was miscalibrated, and the honest one is wide

**Status: corrected here. The thesis reports the corrected figure; the archived notebook and
figure do not.**

The run's Cell 9.3 drew its conformal calibration set by permuting rows at random. Because the
corpus contains on average almost eight measurements of each molecule, a row-wise calibration
set shares molecules with the fitting set — the same leakage this study exists to document,
re-entering through the calibration step. The interval it produced, **±18.67 points at 97.4 %
empirical coverage**, is less than half the honest width, and the conclusion drawn from it —
that the intervals are "conservative" — does not hold.

Recalibrated on a partition disjoint at the level of the molecule, the 90 % interval is
**±38.6 points at 92.6 % empirical coverage**.

| | Half width | Empirical coverage | Status |
|---|---|---|---|
| Molecule-disjoint calibration | **±38.6** | **92.6 %** | **Quote this** |
| Row-wise calibration | ±18.67 | 97.4 % | Superseded |

**What follows from the honest figure.** A ±38.6-point band on a 0–100 scale is wide. It means
the instrument is suited to **ranking candidates for laboratory work**, not to predicting a
specific efficiency. A predicted 75 % with that band does not distinguish a good inhibitor
from a mediocre one in absolute terms; it does, in combination with the Spearman correlation
of 0.687, place candidates in a defensible order.

`figures/fig10_conformal_intervals.png` plots the superseded version and is retained unaltered
because it is what the archived run produced. See [`FIGURES.md`](FIGURES.md).

---

## 2. Experimental validation rests on two compounds

The laboratory comparison covers **two** constituents of African Spiral Flag extracts on
aluminium in 1 M HCl at 303 K: stem 85.0 % measured against 88.1 % predicted, leaf 79.0 %
against 86.9 %.

The agreement is encouraging — both absolute errors, 3.1 and 7.9 points, are smaller than the
15.7-point MAE for unseen molecules, and the ordering of the two extracts was predicted
correctly. But **two observations cannot establish broad external validity, cannot quantify
prediction-interval coverage, and cannot demonstrate that the consistent over-prediction
represents a persistent bias rather than chance.**

The wider comparison against 30 published compounds is stronger evidence (Pearson r = +0.496,
p = 0.0053; Spearman ρ = +0.373, p = 0.0417) but it is a correlation against the same
published record the model was trained on, not against independent experiment.

---

## 3. Nested cross-validation was implemented but not executed

The tuned configuration — 250 trees at maximum depth 31 — was selected by searching
hyperparameters against the same cross-validation folds on which performance is reported.
That is tuning leakage: the reported score reflects a configuration chosen with knowledge of
the folds it is scored on, and it inflates the estimate even when the data partition itself is
sound.

The nested procedure that removes this was written (Cell 6.6b) and **not run** — about three
hours of additional accelerated compute beyond the six-hour pipeline, exceeding the session
allowance.

**Every tuned figure in this repository is therefore optimistic by an unmeasured margin.** The
untuned benchmark figures are unaffected, because no selection was performed against them, and
they carry the comparative conclusions. When reading [`RESULTS.md`](RESULTS.md), the benchmark
and ablation tables are the dependable ones; anything attributed to "the tuned model" is not.

---

## 4. Exposure duration is absent from a third of the corpus

Duration is absent from every Inhibitor 1368 record and from 38 % of ExCorr records — 33 % of
the corpus overall — and **the missingness is structured by source rather than random**. It is
almost perfectly predicted by which database a row came from.

The was-missing indicators let the model distinguish an imputed value from a measured one and
learn a different response in each case. **They do not recover the information that was never
recorded.** A prediction for a long-exposure service condition rests on a weaker evidential
base than the aggregate metrics suggest.

---

## 5. The corpus is dominated by acidic media, and omits whole regimes

4,726 rows in acidic media against 3,052 near-neutral and 538 alkaline. The disaggregated
results do not show strong bias by regime — explained variance is in fact highest in alkali at
0.408 — but **538 rows is not a basis for claiming reliability in alkaline service**.

More seriously, the corpus contains **no atmospheric corrosion, no microbiologically
influenced corrosion, no erosion corrosion and no stress-corrosion cracking at all**. The
model should not be assumed to transfer to any of them. It has not been tested there; it has
not been trained there; there is nothing to extrapolate from.

Zinc substrates were excluded (33 rows across 31 molecules) and are not served.

---

## 6. Named subgroups where the model fails

These are surfaced per request by the deployed service rather than averaged away. They are
listed here so a reader of the repository sees them without running anything.

**Alloy designations with severe bias.** Over- and under-predictions of this size exceed the
conformal band and are systematic, not scatter.

| Designation | n | Bias (points) |
|---|---|---|
| `Cold rolled steel` | 160 | **+30.0** over-predicted |
| `Stainless steel` | 48 | **+22.5** over-predicted |
| `Fe` | 99 | **+16.1** over-predicted |
| `Steel` | 66 | **−18.8** under-predicted |
| `AA1100` | 169 | **−10.0** under-predicted |

The pattern is consistent with sparse support combined with inconsistent labelling in the
source literature, where the same physical material may be recorded as *carbon steel* in one
publication and as *Steel* or *Fe* in another.

**Measurement techniques explaining no variance.**

| Technique | n | R² |
|---|---|---|
| `current density` | 138 | **−0.421** |
| `polarisation resistance` | 437 | **−0.085** |
| `gravimetric` | 1,730 | **−0.045** |

Gravimetric measurement is the single largest technique after potentiodynamic polarisation,
and the model explains none of its variance. It is also the slowest and least controlled
technique in the corpus, carrying the widest scatter in the underlying literature, which
places a ceiling on how well **any** model could predict it.

**Iron is a special case and should not be read as failure.** Its R² is −0.057 while its MAE,
at 12.56, is the *best* of the four metals. Iron records cluster tightly at a high mean
efficiency of 78.3, so there is little variance available to explain. Warning a user on base
metal would flag 42 % of requests misleadingly. This is why R² is never reported here without
the error in the units of the target beside it.

---

## 7. Quantum descriptors could not be pooled

The DFT frontier-orbital parameters exist for only 2,895 of 8,359 rows — 34.6 %, and all from
one source. Adding them to the pooled matrix would have required discarding two-thirds of the
corpus or imputing quantum-chemical quantities, neither defensible. Their contribution could
therefore be assessed **only on their own supporting subset**, where adding them reduced
explained variance from 0.264 to 0.167.

The fold-to-fold standard deviation on that subset is large (0.539 and 0.725), so this is
**an absence of demonstrated benefit rather than a precisely measured harm**. The correlation
of predicted efficiency against ΔE for 20 compounds was negative, as chemistry expects, but
**not statistically significant** (r = −0.417, p = 0.067; ρ = −0.376, p = 0.102).

---

## 8. A residual deduplication artefact

The deduplication key includes exposure duration. Because Inhibitor 1368 never reports
duration while its ExCorr counterparts frequently do, a small number of near-duplicate pairs
were separated by duration being present on one side and absent on the other.

**This affects the row-wise control partition only.** Under the grouped and scaffold schemes
every copy of a molecule is assigned to the same fold by construction, so no near-duplicate
can straddle the train/test boundary. If anything it means the row-wise control slightly
*understates* the leakage it is there to measure.

---

## 9. A single random seed

All results use seed 42 throughout. Repeating the pipeline across several seeds would give
confidence intervals on the fold-to-fold standard deviations reported alongside every mean,
and would establish whether the two-tier structure in the significance testing is stable. That
has not been done.

---

## 10. What the model is for, and what it is not for

**It is a screening and prioritisation instrument.** Its defensible use is to rank candidate
inhibitors under a stated service condition so that laboratory effort goes to the most
promising, and to say when a candidate falls outside the chemistry it has seen.

**It is not a substitute for measurement.** It does not replace electrochemical or
weight-loss testing, and it is not qualified for engineering sign-off. With a ±38.6-point
interval, treating a point estimate as a specification would be a misuse of the instrument.

**A prediction is not a safety or environmental assessment.** It says nothing about toxicity,
ecotoxicity, regulatory status or materials compatibility. Any candidate must still undergo
laboratory, toxicity, environmental and engineering-compatibility testing before adoption.

**A prediction requires the conditions.** Structure alone explains under 17 % of the variance.
A prediction quoted without the temperature, concentration, duration, substrate, medium and
technique it was made for is not interpretable.

---

## 11. The recommended workflow

Stated in the thesis and reproduced here because it is the honest use of a wide-interval
model:

1. Specify the metal, alloy, medium, pH, temperature, concentration and exposure duration.
2. Generate predictions **with their uncertainty intervals**.
3. Check that the case lies within the model's applicability domain.
4. Prioritise candidates with favourable predicted performance **and manageable uncertainty**.
5. Confirm experimentally.

The benefit is in prioritisation, not in exact prediction.
