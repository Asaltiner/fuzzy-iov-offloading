# Gün 4 — Checkpoint 5: Deneysel Sonuçlar (GA-FIS)

## 1. Özet
- **Tam GA koşusu:** 3 bağımsız GA seed'i × (24 birey, 20 nesil, uyarlanabilir mutasyon, 5 eğitim seed'i). Toplam 13.700 simülasyon, seed başına ~12 dk (2 çekirdek). Üç koşunun üçü de elle FIS'i eğitimde geçti (1,2034 → 1,2285–1,2313).
- **Seçim, doğrulama seed'leriyle (201–210) yapıldı.** Test seed'lerine (1–30) seçim aşamasında hiç bakılmadı. Seçilen koşu: `ga_full_s1`.
- **Test sonucu (30 seed, eşleştirilmiş Wilcoxon, Holm düzeltmesi):**
  - Yüksek yükte tamamlama oranı **+0,0138** (0,856 → 0,870, p = 5·10⁻⁸, 30 seed'in 28'inde daha iyi). Acil görevlerde +0,012 (p = 0,008).
  - Normal yükte tamamlama +0,0035 (p = 0,019), acil görevlerde +0,006 (p = 0,023).
  - Kazanç zorlaştıkça büyüyor: 350 araç/km'de tamamlama **+0,027**, acil görevlerde **+0,032** (p = 1,3·10⁻⁸). 50–100 araç/km'de fark anlamlı değil.
  - **Bedeli:** ortalama gecikme normal yükte +0,27 s, yüksek yükte +0,07 s arttı (Bölüm 4).
- **CP4'teki başarı ölçütü** ("yüksek yükte acil görevlerde anlamlı iyileşme, normal yükte kötüleşme yok") **sağlandı.** Gecikmedeki artış ise ölçütte öngörülmeyen bir ödünleşim olarak raporlanıyor.
- **Robustness:** %30'a kadar girdi gürültüsünde iki FIS de neredeyse hiç bozulmuyor (|Δ| < 0,002). GA-FIS'in üstünlüğü her gürültü düzeyinde korunuyor.
- **Ablation:** durulaştırma yöntemi (centroid/bisector/MOM) ve Mamdani/Sugeno seçimi sonucu anlamlı biçimde değiştirmiyor. Bulanık kuyruğu kapatmak (FIFO) ise yüksek yükte acil görev tamamlamayı **−0,037** düşürüyor (p = 5,6·10⁻⁸).
- **Hesaplama maliyeti:** FIS değerlendirmesi görev başına ~0,13 ms (NumPy). Aynı sistem scikit-fuzzy ile ~35 ms; bizim uygulamamız yaklaşık 180 kat hızlı. GA-FIS ek maliyet getirmiyor; MF sayısı ve kural sayısı aynı.
- **Canlı demo:** `streamlit run app.py` (Bölüm 7).

## 2. GA koşusu (CP4'teki önerilerin uygulanması)

| Ayar | Pilot (Gün 3) | Tam koşu (Gün 4) | Gerekçe |
|---|---|---|---|
| Popülasyon × nesil | 16 × 12 | 24 × 20 | Daha geniş arama |
| Eğitim seed'leri | 101–103 | 101–105 | Fitness gürültüsünü azaltmak |
| Mutasyon | sabit σ = 0,08 | uyarlanabilir: 3 nesil iyileşme yoksa σ × 1,5 (≤ 0,25); iyileşince 0,08 | Pilotta en iyi birey 0. nesilde takılmıştı |
| GA seed'i | 1 | 3 (1, 2, 3) | GA'nın kendi rastgeleliğine duyarlılık |
| Seçim | — | doğrulama seed'leri 201–210 | Test setine bakarak seçim yapmamak |

Yakınsama (`results/figures/ga_full_convergence.png`): Pilotun aksine üç koşuda da en iyi birey nesiller boyunca iyileşti (s1: 1,2204 → 1,2313). Uyarlanabilir mutasyon durağan dönemlerde σ'yı 0,25'e kadar çıkardı. s1'deki 6. nesil sıçraması ve s3'teki 11–16. nesil iyileşmeleri bu dönemlerin ardından geldi.

**Eğitim → doğrulama → test (iyimserlik yanlılığı):**

