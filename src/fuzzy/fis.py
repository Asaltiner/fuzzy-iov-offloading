"""
Mamdani tipi Bulanik Cikarim Sistemi (FIS) - edge dugumunde gorev onceliklendirme.

Referans: Z. Trabelsi, M. Ali, T. Qayyum, "Fuzzy-based task offloading in Internet
of Vehicles (IoV) edge computing for latency-sensitive applications," Internet of
Things, vol. 28, 101392, 2024.

Makalede edge dugumu, kuyruktaki gorevleri hiz, mesafe, gorev boyutu ve gorev
onceligine gore bulanik mantikla puanlar; yuksek puanli gorev once calistirilir.

Bu modul FIS'i NumPy ile sifirdan uygular (scikit-fuzzy yalnizca dogrulama testinde
kullanilir). Sebep: simulasyonda FIS binlerce kez cagrilacak ve 4. gunde Genetik
Algoritma uyelik fonksiyonu parametrelerini degistirecek; parametrik ve vektorlu
bir uygulama hem hizli hem de GA'ya uygundur.

Tasarim kararlari (makalede verilmedigi icin VARSAYIM, raporda belirtilecek):
  * Cikarim: Mamdani, VE = min, implikasyon = min, birlestirme = max
  * Durulastirma: agirlik merkezi (centroid)
  * Her girdi icin 3 terim: low / medium / high (yamuk-ucgen-yamuk)
  * Cikti icin 5 terim: very_low ... very_high (ucgen), evren [0, 100]
  * Kural tabani: 3^4 = 81 kural, asagidaki aciliyet ilkesiyle sistematik uretilir
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np

INPUTS = ("distance", "speed", "size", "priority")
IN_TERMS = ("low", "medium", "high")
OUT_TERMS = ("very_low", "low", "medium", "high", "very_high")

# Girdi evrenleri (min, max) - VARSAYIM, gerekceleri docs/03_uygulama_plani.md
UNIVERSE = {
    "distance": (0.0, 250.0),   # m   - iletim menzili 250 m (makale Tablo 3)
    "speed": (0.0, 40.0),       # m/s - bagil hiz; araclar 10-50 m/s -> fark 0-40
    "size": (0.0, 10.0),        # Mb  - gorev veri boyutu
    "priority": (0.0, 1.0),     # 0 = onemsiz, 1 = cok acil (uygulama sinifi)
}
OUT_UNIVERSE = (0.0, 100.0)

# Aciliyet ilkesi: hangi girdinin hangi yonde ve ne agirlikla etki ettigi
#  distance  +1 : arac menzilin kenarina yaklastikca baglanti kopmak uzere -> daha acil
#  speed     +1 : bagil hiz yuksekse baglanti suresi kisa -> daha acil
#  size      -1 : kucuk gorev cabuk biter (shortest-job-first), kuyruk gecikmesini azaltir
#  priority  +1 : uygulamanin kendi onceligi (en guclu etki, agirlik 2)
DIRECTION = {"distance": +1, "speed": +1, "size": -1, "priority": +1}
RULE_WEIGHT = {"distance": 1.0, "speed": 1.0, "size": 1.0, "priority": 2.0}


def default_breakpoints() -> dict[str, np.ndarray]:
    """Her girdi icin 4 kirilma noktasi [b1, b2, b3, b4] (evrene gore normalize, 0-1).

    low    = yamuk (0, 0, b1, b2)
    medium = ucgen (b1, (b2+b3)/2, b4)
    high   = yamuk (b3, b4, 1, 1)
    Varsayilan: esit aralikli (0.25, 0.5, 0.5, 0.75). GA bu degerleri ayarlayacak.
    """
    return {k: np.array([0.25, 0.5, 0.5, 0.75]) for k in INPUTS}


def trapmf(x: np.ndarray, a: float, b: float, c: float, d: float) -> np.ndarray:
    """Yamuk uyelik fonksiyonu (a<=b<=c<=d). a==b veya c==d kenar durumlarini destekler."""
    x = np.asarray(x, dtype=float)
    y = np.zeros_like(x)
    y[(x >= b) & (x <= c)] = 1.0
    if b > a:
        m = (x > a) & (x < b)
        y[m] = (x[m] - a) / (b - a)
    if d > c:
        m = (x > c) & (x < d)
        y[m] = (d - x[m]) / (d - c)
    return y


def trimf(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    return trapmf(x, a, b, b, c)


@dataclass
class FuzzyPrioritySystem:
    """Edge dugumu icin gorev oncelik skoru ureten Mamdani FIS."""

    breakpoints: dict[str, np.ndarray] = field(default_factory=default_breakpoints)
    resolution: int = 201  # cikti evreninin ornek sayisi (centroid hassasiyeti)

    def __post_init__(self) -> None:
        self.y = np.linspace(*OUT_UNIVERSE, self.resolution)
        step = (OUT_UNIVERSE[1] - OUT_UNIVERSE[0]) / (len(OUT_TERMS) - 1)
        # Cikti MF'leri: tepeleri 0,25,50,75,100 olan ucgenler -> (5, resolution)
        self.out_mf = np.stack([
            trimf(self.y, c - step, c, c + step) for c in np.arange(len(OUT_TERMS)) * step
        ])
        self.rules, self.rule_out = self._build_rules()

    # ---------- Kural tabani ----------
    @staticmethod
    def _build_rules() -> tuple[np.ndarray, np.ndarray]:
        """81 kurali uret. rules[r] = her girdinin terim indeksi, rule_out[r] = cikti terimi."""
        rules, outs = [], []
        wsum = sum(RULE_WEIGHT.values())
        for combo in itertools.product(range(3), repeat=len(INPUTS)):
            score = 0.0
            for name, level in zip(INPUTS, combo):
                lvl = level if DIRECTION[name] > 0 else 2 - level
                score += RULE_WEIGHT[name] * lvl
            outs.append(int(round(score / (2 * wsum) * (len(OUT_TERMS) - 1))))
            rules.append(combo)
        return np.array(rules), np.array(outs)

    def rule_table(self) -> list[str]:
        """Kurallari okunabilir IF-THEN metni olarak dondur (rapor/sunum icin)."""
        lines = []
        for combo, o in zip(self.rules, self.rule_out):
            cond = " AND ".join(f"{n} is {IN_TERMS[t]}" for n, t in zip(INPUTS, combo))
            lines.append(f"IF {cond} THEN score is {OUT_TERMS[o]}")
        return lines

    # ---------- Bulaniklastirma ----------
    def input_mf_params(self, name: str) -> list[tuple[float, ...]]:
        lo, hi = UNIVERSE[name]
        b1, b2, b3, b4 = np.sort(self.breakpoints[name])
        s = lambda v: lo + v * (hi - lo)  # noqa: E731  normalize -> gercek birim
        return [
            (s(0), s(0), s(b1), s(b2)),            # low (yamuk)
            (s(b1), s((b2 + b3) / 2), s(b4)),      # medium (ucgen)
            (s(b3), s(b4), s(1), s(1)),            # high (yamuk)
        ]

    def fuzzify(self, name: str, x: np.ndarray) -> np.ndarray:
        """x: (N,) -> uyelik dereceleri (N, 3)."""
        x = np.clip(np.asarray(x, dtype=float), *UNIVERSE[name])
        p = self.input_mf_params(name)
        return np.stack([trapmf(x, *p[0]), trimf(x, *p[1]), trapmf(x, *p[2])], axis=-1)

    # ---------- Cikarim + durulastirma ----------
    def evaluate(self, distance, speed, size, priority) -> np.ndarray:
        """Vektorlu degerlendirme. Skaler veya dizi kabul eder, (N,) skor dondurur."""
        xs = [np.atleast_1d(np.asarray(v, dtype=float)) for v in (distance, speed, size, priority)]
        mu = [self.fuzzify(n, x) for n, x in zip(INPUTS, xs)]          # 4 x (N, 3)
        # Kural atesleme gucu: VE = min  -> (N, 81)
        firing = np.min(np.stack([m[:, self.rules[:, i]] for i, m in enumerate(mu)]), axis=0)
        # Her cikti terimi icin en guclu kural (birlestirme = max) -> (N, 5)
        alpha = np.zeros((firing.shape[0], len(OUT_TERMS)))
        for k in range(len(OUT_TERMS)):
            sel = self.rule_out == k
            if sel.any():
                alpha[:, k] = firing[:, sel].max(axis=1)
        # Implikasyon = min, birlestirme = max -> (N, resolution)
        agg = np.max(np.minimum(alpha[:, :, None], self.out_mf[None, :, :]), axis=1)
        den = agg.sum(axis=1)
        num = (agg * self.y).sum(axis=1)
        # Hicbir kural atesmezse (olmamali, kural tabani tam) orta deger
        return np.where(den > 0, num / np.where(den > 0, den, 1), 50.0)

    def score(self, distance, speed, size, priority) -> float:
        return float(self.evaluate(distance, speed, size, priority)[0])


if __name__ == "__main__":
    fis = FuzzyPrioritySystem()
    print(f"Kural sayisi: {len(fis.rules)}")
    print("Ornek kurallar:")
    for line in fis.rule_table()[:3] + fis.rule_table()[-2:]:
        print("  ", line)
    tests = {
        "yakin, yavas, buyuk, onemsiz gorev": (30, 5, 8.0, 0.1),
        "her sey orta": (125, 20, 5.0, 0.5),
        "menzilden cikiyor, hizli, kucuk, acil": (230, 35, 1.0, 0.9),
        "yakin ama cok acil gorev": (60, 10, 2.0, 0.95),
    }
    for desc, x in tests.items():
        print(f"{desc:40s} {x} -> skor = {fis.score(*x):5.1f}")
