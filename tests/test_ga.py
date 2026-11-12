"""GA-FIS (src/fuzzy/ga_tuning.py) testleri: kodlama, onarim, operatorler, tekrar uretilebilirlik."""
import numpy as np

from src.fuzzy.fis import INPUTS, FuzzyPrioritySystem
from src.fuzzy.ga_tuning import (MARGIN, MIN_GAP, N_GENES, FitnessWeights, GAConfig,
                                 GeneticTuner, decode, default_genome, make_fis,
                                 mean_rel_deadline, repair, run_metrics)
from src.sim import SimConfig


def test_default_genome_unchanged_by_repair():
    g = default_genome()
    assert g.shape == (N_GENES,)
    np.testing.assert_allclose(repair(g), g)


def test_default_genome_reproduces_hand_designed_fis():
    rng = np.random.default_rng(0)
    x = (rng.uniform(0, 250, 50), rng.uniform(0, 40, 50), rng.uniform(0, 10, 50), rng.uniform(0, 1, 50))
    np.testing.assert_allclose(make_fis(default_genome()).evaluate(*x), FuzzyPrioritySystem().evaluate(*x))


def test_repair_produces_valid_breakpoints():
    rng = np.random.default_rng(1)
    for _ in range(200):
        g = repair(rng.uniform(-0.5, 1.5, N_GENES))
        for i in range(len(INPUTS)):
            b = g[4 * i:4 * i + 4]
            assert np.all(np.diff(b) >= -1e-12)
            assert b[1] - b[0] >= MIN_GAP - 1e-9 and b[3] - b[2] >= MIN_GAP - 1e-9
            assert b[0] >= MARGIN - 1e-9 and b[3] <= 1 - MARGIN + 1e-9


def test_random_genome_gives_valid_fis():
    """Rastgele (onarilmis) genomla FIS cikti evreninde kalir ve her girdide en az bir MF > 0."""
    rng = np.random.default_rng(2)
    for _ in range(20):
        fis = make_fis(rng.random(N_GENES))
        s = fis.evaluate(rng.uniform(0, 250, 100), rng.uniform(0, 40, 100),
                         rng.uniform(0, 10, 100), rng.uniform(0, 1, 100))
        assert np.all((s >= 0) & (s <= 100))
        for name, hi in zip(INPUTS, (250, 40, 10, 1)):
            mu = fis.fuzzify(name, np.linspace(0, hi, 200))
            assert np.all(mu.max(axis=1) > 0)


def test_decode_keys():
    bp = decode(default_genome())
    assert set(bp) == set(INPUTS) and all(len(v) == 4 for v in bp.values())


def test_fitness_formula():
    cfg = SimConfig()
    m = {"completion_rate": 0.9, "completion_urgent": 0.8, "avg_delay": mean_rel_deadline(cfg)}
    w = FitnessWeights(lambda_urgent=0.5, lambda_delay=0.2)
    assert abs(run_metrics(m, cfg, w) - (0.9 + 0.4 - 0.2)) < 1e-12


def test_operators_keep_genomes_valid():
    t = GeneticTuner(GAConfig(pop_size=6, generations=0), workers=1, scenarios={})
    pop = t.initial_population()
    assert len(pop) == 6
    np.testing.assert_allclose(pop[0], default_genome())          # seeding
    for _ in range(50):
        c1, c2 = t._crossover(pop[1], pop[2])
        for c in (t._mutate(c1), t._mutate(c2)):
            np.testing.assert_allclose(repair(c), c)


def test_tiny_ga_run_is_reproducible_and_elitist():
    sc = {"tiny": SimConfig(density=60.0, sim_time=60.0, warmup=5.0, tail=10.0)}
    cfg = GAConfig(pop_size=4, generations=2, train_seeds=(101,), sim_time=60.0)
    r1 = GeneticTuner(cfg, workers=1, scenarios=sc)
    o1 = r1.run(log=lambda *_: None)
    r2 = GeneticTuner(cfg, workers=1, scenarios=sc)
    o2 = r2.run(log=lambda *_: None)
    assert o1["best_genome"] == o2["best_genome"]
    best = [h["best"] for h in r1.history]
    assert all(b2 >= b1 - 1e-12 for b1, b2 in zip(best, best[1:]))    # elitizm: monoton
    assert best[-1] >= r1.history[0]["baseline"] - 1e-12                # seeding: baseline'dan kotu degil
