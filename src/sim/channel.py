"""
V2V kanal modeli: Nakagami-m sonumleme (Denk. 1-2) + basit 802.11p yuk/carpisma modeli.

Denk. 1 (makale):  P = exp(-m r_T/Phi) * sum_{k=0}^{m-1} (m r_T/Phi)^k / k!
Bu ifade, tamsayi m icin duzenlenmis ust tamamlanmamis gamma fonksiyonuna esittir:
    P = Q(m, m r_T/Phi) = gammaincc(m, m r_T/Phi)
gammaincc, Denk. 2'deki tamsayi olmayan m = 1.5 icin de tanimli oldugundan onu kullaniyoruz
(tests/test_sim.py'de tamsayi m icin toplam formuluyle esitligi dogrulaniyor).

Ortalama alinan guc: Phi(d)/r_T = margin * (R/d)^alpha  (VARSAYIM: log-mesafe yol kaybi).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import gammaincc

from .config import SimConfig


def nakagami_m(d: np.ndarray) -> np.ndarray:
    """Denk. 2: d < 50 m -> 3, 50 <= d < 150 m -> 1.5, d >= 150 m -> 1."""
    d = np.asarray(d, dtype=float)
    return np.where(d < 50.0, 3.0, np.where(d < 150.0, 1.5, 1.0))


def nakagami_success_sum(m: int, x: float) -> float:
    """Denk. 1'in makaledeki toplam bicimi (yalnizca tamsayi m; test icin)."""
    return math.exp(-x) * sum(x**k / math.factorial(k) for k in range(m))


def link_success_prob(d: np.ndarray, cfg: SimConfig) -> np.ndarray:
    """Tek bir iletimin Nakagami-m kanalinda basarili olma olasiligi (menzil disi -> 0)."""
    d = np.maximum(np.asarray(d, dtype=float), 1.0)
    m = nakagami_m(d)
    x = m * (d / cfg.comm_range) ** cfg.pathloss_exp / cfg.link_margin   # m * r_T / Phi
    p = gammaincc(m, x)
    return np.where(d <= cfg.comm_range, p, 0.0)


def collision_prob(n_neighbors: int, cfg: SimConfig) -> float:
    """Komsu sayisi arttikca CSMA/CA carpisma olasiligi artar: 1-(1-tau)^n."""
    return 1.0 - (1.0 - cfg.collision_tau) ** max(n_neighbors, 0)


def effective_rate(n_neighbors: int, cfg: SimConfig) -> float:
    """Yogunluga bagli etkin veri hizi (Mbps).

    Komsuluktaki beklenen veri yuku (n * gorev_hizi * E[boyut]) servis kanallarinin
    toplam kapasitesine bolunerek kanal kullanimi U bulunur; baglanti hizi R*(1-U).
    Beacon'lar kontrol kanalinda (CCH) gittigi icin veri hizindan dusulmez, ancak
    carpisma olasiligina katkida bulunur (collision_prob).
    """
    mean_size = 0.5 * (cfg.size_min + cfg.size_max)
    offered = n_neighbors * cfg.task_rate * mean_size                    # Mbps
    util = min(0.9, offered / (cfg.n_service_channels * cfg.data_rate))
    return cfg.data_rate * (1.0 - util)


def transfer(size_mb: float, d: float, n_neighbors: int, cfg: SimConfig,
             rng: np.random.Generator) -> tuple[bool, float]:
    """size_mb'lik veriyi d mesafesindeki dugume parca-parca ARQ ile gonder.

    Her parca basari olasiligi p = P_nakagami(d) * (1 - P_carpisma) olan bagimsiz
    denemelerle iletilir; bir parca max_retx+1 denemede gecemezse aktarim basarisiz.
    Donus: (basarili_mi, gecen_sure_s)
    """
    rate = effective_rate(n_neighbors, cfg)
    n_frag = max(1, math.ceil(size_mb / cfg.fragment_mb))
    t_frag = (size_mb / n_frag) / rate
    p = float(link_success_prob(d, cfg)) * (1.0 - collision_prob(n_neighbors, cfg))
    if p <= 0.0:
        return False, t_frag * (cfg.max_retx + 1)
    tries = rng.geometric(p, size=n_frag)                 # her parca icin deneme sayisi
    limit = cfg.max_retx + 1
    if np.any(tries > limit):
        first_fail = int(np.argmax(tries > limit))
        used = tries[:first_fail].sum() + limit
        return False, float(used * t_frag)
    return True, float(tries.sum() * t_frag)