| Koşu | Eğitim F | Doğrulama F | Test F (normal) | Test F (yüksek yük) |
|---|---|---|---|---|
| ga_full_s1 (seçilen) | 1,2313 | 1,2045 | 1,2939 | 1,1316 |
| ga_full_s2 | 1,2285 | 1,2002 | 1,2966 | 1,1260 |
| ga_full_s3 | 1,2303 | 1,2036 | 1,2958 | 1,1339 |
| Elle FIS | 1,2034 | 1,1924 | 1,2922 | 1,1132 |

- Eğitimdeki kazanç (+0,028) doğrulamada +0,012'ye iniyor. Bu, pilotta da görülen iyimserlik yanlılığı.
- Üç GA koşusu test setinde birbirine çok yakın ve hepsi elle FIS'ten iyi. Yani sonuç tek bir şanslı GA koşusuna bağlı değil.
- Doğrulamada en iyi olan s1, testte her senaryoda en iyi değil (normalde s2, yüksek yükte s3 biraz önde). Aradaki farklar güven aralıklarının içinde. Seçimin önemi az, bu da istenen bir durum.

### Bulunan üyelik fonksiyonları (normalize, `results/figures/ga_full_mf.png`)

| Girdi | b1 | b2 | b3 | b4 | Yorum |
|---|---|---|---|---|---|
| mesafe | 0,216 | 0,236 | 0,745 | 0,927 | "low" yalnızca ~59 m'nin altı ve dik bir düşüşle bitiyor; "medium" çok geniş (54–232 m) |
| hız | 0,020 | 0,318 | 0,906 | 0,938 | "medium" 1–37 m/s arasını kaplıyor; "high" yalnızca > 36 m/s (neredeyse yalnız karşı yön) |
| boyut | 0,149 | 0,345 | 0,606 | 0,658 | "high" 6,1 Mb'den sonra hızlıca 1'e çıkıyor; büyük görevler net ayrılıyor |
| öncelik | 0,175 | 0,231 | 0,502 | 0,864 | "low" yalnızca p < 0,23; "high" yavaş yükselip 0,86'da doyuyor |

Gün 3 pilotundaki MF'lerle benzer olmaları beklenmiyordu (o koşu gürültülü bir 3 seed'lik fitness'a uyuyordu). Ortak nokta: üç koşunun hepsinde **mesafe "low" terimi daraldı**. Mesafe MF'leri edge seçimindeki MF_dist'i de belirlediği için, bu daralma yakın düğüme olan tercihin zayıfladığı anlamına geliyor (Bölüm 4).

## 3. Test sonuçları (seed 1–30)

Tam tablo: `results/tables/ga_test_summary.md`. Ham veri: `results/tables/ga_test_*_raw.csv`. İstatistik: `ga_test_wilcoxon.csv`.

### 3.1 Baseline / Geliştirilen / Değişim (yönerge 6.2)

**Yüksek yük (100 araç/km, 0,035 görev/s/araç)**

| Ölçüt | Elle FIS (baseline) | GA-FIS | Değişim | p (Holm) | Daha iyi / eşit / kötü seed |
|---|---|---|---|---|---|
| Tamamlama oranı | 0,8559 ± 0,0077 | 0,8697 ± 0,0072 | **+0,0138** (+%1,6) | 5,2·10⁻⁸ | 28 / 0 / 2 |
| Acil görev tamamlama | 0,7840 ± 0,0148 | 0,7959 ± 0,0120 | **+0,0119** | 0,008 | 21 / 1 / 8 |
| Gecikme (s, son teslim sınırlı) | 7,579 ± 0,073 | 7,654 ± 0,070 | +0,075 (kötü) | 5,6·10⁻⁹ | 1 / 0 / 29 |
| Uygunluk F | 1,1132 | 1,1316 | +0,0184 | 2,8·10⁻⁶ | 25 / 0 / 5 |
| FIS süresi (ms/görev) | 0,134 | 0,142 | +%5 (ölçüm gürültüsü düzeyinde) | – | – |

**Normal yük (150 araç/km, 0,015 görev/s/araç)**

