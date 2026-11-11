"""
Arac hareketi: iki yonlu, cok seritli, halka (wrap-around) otoyol.

Halka yapisi sayesinde yol sonunda arac kaybolmaz ve yogunluk simulasyon boyunca
sabit kalir (yogunluk deneyleri icin gerekli). Makaledeki SUMO kent haritasi yerine
kullanilan bu sadelestirme raporda sinirlilik olarak belirtilecektir.
"""
from __future__ import annotations

import numpy as np

from .config import SimConfig


class Highway:
    def __init__(self, cfg: SimConfig, rng: np.random.Generator):
        self.cfg = cfg
        self.rng = rng
        n = cfg.n_vehicles
        self.n = n
        self.L = cfg.road_length
        self.x = rng.uniform(0, self.L, n)
        self.direction = np.where(rng.random(n) < 0.5, 1.0, -1.0)
        lane = rng.integers(0, cfg.lanes_per_dir, n)
        # +x yonu y = 0, 3.5 ; -x yonu karsi taraf (orta refuj 5 m)
        side = np.where(self.direction > 0, 0.0, 5.0 + cfg.lanes_per_dir * cfg.lane_width)
        self.y = side + lane * cfg.lane_width
        lo = max(1.0, cfg.mean_speed - cfg.speed_spread)
        hi = cfg.mean_speed + cfg.speed_spread
        self.vmin, self.vmax = lo, hi
        self.speed = rng.uniform(lo, hi, n)          # buyukluk (m/s)

    @property
    def velocity(self) -> np.ndarray:
        """Isaretli hiz (m/s): +x yonunde pozitif."""
        return self.speed * self.direction

    def step(self, dt: float) -> None:
        self.speed = np.clip(self.speed + self.rng.normal(0, self.cfg.accel_std * dt, self.n),
                             self.vmin, self.vmax)
        self.x = (self.x + self.velocity * dt) % self.L

    # ---------- geometri ----------
    def dx(self, i: int, j=None) -> np.ndarray:
        """i'den j'ye isaretli x farki, halka uzerinde [-L/2, L/2] araligina sarilmis."""
        xj = self.x if j is None else self.x[j]
        d = xj - self.x[i]
        return (d + self.L / 2) % self.L - self.L / 2

    def dist(self, i: int, j=None) -> np.ndarray:
        """i ile j (None ise tum araclar) arasindaki Oklid mesafesi."""
        yj = self.y if j is None else self.y[j]
        return np.hypot(self.dx(i, j), yj - self.y[i])

    def rel_speed(self, i: int, j=None) -> np.ndarray:
        """Denk. 4'teki |v_i - v_j| (isaretli hizlarla; karsi yon -> buyuk fark)."""
        vj = self.velocity if j is None else self.velocity[j]
        return np.abs(vj - self.velocity[i])

    def link_expiration(self, i: int, j) -> np.ndarray:
        """Baglanti kopma suresi (LET): i ile j'nin mesafesi menzili ne zaman asar?

        Hizlar sabit varsayilir. Halka uzerinde 1-B goreli hareket:
        |dx + dv*t| <= Rx, Rx = sqrt(R^2 - dy^2).
        """
        j = np.atleast_1d(j)
        R = self.cfg.comm_range
        dx = self.dx(i, j)
        dy = self.y[j] - self.y[i]
        rx = np.sqrt(np.maximum(R**2 - dy**2, 0.0))
        dv = self.velocity[j] - self.velocity[i]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (np.sign(dv) * rx - dx) / dv
        t = np.where(np.abs(dv) < 1e-9, np.inf, t)
        return np.where(np.abs(dx) <= rx, np.maximum(t, 0.0), 0.0)
