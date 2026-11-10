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
python -m src.fuzzy.fis          # FIS'i örnek girdilerle çalıştır, kuralları yazdır
python -m src.fuzzy.plot_fis     # MF ve kontrol yüzeyi grafiklerini üret
python -m pytest -q              # testler (scikit-fuzzy ile doğrulama dahil)
```
_Simülasyon ve deney komutları sonraki günlerde eklenecek._

## Reproduction Experiments
_Gün 3_ — Ortalama gecikme ve görev tamamlama oranının yoğunluğa göre değişimi (Şek. 9, 11); tamamlama oranının hıza göre değişimi (Şek. 12).

## Proposed Extension
_Gün 3–4_ — Üyelik fonksiyonlarının Genetik Algoritma ile optimizasyonu (GA-FIS), gürültü/robustness analizi, durulaştırma ablation'ı.

## Experimental Results
_Gün 4_

## Limitations
_Gün 5_

## Repository Structure
```
src/fuzzy/            Bulanık çıkarım sistemi (fis.py) ve grafikler
src/sim/              Araç ağı simülatörü (Gün 2)
experiments/          baseline/ ve proposed/ deney betikleri
results/figures|tables  Üretilen grafikler ve CSV sonuçlar
docs/                 Makale analizi, literatür ve uygulama planı
report/ presentation/ Rapor ve sunum PDF'leri
references/           Kaynak listesi
tests/                Birim testleri
```

## References
Bkz. [`references/README.md`](references/README.md)
