"""
Simulasyon parametreleri.

Makalede (Tablo 3) verilen degerler "MAKALE", makalede olmayip bizim sectigimiz
degerler "VARSAYIM" olarak isaretlidir. Varsayimlarin gerekcesi
docs/04_gun2_simulator.md dosyasinda tablo halinde verilmistir.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class SimConfig:
    # ---------- Yol ve hareket ----------
    road_length: float = 2000.0       # m, halka (wrap-around) otoyol - VARSAYIM (makale: 3x3 km kent)
    lanes_per_dir: int = 2            # VARSAYIM
    lane_width: float = 3.5           # m
    density: float = 150.0            # arac/km (iki yon toplam) - MAKALE araligi 50-350
    mean_speed: float = 30.0          # m/s - MAKALE araligi 10-50
    speed_spread: float = 5.0         # m/s, araclar U(mean-spread, mean+spread) - VARSAYIM
    accel_std: float = 0.5            # m/s^2, rastgele hiz degisimi - VARSAYIM

    # ---------- Zaman ----------
    sim_time: float = 300.0           # s (makale 500 s; sure kisiti) - VARSAYIM
    dt: float = 0.1                   # s, zaman adimi
    warmup: float = 20.0              # s, bu sureden once uretilen gorevler istatistige girmez
    tail: float = 30.0                # s, son 30 s'de gorev uretilmez (bitmemis gorev kalmasin)

    # ---------- Kanal (IEEE 802.11p) ----------
    comm_range: float = 250.0         # m - MAKALE
    data_rate: float = 6.0            # Mbps - MAKALE
    n_service_channels: int = 4       # WAVE SCH sayisi (veri trafigi) - VARSAYIM
    beacon_bytes: int = 194           # MAKALE
    beacon_hz: float = 10.0           # VARSAYIM (802.11p tipik)
    collision_tau: float = 0.002      # komsu basina carpisma olasiligi katkisi - VARSAYIM
    pathloss_exp: float = 3.0         # yol kaybi ussu - VARSAYIM
    link_margin: float = 2.0          # menzil sinirinda ortalama SNR / esik orani - VARSAYIM
    fragment_mb: float = 1.0          # Mb, ARQ parca boyutu - VARSAYIM
    max_retx: int = 4                 # parca basina en fazla yeniden iletim - VARSAYIM
    result_ratio: float = 0.05        # sonuc boyutu / gorev boyutu - VARSAYIM

    # ---------- Gorevler ----------
    task_rate: float = 0.015          # gorev/s/arac (Poisson) - VARSAYIM
    size_min: float = 0.5             # Mb - VARSAYIM (FIS evreni 0-10 Mb)
    size_max: float = 10.0            # Mb
    mi_per_mb: float = 1500.0         # Mb basina islem yuku (MI) - VARSAYIM
    deadline_base: float = 3.0        # s
    deadline_per_mb: float = 1.0      # s/Mb
    deadline_urgency: float = 6.0     # s; deadline = base + per_mb*S + urgency*(1-p)

    # ---------- Dugum kapasitesi (Sek. 4: poor/average/good MIPS) ----------
    mips_levels: tuple = (500.0, 1000.0, 2000.0)   # VARSAYIM
    mips_probs: tuple = (0.5, 0.35, 0.15)          # VARSAYIM

    # ---------- Yontem parametreleri ----------
    chgo_update: float = 1.0          # s, CHGO merkezi durum guncelleme periyodu - VARSAYIM
    nf_max_wait: float = 2.0          # s, NF'de "kapasite uygun" esigi - VARSAYIM
    selection_weights: dict = field(default_factory=lambda: {
        # Denk. 5-9: w_x = I_x / sum(I). Onem skorlari makalede yok -> esit - VARSAYIM
        "distance": 1.0, "speed": 1.0, "cpu": 1.0, "load": 1.0,
    })

    @property
    def n_vehicles(self) -> int:
        return max(2, int(round(self.density * self.road_length / 1000.0)))

    def with_(self, **kw) -> "SimConfig":
        return replace(self, **kw)
