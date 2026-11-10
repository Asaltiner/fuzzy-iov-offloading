# Checkpoint 2 — Uygulama Planı

## 1. Geliştirme ortamı
- **Python ≥ 3.10.** Kütüphaneler: NumPy, SciPy, pandas, Matplotlib, scikit-fuzzy (yalnızca doğrulama için), Streamlit (canlı demo).
- **Tekrar üretilebilirlik:** her koşu bir `seed` ile başlatılır. Sonuçlar `results/tables/*.csv` dosyalarına yazılır, grafikler bu CSV'lerden üretilir.

## 2. Simülatör tasarımı
Simülatör ayrık zamanlıdır (adım Δt = 0,1 s).

| Bileşen | Modelleme | Kaynak |
|---|---|---|
| Yol | 3 km'lik, çift yönlü, çok şeritli düz otoyol segmenti; uçlarda wrap-around | Makalede 3×3 km kent haritası var; sadeleştirdik (sınırlılık) |
| Hareket | Her araca U(10, 50) m/s hız atanır, her adımda küçük rastgele hız değişimi olur | Tablo 3 |
| Yoğunluk | 50–350 araç/km aralığı ölçekli araç sayısına çevrilir (bkz. not) | Tablo 3 |
| Bağlantı | Menzil 250 m; Nakagami-m başarı olasılığı, λ mesafeye göre 3 / 1,5 / 1 | Denk. 1–2 |
| İletim süresi | boyut / (6 Mbps), başarısız iletimde yeniden deneme | Tablo 3 |
| Görev üretimi | Poisson geliş; boyut U(0,5–10) Mb; CPU ihtiyacı ∝ boyut; öncelik U(0,1); deadline önceliğe bağlı | Varsayım |
| Düğüm kapasitesi | MIPS ∈ {poor, average, good} rastgele; tek çekirdekli kuyruk | Şek. 4'ten esinlenildi |
| Başarı | Sonuç, UN–EN bağlantısı kopmadan ve deadline geçmeden geri dönerse görev tamamlanmış sayılır | Varsayım |

**Not:** 350 araç/km × 3 km × çift yön ≈ 2000 araç eder. Hesap süresini makul tutmak için yoğunluk değerleri korunacak, gerekirse segment kısaltılacak.

## 3. Bulanık sistem (`src/fuzzy/fis.py`)

| Değişken | Evren | Terimler | MF tipi |
|---|---|---|---|
| mesafe | 0–250 m | low, medium, high | yamuk / üçgen / yamuk |
| bağıl hız | 0–40 m/s | low, medium, high | yamuk / üçgen / yamuk |
| görev boyutu | 0–10 Mb | low, medium, high | yamuk / üçgen / yamuk |
| öncelik | 0–1 | low, medium, high | yamuk / üçgen / yamuk |
| **skor (çıktı)** | 0–100 | very_low … very_high | üçgen |

- **Çıkarım:** Mamdani (VE = min, implikasyon = min, birleştirme = max). **Durulaştırma:** centroid.
- **Mamdani'yi seçme gerekçesi:** Makale çıkarım tipini belirtmiyor. Mamdani dilsel olarak yorumlanabilir ve savunmada kural açıklamak kolay. Sugeno ile karşılaştırma ablation olarak yapılacak.
- **Kural tabanı:** 81 kural. Aciliyet ilkesinden sistematik olarak üretiliyor:
  - Mesafe ↑ → skor ↑ (araç menzilden çıkmak üzere)
  - Bağıl hız ↑ → skor ↑ (bağlantı süresi kısa)
  - Görev boyutu ↓ → skor ↑ (shortest-job-first)
  - Öncelik ↑ → skor ↑ (ağırlık 2)
  - Makalenin ANFIS verisi olmadığı için kuralları veriden öğrenemiyoruz; bu durum sınırlılık olarak raporlanacak.
- **Doğrulama:** Kendi NumPy uygulamamız, aynı kurallarla kurulan scikit-fuzzy sistemiyle 25 rastgele girdide 0,5 puandan küçük farkla aynı sonucu veriyor. Ayrıca monotonluk ve çıktı aralığı testleri var (`tests/test_fis.py`).
- **Edge seçimi skoru (Denk. 5–9):** com_score = Σ w_x·MF_x. Önem skorları (I_x) varsayılan olarak eşit; duyarlılık analizi ek deney olarak yapılacak.

