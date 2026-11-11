"""Simulator dogrulama ve saglama testleri: python -m pytest -q tests/test_sim.py"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.sim import METHODS, SimConfig, Simulation, run_simulation  # noqa: E402
from src.sim.channel import (link_success_prob, nakagami_m,  # noqa: E402
                             nakagami_success_sum)
from src.sim.mobility import Highway  # noqa: E402

FAST = SimConfig(density=100, sim_time=90.0, warmup=10.0, tail=20.0)


# ---------- Kanal ----------
@pytest.mark.parametrize("m", [1, 2, 3])
@pytest.mark.parametrize("x", [0.05, 0.5, 2.0])
def test_gammaincc_equals_paper_sum(m, x):
    """Denk. 1'deki toplam bicimi ile kullandigimiz gammaincc ayni olmali."""
    from scipy.special import gammaincc
    assert abs(gammaincc(m, x) - nakagami_success_sum(m, x)) < 1e-12


def test_nakagami_m_thresholds():
    """Denk. 2: 49 m -> 3, 50 m -> 1.5, 149 m -> 1.5, 150 m -> 1."""
    assert list(nakagami_m([49, 50, 149, 150, 249])) == [3, 1.5, 1.5, 1, 1]


def test_link_prob_monotone_and_zero_outside_range():
    cfg = SimConfig()
    d = np.linspace(1, 250, 300)
    p = link_success_prob(d, cfg)
    assert np.all((p >= 0) & (p <= 1))
    assert np.all(np.diff(p) <= 1e-12)          # mesafe arttikca basari azalir
    assert link_success_prob(np.array([251.0]), cfg)[0] == 0.0


# ---------- Hareket ----------
def test_link_expiration_time():
    """LET aninda iki aracin x farki tam menzil sinirinda olmali."""
    cfg = SimConfig(density=50)
    hw = Highway(cfg, np.random.default_rng(0))
    hw.x[:2] = [100.0, 150.0]
    hw.y[:2] = [0.0, 0.0]
    hw.direction[:2] = [1.0, -1.0]
    hw.speed[:2] = [20.0, 10.0]                   # goreli hiz 30 m/s, birbirinden uzaklasmiyor
    t = float(hw.link_expiration(0, 1)[0])
    # x farki: 50 - 30 t = -250  ->  t = 10 s
    assert abs(t - 10.0) < 1e-9


def test_ring_distance_wraps():
    cfg = SimConfig(density=50)
    hw = Highway(cfg, np.random.default_rng(0))
    hw.x[:2] = [10.0, cfg.road_length - 10.0]
    hw.y[:2] = [0.0, 0.0]
    assert abs(float(hw.dist(0, 1)) - 20.0) < 1e-9


# ---------- Simulasyon ----------
def test_same_seed_is_deterministic():
    a = run_simulation("FUZZY", FAST, seed=7)
    b = run_simulation("FUZZY", FAST, seed=7)
    for k in ("completion_rate", "avg_delay", "n_tasks"):
        assert a[k] == b[k]


def test_common_random_numbers_across_methods():
    """Adil karsilastirma: ayni seed -> tum yontemlerde ayni araclar ve ayni gorevler."""
    sims = [Simulation(m, FAST, seed=3) for m in ("LPA", "FUZZY")]
    for attr in ("gen_t", "origin", "size", "priority", "deadline"):
        assert np.array_equal(getattr(sims[0].tasks, attr), getattr(sims[1].tasks, attr))
    assert np.array_equal(sims[0].mips, sims[1].mips)
    assert np.array_equal(sims[0].hw.x, sims[1].hw.x)


@pytest.mark.parametrize("method", METHODS)
def test_metrics_are_sane(method):
    m = run_simulation(method, FAST, seed=1)
    assert m["n_tasks"] > 50
    assert 0.0 <= m["completion_rate"] <= 1.0
    assert m["avg_delay"] > 0
    fracs = [v for k, v in m.items() if k.startswith("frac_")]
    assert abs(sum(fracs) + m["completion_rate"] - 1.0) < 1e-9      # tum durumlar = %100
    if method == "LPA":
        assert m["offload_ratio"] == 0.0
    else:
        assert m["offload_ratio"] > 0.95


def test_neighbors_grow_with_density():
    lo = run_simulation("RPA", FAST.with_(density=50), seed=1)["avg_neighbors"]
    hi = run_simulation("RPA", FAST.with_(density=300), seed=1)["avg_neighbors"]
    assert hi > 4 * lo


def test_fuzzy_queue_prefers_urgent_task():
    """EN kuyrugunda bulanik siralama, digerleri esitken onceligi yuksek gorevi secmeli."""
    sim = Simulation("FUZZY", FAST, seed=1)
    T = sim.tasks
    j, a, b = 0, 1, 2
    for k, (orig, pr) in enumerate([(a, 0.1), (b, 0.95)]):
        T.origin[k], T.priority[k], T.size[k] = orig, pr, 3.0
    sim.hw.x[[j, a, b]] = [0.0, 100.0, 100.0]
    sim.hw.y[[j, a, b]] = [0.0, 0.0, 0.0]
    sim.hw.speed[[a, b]] = sim.hw.speed[j]
    sim.hw.direction[[j, a, b]] = 1.0
    assert sim._fuzzy_pick(j, [0, 1]) == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
