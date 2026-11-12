# Fuzzy-Based Task Offloading in IoV Edge Computing — Reproduction & GA-Tuned Extension

> Bulanık Mantık Dersi Dönem Projesi

## Student Information
- **Ad Soyad:** Ahmet Sadık Altıner
- **Ders:** Bulanık Mantık

## Original Paper
Z. Trabelsi, M. Ali, and T. Qayyum, "Fuzzy-based task offloading in Internet of Vehicles (IoV) edge computing for latency-sensitive applications," *Internet of Things*, vol. 28, Art. no. 101392, 2024. doi: [10.1016/j.iot.2024.101392](https://doi.org/10.1016/j.iot.2024.101392)

## Problem Description
Araçların işlem kaynakları kısıtlıdır, bu yüzden görevler V2V ile komşu araçlara (edge node) aktarılır. Ancak yüksek hareketlilik bağlantıları kısa ömürlü yapar ve görevlerin aciliyeti birbirinden farklıdır. Referans çalışma iki adımlı bir çözüm öneriyor: (i) bağlantı süresini ve kaynağı dikkate alan bir edge seçimi, (ii) edge düğümünde bulanık mantıkla görev önceliklendirme.

## Method
Bulanık sistem şu şekilde kurgulandı:
- **Girdiler:** mesafe, bağıl hız, görev boyutu, görev önceliği. Her biri 3 terimli (low/medium/high).
- **Çıktı:** öncelik skoru (0–100). Edge kuyruğu bu skora göre sıralanır.
- **Çıkarım:** Mamdani (min/max), centroid durulaştırma, 81 kural.

Ayrıntılar: [`docs/01_makale_analizi.md`](docs/01_makale_analizi.md) ve [`docs/03_uygulama_plani.md`](docs/03_uygulama_plani.md).

## Fuzzy System Architecture
```
Beacon (konum, hız, MIPS) ──► Edge seçimi (Denk. 3–9) ──► Görev EN'ye gönderilir
                                                          │
           mesafe, hız, boyut, öncelik ──► Bulanıklaştırma ──► 81 kural (Mamdani)
                                                          ──► Birleştirme ──► Centroid ──► Skor ──► Öncelik kuyruğu
```
![Girdi üyelik fonksiyonları](results/figures/mf_inputs.png)

## Dataset
Referans çalışma simülasyon tabanlıdır (Veins + SUMO) ve veri paylaşılmamıştır. Bu projede veri, Python simülatörü tarafından tohum (seed) kontrollü olarak üretilir. Makaledeki grafiklerden sayısallaştırılan değerler `data/paper_digitized/` klasöründe tutulur.

## Installation
```bash
git clone https://github.com/<kullanici>/fuzzy-iov-offloading.git
cd fuzzy-iov-offloading
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Requirements
Python ≥ 3.10. Gerekli paketler `requirements.txt` dosyasında.

## How to Run
```bash
python -m src.fuzzy.fis                                   # FIS'i örnek girdilerle çalıştır, kuralları yazdır
python -m src.fuzzy.plot_fis                              # MF ve kontrol yüzeyi grafiklerini üret
python -m pytest -q                                       # 34 test (FIS doğrulaması, simülatör, GA)
python -m experiments.baseline.cp3_first_results          # tek senaryo, 6 yöntem, 10 seed (~10 s)
python -m experiments.baseline.run_sweep --exp density --reps 30   # E1: Şek. 9 ve 11
python -m experiments.baseline.run_sweep --exp speed   --reps 30   # E2: Şek. 12
python -m experiments.baseline.compare_with_paper --reps 30        # makaleyle karşılaştırma tabloları
python -m src.fuzzy.ga_tuning --pop 16 --gens 12 --tag ga_pilot    # GA-FIS (MF optimizasyonu)
python -m experiments.proposed.ga_pilot_holdout --tag ga_pilot     # GA-FIS'i test seed'lerinde kontrol et
```
Tek bir koşu Python içinden:
```python
from src.sim import SimConfig, run_simulation
run_simulation("FUZZY", SimConfig(density=200, mean_speed=30), seed=1)
```

## Reproduction Experiments
Python'da yazılmış, seed kontrollü ayrık zamanlı bir simülatör kullanılıyor (`src/sim/`). İçerik: iki yönlü halka otoyol, 250 m V2V menzili, Nakagami-m kanal (Denk. 1–2), beacon tabanlı edge seçimi (Denk. 3–9), EN'de bulanık öncelik kuyruğu. Karşılaştırılan yöntemler: LPA, RPA, CHGO, NF, FUZZY ve ablation için FUZZY_FIFO. Tasarım ve varsayımlar: [`docs/04_gun2_simulator.md`](docs/04_gun2_simulator.md).

| Deney | Değişken | Makale |
|---|---|---|
| E1 | yoğunluk 50–350 araç/km | Şek. 9 (gecikme), Şek. 11 (tamamlama) |
| E2 | ortalama hız 10–50 m/s | Şek. 12 (tamamlama) |

**İlk sonuçlar** (150 araç/km, 30 m/s, 10 seed): FUZZY tamamlama oranı 0,951 ± 0,006. En iyi baseline NF: 0,697 ± 0,015.

![CP3](results/figures/cp3_completion.png)

**30 tekrarlı sonuçlar:** FUZZY 19 noktanın hepsinde en iyi yöntem. En iyi baseline (NF) ile fark eşleştirilmiş Wilcoxon testinde anlamlı (p ≤ 1,7·10⁻⁶). Makaledeki 8 nitel iddianın 5'i tutuyor. Ayrıntılar: [`docs/05_gun3_cp4.md`](docs/05_gun3_cp4.md), [`results/tables/paper_comparison_r30.md`](results/tables/paper_comparison_r30.md).

![E1](results/figures/e1_density_completion_rate_r30.png)

## Proposed Extension
**GA-FIS:** 4 girdinin MF kırılma noktaları (16 gen) Genetik Algoritma ile optimize ediliyor (`src/fuzzy/ga_tuning.py`). Kural tabanı, çıkarım ve durulaştırma değişmiyor. Uygunluk ölçütü: tamamlama + 0,5·acil tamamlama − 0,2·normalize gecikme. Eğitim için normal ve yüksek yük senaryoları, ayrı eğitim seed'leri (101–103) kullanılıyor. Test seed'leri (1–30) GA tarafından hiç görülmüyor. Ek deneyler: gürültü/robustness analizi, durulaştırma ve Mamdani/Sugeno ablation'ı. Katkı önerisi (CP4): [`docs/05_gun3_cp4.md`](docs/05_gun3_cp4.md).

![GA-FIS MF](results/figures/ga_pilot_mf.png)

## Repository Structure
```
src/fuzzy/            Bulanık çıkarım sistemi (fis.py) ve grafikler
src/sim/              IoV simülatörü: hareket, kanal, görevler, yöntemler, deney yardımcıları
experiments/          baseline/ ve proposed/ deney betikleri
results/figures|tables  Üretilen grafikler ve CSV sonuçlar
docs/                 Makale analizi, literatür ve uygulama planı
report/ presentation/ Rapor ve sunum PDF'leri
references/           Kaynak listesi
tests/                Birim testleri
```

## References
Bkz. [`references/README.md`](references/README.md)