| Ölçüt | Elle FIS | GA-FIS | Değişim | p (Holm) | İyi / eşit / kötü |
|---|---|---|---|---|---|
| Tamamlama oranı | 0,9480 ± 0,0046 | 0,9515 ± 0,0042 | +0,0035 | 0,019 | 19 / 3 / 8 |
| Acil görev tamamlama | 0,9142 ± 0,0077 | 0,9202 ± 0,0070 | +0,0060 | 0,023 | 21 / 1 / 8 |
| Gecikme (s) | 6,354 ± 0,082 | 6,622 ± 0,079 | +0,267 (kötü) | 3,7·10⁻⁹ | 0 / 0 / 30 |
| Uygunluk F | 1,2922 | 1,2939 | +0,0017 | 0,40 | 19 / 0 / 11 |

±: %95 güven aralığı yarı genişliği. Referans olarak en iyi baseline NF: normal 0,699, yüksek yük 0,607. Elle FIS ile GA-FIS arasındaki fark, FUZZY ile NF arasındaki farkın (~0,25) yanında küçük. Ancak tutarlı ve istatistiksel olarak anlamlı.

### 3.2 Yoğunluk taraması (T2, normal yük) — `ga_test_density_diff.png`

| Yoğunluk | 50 | 100 | 150 | 200 | 250 | 300 | 350 |
|---|---|---|---|---|---|---|---|
| ΔTamamlama | +0,002 | +0,001 | +0,004 | **+0,007** | **+0,012** | **+0,020** | **+0,027** |
| ΔAcil | +0,005 | +0,003 | +0,006 | **+0,020** | **+0,023** | **+0,030** | **+0,032** |
| ΔGecikme (s) | +0,16 | +0,28 | +0,27 | +0,16 | +0,06 | −0,00 | **−0,08** |

Kalın: p_Holm < 0,05. Yoğunluk arttıkça GA-FIS'in avantajı büyüyor. 300 araç/km'de gecikme farkı kayboluyor, 350'de GA-FIS gecikmede de daha iyi. Elle FIS'in en çok düştüğü bölge (0,948 → 0,834) GA-FIS'in en çok kazandırdığı bölge.

### 3.3 Yük taraması (T3, yeni senaryo, 100 araç/km) — `ga_test_load.png`

| Görev hızı | 0,015 | 0,025 | 0,035 | 0,045 |
|---|---|---|---|---|
| ΔTamamlama | +0,001 | **+0,009** | **+0,014** | **+0,019** |
| ΔAcil | +0,003 | **+0,010** | **+0,012** | **+0,013** |
| ΔGecikme (s) | +0,28 | +0,17 | +0,07 | +0,02 |

Aynı örüntü: yük arttıkça kazanç büyüyor, gecikme bedeli küçülüyor.

## 4. Tartışma: GA-FIS neden daha iyi, gecikme neden arttı?

Görev sonuç tablosundan (`ga_test_main_raw.csv`):

| | Kuyrukta bekleme (s) | Kuyruktan düşen görev | Tamamlanan görevin gecikmesi (s) |
|---|---|---|---|
| Normal, elle FIS | 0,48 | %4,8 | 6,06 |
| Normal, GA-FIS | **0,35** | **%4,3** | 6,36 |
| Yüksek yük, elle FIS | 0,77 | %13,6 | 6,81 |
| Yüksek yük, GA-FIS | **0,62** | **%12,0** | 6,97 |

- GA-FIS ile görevler **kuyrukta daha az bekliyor ve daha az düşüyor**. Tamamlama artışının ana kaynağı bu.
- Buna karşın tamamlanan görevlerin uçtan uca gecikmesi artıyor. Bekleme azaldığına göre artış iletim tarafından geliyor olmalı. En olası açıklama: daralan mesafe-"low" MF'si nedeniyle edge seçiminde yakınlığın ağırlığı azaldı. Seçim, daha uzaktaki ama daha boş ya da daha hızlı düğümlere kaydı. Uzak düğümde Nakagami-m kanalında yeniden iletim artar, yükleme süresi uzar.
  - **Bu açıklama bir hipotez.** Doğrudan ölçmedik (yükleme süresi ayrı kaydedilmiyor). Rapora "olası neden" olarak yazılmalı. Gün 5'te zaman kalırsa `upload_t` metriği eklenerek doğrulanabilir.
