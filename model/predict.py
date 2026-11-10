"""
Corrosion inhibition efficiency prediction.

Load once at application start, then call predict() per request.

    from predict import Predictor
    p = Predictor("deployment_bundle")
    p.predict(smiles="BrCCCCOc1cccc2cccnc12", metal="Fe", alloy="Carbon steel",
              methodology="potentiodynamic polarisation", ph_source="measured",
              temperature_K=298.15, concentration_mM=1.0, pH=0.0)

Pin the versions in contract.json["training"]. Loading these artefacts under a
different scikit-learn version can change behaviour silently.
"""
import json, os
import numpy as np
import pandas as pd
import joblib
from rdkit import Chem
from rdkit.Chem import Descriptors


class OutsideDomain(Warning):
    pass


class Predictor:
    def __init__(self, bundle_dir="deployment_bundle"):
        b = bundle_dir
        self.C = json.load(open(os.path.join(b, "contract.json")))
        self.model = joblib.load(os.path.join(b, "model.joblib"))
        self.scaler = joblib.load(os.path.join(b, "scaler.joblib"))
        self.imputer = joblib.load(os.path.join(b, "descriptor_imputer.joblib"))
        self.mask = np.load(os.path.join(b, "descriptor_variance_mask.npy"))
        self.enc = {k: joblib.load(os.path.join(b, f"encoder_{k}.joblib"))
                    for k in ("metal", "alloy", "method", "ph_source")}
        self.NAMES = self.C["descriptor_names_all"]
        self.NUM = self.C["condition_numeric_names"]
        self.MED = self.C["condition_numeric_medians"]
        self.AD = self.C["applicability_domain"]

    # ------------------------------------------------------------------ build
    def featurise(self, smiles, metal, alloy, methodology, ph_source,
                  temperature_K=None, concentration_mM=None, duration_h=None,
                  pH=None, salt_concentration_M=None, synergist_present=0):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"SMILES could not be parsed: {smiles!r}")

        d = Descriptors.CalcMolDescriptors(mol, missingVal=np.nan)
        desc = np.array([[float(d.get(n, np.nan)) for n in self.NAMES]])
        desc = self.imputer.transform(desc)[:, self.mask]

        T, dh, cm, sm = temperature_K, duration_h, concentration_mM, salt_concentration_M
        raw = {
            "temperature_K":    T,
            "inv_T":            None if T is None else 1.0 / T,
            "duration_h":       dh,
            "log10_duration_h": None if dh is None else float(np.log10(max(dh, 1e-3))),
            "log10_conc_mM":    None if cm is None else float(np.log10(max(cm, 1e-6))),
            "pH":               pH,
            "log10_salt_M":     None if sm is None else float(np.log10(max(sm, 1e-6))),
        }
        nums = np.array([[raw[n] if raw[n] is not None else self.MED[n]
                          for n in self.NUM]], dtype=float)
        flags = np.array([[0.0 if raw[n] is not None else 1.0
                           for n in self.NUM]], dtype=float)

        # DataFrames, not bare lists, so the encoders see the column names
        # they were fitted with and stay silent
        cats = np.hstack([
            self.enc["metal"].transform(pd.DataFrame({"metal": [metal]})),
            self.enc["alloy"].transform(pd.DataFrame({"alloy": [alloy]})),
            self.enc["method"].transform(pd.DataFrame({"methodology": [methodology]})),
            self.enc["ph_source"].transform(pd.DataFrame({"ph_source": [ph_source]})),
        ])
        x = np.hstack([desc, nums, flags, cats,
                       np.array([[float(synergist_present)]])])
        if x.shape[1] != self.C["n_features"]:
            raise RuntimeError(
                f"built {x.shape[1]} features, model expects {self.C['n_features']}")
        return x

    # ------------------------------------------------------------- guardrails
    def check_domain(self, metal, alloy, methodology, **cond):
        notes = []
        if metal not in self.AD["metals_supported"]:
            notes.append(f"metal {metal!r} is outside the four the model was "
                         f"trained on ({', '.join(self.AD['metals_supported'])})")
        for k in ("temperature_K", "concentration_mM", "duration_h", "pH"):
            v = cond.get(k)
            if v is None:
                continue
            lo, hi = self.AD[k]
            if v < lo or v > hi:
                notes.append(f"{k} = {v} lies outside the training range "
                             f"{lo:g} to {hi:g}, so this is an extrapolation")
        if alloy in self.AD["unreliable_alloys"]:
            notes.append(f"the model is known to be unreliable on {alloy!r}; "
                         f"treat this prediction with caution")
        if methodology in self.AD["unreliable_methods"]:
            notes.append(f"the model explains little variance for measurements "
                         f"made by {methodology!r}")
        return notes

    # ---------------------------------------------------------------- predict
    def predict(self, **kw):
        x = self.featurise(**kw)
        point = float(self.model.predict(self.scaler.transform(x))[0])
        half = self.C["conformal"]["half_width"]
        return {
            "predicted_IE_percent": round(min(100.0, max(0.0, point)), 1),
            "interval_low":  round(max(0.0, point - half), 1),
            "interval_high": round(min(100.0, point + half), 1),
            "interval_confidence": f"{int((1 - self.C['conformal']['alpha']) * 100)} percent",
            "interval_half_width": half,
            "warnings": self.check_domain(
                kw.get("metal"), kw.get("alloy"), kw.get("methodology"),
                temperature_K=kw.get("temperature_K"),
                concentration_mM=kw.get("concentration_mM"),
                duration_h=kw.get("duration_h"), pH=kw.get("pH")),
        }


def self_test(bundle_dir="deployment_bundle"):
    """Verify the wiring against the record stored in example.json."""
    p = Predictor(bundle_dir)
    ex = json.load(open(os.path.join(bundle_dir, "example.json")))
    x = p.featurise(**ex["inputs"])
    a = np.array(ex["expected_feature_vector_first_10"])
    b = np.array(ex["expected_feature_vector_last_10"])
    ok_head = np.allclose(x[0, :10], a, atol=1e-6)
    ok_tail = np.allclose(x[0, -10:], b, atol=1e-6)
    got = float(p.model.predict(p.scaler.transform(x))[0])
    ok_pred = abs(got - ex["expected_prediction"]) < 0.01
    print(f"first 10 features match : {ok_head}")
    print(f"last 10 features match  : {ok_tail}")
    print(f"prediction matches      : {ok_pred}  "
          f"(got {got:.3f}, expected {ex['expected_prediction']:.3f})")
    if not (ok_head and ok_tail and ok_pred):
        raise SystemExit("SELF TEST FAILED, do not deploy")
    print("self test passed")
    return p


if __name__ == "__main__":
    import sys
    self_test(sys.argv[1] if len(sys.argv) > 1 else "deployment_bundle")
