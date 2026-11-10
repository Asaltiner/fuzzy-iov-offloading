"""FIS dogrulama testleri: python -m pytest -q  (veya python tests/test_fis.py)

1) Kendi NumPy uygulamamiz, scikit-fuzzy ile kurulan ayni Mamdani sistemle
   ayni sonucu vermeli (bagimsiz dogrulama).
2) Monotonluk: aciliyet ilkesi geregi, oncelik artinca skor azalmamali.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.fuzzy.fis import INPUTS, IN_TERMS, OUT_TERMS, UNIVERSE, FuzzyPrioritySystem  # noqa: E402


def build_skfuzzy(fis: FuzzyPrioritySystem):
    import skfuzzy as fuzz
    from skfuzzy import control as ctrl

    ants = {}
    for name in INPUTS:
        lo, hi = UNIVERSE[name]
        a = ctrl.Antecedent(np.linspace(lo, hi, 2001), name)
        p = fis.input_mf_params(name)
        a["low"] = fuzz.trapmf(a.universe, list(p[0]))
        a["medium"] = fuzz.trimf(a.universe, list(p[1]))
        a["high"] = fuzz.trapmf(a.universe, list(p[2]))
        ants[name] = a
    out = ctrl.Consequent(fis.y, "score", defuzzify_method="centroid")
    for k, t in enumerate(OUT_TERMS):
        out[t] = fis.out_mf[k]
    rules = []
    for combo, o in zip(fis.rules, fis.rule_out):
        cond = ants[INPUTS[0]][IN_TERMS[combo[0]]]
        for n, t in zip(INPUTS[1:], combo[1:]):
            cond = cond & ants[n][IN_TERMS[t]]
        rules.append(ctrl.Rule(cond, out[OUT_TERMS[o]]))
    return ctrl.ControlSystem(rules)


def test_matches_skfuzzy():
    from skfuzzy import control as ctrl

    fis = FuzzyPrioritySystem()
    system = build_skfuzzy(fis)
    rng = np.random.default_rng(42)
    for _ in range(25):
        x = [rng.uniform(*UNIVERSE[n]) for n in INPUTS]
        sim = ctrl.ControlSystemSimulation(system)
        for n, v in zip(INPUTS, x):
            sim.input[n] = v
        sim.compute()
        assert abs(sim.output["score"] - fis.score(*x)) < 0.5, x


def test_monotonic_in_priority():
    fis = FuzzyPrioritySystem()
    p = np.linspace(0, 1, 50)
    s = fis.evaluate(np.full(50, 125.0), np.full(50, 20.0), np.full(50, 5.0), p)
    assert np.all(np.diff(s) >= -1e-6)


def test_output_range():
    fis = FuzzyPrioritySystem()
    rng = np.random.default_rng(0)
    xs = [rng.uniform(*UNIVERSE[n], 1000) for n in INPUTS]
    s = fis.evaluate(*xs)
    assert s.min() >= 0 and s.max() <= 100


if __name__ == "__main__":
    test_matches_skfuzzy()
    test_monotonic_in_priority()
    test_output_range()
    print("Tum testler gecti.")