- Yüksek yoğunlukta yakın düğümler kalabalıklaşıyor. Bu durumda yük dengeleme kazancı iletim bedelinden büyük olduğu için gecikme de iyileşiyor (350 araç/km).
- **Fitness fonksiyonunun etkisi:** F'de gecikmenin ağırlığı (0,2 · gecikme / 11,25 s) küçük. 0,27 s'lik artış F'yi yalnızca ~0,005 düşürüyor, tamamlamadaki +0,0035 ve acil görevlerdeki 0,5 × 0,006 ise ~0,0065 artırıyor. GA tam olarak kendisine söyleneni optimize etti. Gecikme daha önemliyse λ_d büyütülmeli. Bu, çok amaçlı (Pareto) bir GA için doğal bir gelecek çalışma.
- Normal yükte F farkı anlamlı değil (p = 0,40). Tamamlama kazancı ile gecikme bedeli birbirini neredeyse götürüyor.

## 5. Robustness: girdi gürültüsü — `robustness_noise.png`, `robustness_summary.md`

Model: beacon'dan okunan mesafe ve bağıl hız x · (1 + N(0, σ)) olarak bozuluyor. Hareket, görevler ve kanal aynı. Yalnızca bulanık girdiler etkileniyor.

| σ | 0 | 0,05 | 0,10 | 0,20 | 0,30 |
|---|---|---|---|---|---|
| Elle FIS CR, yüksek yük | 0,8559 | 0,8557 | 0,8557 | 0,8554 | 0,8545 |
| GA-FIS CR, yüksek yük | 0,8697 | 0,8694 | 0,8700 | 0,8715 | 0,8706 |
| Δ (GA − elle), p_Holm | +0,014, 2·10⁻⁷ | +0,014 | +0,014 | +0,016 | +0,016, 2·10⁻⁸ |

- %30 gürültüde bile iki FIS'in tamamlama oranı en fazla 0,0015 değişiyor. **Bulanık sistem ölçüm gürültüsüne karşı çok dayanıklı.**
  - Neden 1: MF'ler geniş ve örtüşük. Küçük bir girdi kayması üyelik derecelerini az değiştiriyor.
  - Neden 2: edge seçimini asıl belirleyen LET/son teslim filtresi ve yük/CPU terimleri gürültüsüz.