## 4. Baseline yöntemler
| Kod | Yöntem | Kuyruk disiplini |
|---|---|---|
| LPA | Görev yerelde işlenir | FIFO |
| RPA | Menzildeki rastgele bir araç seçilir | FIFO |
| CHGO | Tahmini işlem gecikmesi en düşük araç seçilir (global bilgiyle) | FIFO |
| NF | Araçlar MIPS'e göre sıralanır, kapasitesi uygun ilk araç seçilir | FIFO |
| **FUZZY (referans)** | Beacon tabanlı edge seçimi + bulanık öncelik kuyruğu | Bulanık skor |

## 5. Yeniden üretim deneyleri
- **E1:** yoğunluk ∈ {50, 100, 150, 200, 250, 300, 350} araç/km → ortalama gecikme (Şek. 9) ve tamamlama oranı (Şek. 11)
- **E2:** ortalama hız ∈ {10, 20, 30, 40, 50} m/s → tamamlama oranı (Şek. 12)
- Her nokta için 30 tekrar (makalede 50; süre kısıtı nedeniyle 30). Sonuçlar ortalama ± %95 güven aralığı olarak verilecek.
- **Makaleyle karşılaştırma:** Şek. 9/11/12 WebPlotDigitizer ile sayısallaştırılacak. Yöntem sıralaması Spearman korelasyonuyla, eğilim yönü ise eğimin işaretiyle karşılaştırılacak.

## 6. Özgün katkı planı (Checkpoint 4 taslağı)
**Ne değişecek?**
Elle (eşit aralıklı) tasarlanmış üyelik fonksiyonları yerine, kırılma noktaları **Genetik Algoritma ile optimize edilmiş** FIS kullanılacak (GA-FIS).
- Kromozom: 4 girdi × 4 kırılma noktası = 16 gen ∈ [0, 1]
- Fitness: eğitim senaryolarında (ayrı seed'ler) tamamlama oranı − α·normalize gecikme

**Neden?**
- Yazarlar gelecek çalışma olarak MF ve kural setlerinin GA veya DRL ile otomatik ayarlanmasını öneriyor.
- Kontrol yüzeyi (`results/figures/surface_distance_priority.png`) eşit aralıklı MF'lerde basamaklı ve düz bölgeler gösteriyor. Bu bölgelerde FIS, farklı aciliyetteki görevleri aynı skorla sıralıyor.

**Nasıl ölçülecek?**
- Baseline (elle tasarlanmış FIS) ile GA-FIS **aynı test seed'leriyle** koşturulacak. Eğitim ve test seed'leri ayrı tutulacak.
- Metrikler: tamamlama oranı, ortalama gecikme, kuyruk gecikmesi, FIS çalışma süresi (ms/karar).
- İstatistik: 30 tekrar, ortalama ± std, Wilcoxon işaretli sıra testi (p < 0,05).

**Ek deneyler:**
1. **Robustness:** Mesafe ve hız girdilerine %0–20 Gauss gürültüsü eklenir (GPS ve beacon hatasını temsil eder). FUZZY ile CHGO'nun performans düşüşü karşılaştırılır.
2. **Ablation:** centroid / bisector / MOM durulaştırma yöntemleri ve Mamdani / Sugeno (0. derece) karşılaştırılır.

## 7. Başarı ölçütleri
- **Yeniden üretim başarılı sayılır, eğer** FUZZY yöntemi yoğunluk ve hız eksenlerinin çoğunda baseline'lardan iyiyse ve eğilimler makaleyle aynı yöndeyse (yoğunluk ↑ → gecikme ↑, LPA en kötü).
- **Katkı:** GA-FIS'in istatistiksel olarak anlamlı bir iyileşme sağlaması beklenir. İyileşme çıkmazsa bunun nedenleri (aşırı uyum, fitness gürültüsü vb.) raporda tartışılacak; yönerge buna izin veriyor.
