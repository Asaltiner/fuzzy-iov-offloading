"""
Gorev akisi uretimi.

Gorevler yontemden BAGIMSIZ olarak simulasyon basinda uretilir. Boylece ayni seed ile
calistirilan tum yontemler birebir ayni gorevlerle karsilasir (ortak rastgele sayilar,
adil karsilastirma).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import SimConfig

# Gorev durum kodlari
PENDING, COMPLETED, FAIL_UPLOAD, FAIL_LINK, DROPPED, LATE, FAIL_RESULT = range(7)
STATE_NAMES = {
    PENDING: "pending", COMPLETED: "completed", FAIL_UPLOAD: "fail_upload",
    FAIL_LINK: "fail_link", DROPPED: "dropped_queue", LATE: "late", FAIL_RESULT: "fail_result",
}


@dataclass
class TaskTable:
    gen_t: np.ndarray        # uretilme zamani (s)
    origin: np.ndarray       # gorevi ureten arac (UN)
    size: np.ndarray         # veri boyutu (Mb)
    mi: np.ndarray           # islem yuku (milyon komut)
    priority: np.ndarray     # 0-1 (uygulama onceligi)
    deadline: np.ndarray     # mutlak son teslim zamani (s)

    def __post_init__(self):
        n = len(self.gen_t)
        self.target = np.full(n, -1, dtype=int)
        self.state = np.full(n, PENDING, dtype=int)
        self.arrive_t = np.full(n, np.nan)
        self.start_t = np.full(n, np.nan)
        self.finish_t = np.full(n, np.nan)
        self.delay = np.full(n, np.nan)

    def __len__(self):
        return len(self.gen_t)


def generate_tasks(cfg: SimConfig, n_vehicles: int, rng: np.random.Generator) -> TaskTable:
    t_end = cfg.sim_time - cfg.tail
    n = rng.poisson(cfg.task_rate * n_vehicles * t_end)
    gen_t = np.sort(rng.uniform(0, t_end, n))
    origin = rng.integers(0, n_vehicles, n)
    size = rng.uniform(cfg.size_min, cfg.size_max, n)
    prio = rng.random(n)
    rel_deadline = cfg.deadline_base + cfg.deadline_per_mb * size + cfg.deadline_urgency * (1 - prio)
    return TaskTable(gen_t=gen_t, origin=origin, size=size, mi=size * cfg.mi_per_mb,
                     priority=prio, deadline=gen_t + rel_deadline)