- **Beklentimizin aksine** GA-FIS'in dik geçişleri onu kırılgan yapmadı; avantajı her σ'da korunuyor.
- Sınırlılık: gürültü LET hesabına uygulanmadı (gerçekte konum hatası LET'i de bozar). Bu yüzden sonuç "FIS girdilerinin gürültüsüne dayanıklılık" olarak yorumlanmalı, "konum hatasına dayanıklılık" olarak değil.

## 6. Ablation ve hesaplama maliyeti — `ablation_summary.md`, `ablation_urgent.png`

Tüm ablation karşılaştırmaları (5 varyant × 2 senaryo × 3 metrik = 30 test) Holm ile birlikte düzeltildi.

| Varyant (yüksek yük) | Tamamlama | ΔAcil | p | FIS ms/görev |
|---|---|---|---|---|
| Elle FIS (Mamdani + centroid) | 0,8559 | – | – | 0,12 |
| Bisector durulaştırma | 0,8564 | +0,001 | 1,0 | 0,12 |
| MOM durulaştırma | 0,8559 | −0,006 | 0,25 | 0,15 |
| Sugeno (0. derece) | 0,8542 | −0,002 | 1,0 | 0,11 |
| **FIFO kuyruk** (bulanık sıralama kapalı) | 0,8541 | **−0,037** | 5,6·10⁻⁸ | – |
| GA-FIS | **0,8697** | +0,012 | 0,083* | 0,14 |

\* Bu tabloda GA-FIS'in acil görev farkı 30 testlik geniş Holm ailesi içinde düzeltildiği için p = 0,083. Bölüm 3.1'deki düzeltmede (her metrik için iki senaryo üzerinden Holm) p = 0,008. Tamamlama farkı iki düzeltmede de anlamlı (p = 7·10⁻⁷).

- **Çıkarım/durulaştırma seçimi önemsiz:** üç durulaştırma yöntemi ve Sugeno anlamlı fark yaratmıyor. Kuyrukta yalnızca skorların **sırası** önemli. Bu yöntemler aynı kural tabanından hemen hemen aynı sıralamayı üretiyor.
- **Bulanık kuyruk önemli, ama yalnızca acil görevler için:** FIFO'ya geçince toplam tamamlama neredeyse değişmiyor (−0,002). Acil görevler ise belirgin şekilde kaybediyor (yüksek yükte −0,037, normalde −0,015). Gün 3'te "kuyruğun etkisi yok" gözlemi yalnızca **toplam** tamamlama için doğruydu. Kuyruk, aynı toplam içinde acil görevleri öne alıyor.
- **MF şekli (GA-FIS) önemli:** sonucu anlamlı biçimde değiştiren tek FIS parametresi MF şekli. Bunun nedeni, MF'lerin kuyruğun yanında edge seçimini de etkilemesi.

**Hesaplama maliyeti** (medyan, tek çekirdek, `fis_timing.csv`):

| Uygulama | Tek görev (ms) | 50 görevlik kuyruk (ms/görev) |
|---|---|---|
| Bizim NumPy Mamdani (elle veya GA) | 0,19 | 0,006 |
| Bizim NumPy Sugeno | 0,16 | 0,004 |
| scikit-fuzzy (aynı sistem) | 34,8 | – |

Vektörlü uygulama sayesinde bir simülasyondaki tüm FIS çağrıları toplam süreye ihmal edilebilir katkı yapıyor. Sugeno en hızlısı (durulaştırma integrali yok) ve sonuç farkı yaratmadığı için gerçek zamanlı bir araç üstü uygulamada tercih edilebilir.

## 7. Canlı demo (`app.py`)
```bash
streamlit run app.py
```
- **Canlı FIS:** kaydırıcılarla girdi → MF'ler üzerinde üyelik dereceleri, en güçlü 8 kural, kırpılmış çıktı kümeleri, centroid ve skor. Elle FIS / GA-FIS / Sugeno / Bisector / MOM arasında geçiş yapılabiliyor. Elle FIS'in MF'leri noktalı olarak üst üste çiziliyor.
- **Kontrol yüzeyi:** seçilen iki girdiye göre skor ısı haritası. Elle FIS ve seçilen FIS yan yana.
- **Mini simülasyon:** yoğunluk, hız, görev hızı, süre, seed ve gürültü seçilip yöntemler karşılaştırılıyor (120 s'lik bir koşu ~1 s). Hoca "farklı koşul" isterse buradan anında gösterilebilir.
- **Deney sonuçları:** bu belgedeki tablolar ve grafikler.

`streamlit.testing.AppTest` ile otomatik kontrol edildi: üç sekme ve simülasyon düğmesi hatasız çalışıyor.

## 8. Çalıştırma
```bash
python -m pytest -q                                   # 40 test
python -m src.fuzzy.ga_tuning --pop 24 --gens 20 --seeds 101 102 103 104 105 \
       --adaptive --ga-seed 1 --tag ga_full_s1          # her GA seed'i ~12 dk (2 çekirdek); 2 ve 3 için tekrarla
python -m experiments.proposed.ga_evaluate            # doğrulama + test T1–T3, ~8 dk
python -m experiments.proposed.robustness             # ~4 dk
python -m experiments.proposed.ablation               # ~3 dk
streamlit run app.py
```
GA koşuları uzun olduğu için sonuçları (`results/ga/ga_full_s*_best.json`, `ga_selected.json`) repoda tutuyoruz. Değerlendirme betikleri GA'yı yeniden koşmadan bu dosyalardan başlayabilir.

## 9. Bu aşamanın sınırlılıkları
- GA yalnızca girdi MF'lerini ayarlıyor. Kural tabanı ve çıktı MF'leri sabit.
- Gecikmedeki artışın nedeni (uzak düğüm seçimi) hipotez düzeyinde, ayrıca ölçülmedi.
- Fitness tek amaçlı ve ağırlıklar (0,5; 0,2) elle seçildi. Farklı ağırlıklar farklı bir ödünleşim noktası verir.
- Gürültü yalnızca FIS girdilerine uygulandı, LET hesabına uygulanmadı.
- Tüm sonuçlar kendi simülatörümüzde. Makaledeki Veins/SUMO ortamında GA-FIS'in kazancı farklı olabilir.
- FIS süreleri tek makinede ve paralel iş yükü altında ölçüldü. Mutlak değerler değil oranlar anlamlı.
