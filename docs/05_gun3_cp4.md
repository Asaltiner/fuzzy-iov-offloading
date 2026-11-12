# Gün 3 — Yeniden Üretim Deneyleri (30 tekrar) ve Checkpoint 4: Katkı Önerisi

## 1. Özet
- E1 (yoğunluk) ve E2 (hız) deneyleri **30 tekrarla** koşturuldu: 2.160 simülasyon, 2 çekirdekte ≈ 4 dk.
- Makaleyle karşılaştırma otomatikleştirildi (`experiments/baseline/compare_with_paper.py`). Makaledeki 8 nitel iddianın **5'i** bizim sonuçlarımızla uyumlu.
- FUZZY, 19 karşılaştırma noktasının hepsinde en iyi baseline'dan (her noktada NF) anlamlı olarak iyi. Eşleştirilmiş Wilcoxon testinde p ≤ 1,7·10⁻⁶.
- GA-FIS kodu yazıldı (`src/fuzzy/ga_tuning.py`, 8 yeni test, toplam 34/34). Pilot GA koşusu yapıldı (16 birey × 12 nesil, 1.098 simülasyon, 140 s). Test seed'lerinde küçük ama tutarlı bir iyileşme görüldü (Bölüm 5.4).

## 2. E1 ve E2 sonuçları (30 tekrar, tamamlama oranı ortalaması)

**E1 — yoğunluk (30 m/s)**

| Yöntem | 50 | 100 | 150 | 200 | 250 | 300 | 350 |
|:--|--:|--:|--:|--:|--:|--:|--:|
| LPA | 0,588 | 0,584 | 0,584 | 0,589 | 0,587 | 0,586 | 0,584 |
| RPA | 0,333 | 0,323 | 0,313 | 0,307 | 0,293 | 0,277 | 0,251 |
| CHGO | 0,623 | 0,578 | 0,537 | 0,495 | 0,454 | 0,412 | 0,372 |
| NF | 0,686 | 0,699 | 0,699 | 0,700 | 0,690 | 0,683 | 0,664 |
| **FUZZY** | **0,933** | **0,954** | **0,948** | **0,938** | **0,916** | **0,885** | **0,834** |
| FUZZY_FIFO | 0,934 | 0,954 | 0,947 | 0,936 | 0,914 | 0,884 | 0,833 |

**E2 — hız (150 araç/km)**

| Yöntem | 10 | 20 | 30 | 40 | 50 m/s |
|:--|--:|--:|--:|--:|--:|
| LPA | 0,584 | 0,584 | 0,584 | 0,584 | 0,584 |
| RPA | 0,421 | 0,354 | 0,313 | 0,290 | 0,276 |
| CHGO | 0,698 | 0,603 | 0,537 | 0,497 | 0,476 |
| NF | 0,888 | 0,775 | 0,699 | 0,653 | 0,641 |
| **FUZZY** | **0,953** | **0,950** | **0,948** | **0,948** | **0,947** |
| FUZZY_FIFO | 0,952 | 0,949 | 0,947 | 0,947 | 0,947 |

5 tekrarlı ön sonuçlarla fark en fazla 0,01. Sıralamalar değişmedi.

Grafikler: `results/figures/e1_density_*_r30.png`, `e2_speed_*_r30.png`, `rank_heatmap_r30.png`.
Ham ve özet tablolar: `results/tables/e1_density_*_r30.csv`, `e2_speed_*_r30.csv`.

## 3. Makaleyle karşılaştırma

Yöntem: `compare_with_paper.py` üç katmanda karşılaştırma yapıyor.
1. **Eğilim:** her yöntem için metrik ile x (yoğunluk/hız) arasında Spearman ρ hesaplanıyor (koşu düzeyinde, n = 210 veya 150).
2. **Sıralama ve istatistik:** her noktada yöntem sıralaması çıkarılıyor. FUZZY, o noktadaki en iyi baseline ile eşleştirilmiş Wilcoxon testiyle karşılaştırılıyor. Testin eşleştirilmiş olması, aynı seed'in her yöntemde aynı trafik ve görev akışını üretmesinden geliyor (ortak rastgele sayılar).
3. **Sayısal karşılaştırma:** Şek. 9/11/12 sayısallaştırıldığında bizim eğrilerimiz ile makalenin eğrileri arasında Spearman ρ hesaplanacak. Hem eğri şekli hem de her noktadaki sıralama uyumu ölçülecek. **CSV'ler hâlâ boş olduğu için bu katman henüz çalışmadı.**

| Makaledeki iddia | Şekil | Bizde | Uyum |
|---|---|---|---|
| Önerilen yöntem tüm yoğunluklarda en düşük gecikmeye sahip | 9 | 7/7 noktada 1. | ✅ |
| Önerilen yöntem tüm noktalarda en yüksek tamamlama oranına sahip | 11–12 | 12/12 noktada 1. | ✅ |
| Yoğunluk arttıkça gecikme artıyor | 9 | RPA, CHGO, NF ve FUZZY'de anlamlı artış (ρ = 0,74–0,98). LPA'da etki yok. | ✅ |
| CHGO yoğun ağda zayıflıyor | 11 | ρ = −0,99 | ✅ |
| NF yoğun bölgelerde güçlü ve kararlı | 11 | 50→350 araç/km arasında en küçük düşüş NF'de (−0,022) | ✅ |
| CHGO hıza karşı tutarlı | 12 | ρ = −0,96 (0,70 → 0,48) | ❌ |
| LPA en kötü yöntem | 11–12 | 12/12 noktada en kötü RPA | ❌ |
| Yüksek yoğunlukta RPA > LPA | 11 | 350 araç/km'de RPA 0,251, LPA 0,584 | ❌ |

**Uyum: 5/8.** Önerilen yöntemin üstünlüğü ve yoğunluk eğilimleri birebir tutuyor. Uyumsuzluklar, makalenin vermediği baseline ayrıntılarından kaynaklanıyor (nedenleri docs/04 §6'da):
- LPA bizde kanal kullanmıyor; yoğunluk ve hızdan bağımsız.
- RPA, düğümlerin %50'sinin zayıf olduğu kapasite dağılımında çok kötü sonuç veriyor.
- CHGO'muz hareketliliği hiç dikkate almıyor.

**Yeni gözlem (30 tekrarla netleşti):** FUZZY'nin hızla ilişkisi istatistiksel olarak anlamlı değil (ρ = −0,16, p = 0,06; 0,953 → 0,947). Bu, makalenin "hareketliliğe dayanıklı" iddiasını destekliyor. Kaynağı, edge seçimindeki LET filtresi.

**Bulanık kuyruğun genel katkısı:** FUZZY ile FUZZY_FIFO arasındaki fark tüm noktalarda 0,002'den küçük. Normal yükte genel tamamlama oranını belirleyen edge seçimi, kuyruk sıralaması değil. Bu yüzden GA deneyine yüksek yük senaryosu ekledik.

## 4. Checkpoint 4 — Katkı önerisi

### 4.1 Ne değiştirilecek?
Elle tasarlanmış FIS'in eşit aralıklı üyelik fonksiyonları (her girdi için kırılma noktaları 0,25 / 0,5 / 0,5 / 0,75) yerine, kırılma noktaları **Genetik Algoritma ile optimize edilmiş GA-FIS** kullanılacak.

- **Değişmeyenler:** kural tabanı (81 kural), çıkarım (Mamdani min/max), durulaştırma (centroid), edge seçim formülü, simülatör. Böylece gözlenen fark yalnızca MF şekline atfedilebilir.
- **Kromozom:** 4 girdi × 4 kırılma noktası = 16 gerçek değerli gen, normalize [0, 1].
  - low = yamuk(0, 0, b1, b2)
  - medium = üçgen(b1, (b2+b3)/2, b4)
  - high = yamuk(b3, b4, 1, 1)
- **Onarım:** her girdinin genleri sıralanıyor, [0,02; 0,94] aralığına kırpılıyor ve rampalara en az 0,02 genişlik bırakılıyor. Böylece her birey geçerli bir FIS'e karşılık geliyor. Varsayılan genom onarımdan değişmeden geçiyor ve elle tasarlanmış FIS'i birebir üretiyor (test edildi).

### 4.2 Neden?
1. **Makale MF parametrelerini vermiyor.** Bizim eşit aralıklı seçimimiz keyfi bir varsayım. Bu varsayımın sonuca etkisi ölçülmeli.
2. **Yazarlar MF ve kuralların GA veya DRL ile otomatik ayarlanmasını gelecek çalışma olarak öneriyor.**
3. **Mesafe ve hız MF'leri iki yerde kullanılıyor:** edge seçimindeki com_score'da ve EN kuyruğundaki öncelik skorunda. MF şekli iki aşamayı birlikte etkiliyor. Bu nedenle tek bir parametre seti üzerinden uçtan uca ayar anlamlı.
4. **Kontrol yüzeyi eşit aralıklı MF'lerde basamaklı** (`surface_distance_priority.png`). Düz bölgelerde farklı aciliyetteki görevler aynı skoru alıyor.

### 4.3 GA tasarımı (`src/fuzzy/ga_tuning.py`)

| Bileşen | Seçim | Gerekçe |
|---|---|---|
| Kodlama | Gerçek değerli, 16 gen | Kırılma noktaları sürekli |
| Başlangıç | 1 elle FIS + 15 rastgele birey | Seeding: GA en kötü ihtimalle baseline'ı korur |
| Seçim | Turnuva, k = 3 | Ölçekten bağımsız, gürültülü fitness'a dayanıklı |
| Çaprazlama | BLX-α (α = 0,3), p = 0,9 | Gerçek kodlu GA'da standart |
| Mutasyon | Gauss, σ = 0,08, birey başına ortalama 2 gen | Yerel arama |
| Elitizm | En iyi 2 birey aynen aktarılır | En iyi fitness monoton (test edildi) |
| Önbellek | Aynı genom tekrar simüle edilmez | Hesap tasarrufu |
| Paralellik | ProcessPoolExecutor | Birey × senaryo × seed işleri |

**Uygunluk fonksiyonu** (eğitim senaryoları × eğitim seed'leri ortalaması):

  F = CR + 0,5 · CR_acil − 0,2 · (gecikme / D̄)

- CR: tamamlama oranı
- CR_acil: p ≥ 0,7 olan görevlerin tamamlama oranı (bulanık kuyruğun asıl etki alanı)
- gecikme: son teslim sınırlı ortalama gecikme
- D̄ = 3 + 5,25 + 3 = 11,25 s: ortalama göreli son teslim süresi

**Eğitim senaryoları:**
- normal: 150 araç/km, 30 m/s, görev hızı 0,015
- yüksek yük: 100 araç/km, 30 m/s, görev hızı 0,035

Her senaryo 200 s simüle ediliyor. Eğitim seed'leri **101, 102, 103**.

### 4.4 Başarı nasıl ölçülecek? (Gün 4)
- **Test seed'leri 1–30.** GA bu seed'leri hiç görmüyor; eğitim ve test ayrımı aşırı uyumu ölçmeyi sağlıyor.
- **Karşılaştırma:** FUZZY (elle FIS) ile FUZZY (GA-FIS). Aynı simülatör ve aynı seed'ler kullanılıyor. Senaryolar: E1 yoğunluk taraması, normal yük ve yüksek yük.
- **Metrikler:** tamamlama oranı, acil görev tamamlama oranı, ortalama gecikme, FIS çalışma süresi (ms/görev).
- **İstatistik:** 30 tekrar, ortalama ± %95 güven aralığı, eşleştirilmiş Wilcoxon (p < 0,05). Aynı seed iki varyantta aynı trafiği ürettiği için eşleştirme geçerli.
- **Başarı ölçütü:** GA-FIS, yüksek yük senaryosunda acil görev tamamlama oranında elle FIS'ten anlamlı olarak iyi olmalı ve normal yükte kötüleşmemeli.
- **İyileşme çıkmazsa:** sonuç nedenleriyle (fitness gürültüsü, aşırı uyum, kuyruğun düşük etkisi) tartışılacak. Yönerge buna izin veriyor.
- **Ek deneyler:** gürültü robustness'ı (mesafe/hız girdilerine %0–20 Gauss gürültüsü) ve ablation (durulaştırma: centroid / bisector / MOM; Mamdani / Sugeno).

## 5. Pilot GA koşusu (16 birey × 12 nesil)

### 5.1 Yakınsama
| Nesil | En iyi | Popülasyon ortalaması | Elle FIS |
|---|---|---|---|
| 0 | 1,2303 | 1,2112 | 1,2030 |
| 6 | 1,2303 | 1,2210 | 1,2030 |
| 12 | 1,2303 | 1,2242 | 1,2030 |

1.098 simülasyon, 140 s. Grafikler: `results/figures/ga_pilot_convergence.png` ve `ga_pilot_mf.png`.

### 5.2 Bulunan MF'ler (normalize)
| Girdi | b1 | b2 | b3 | b4 | Yorum |
|---|---|---|---|---|---|
| mesafe | 0,206 | 0,551 | 0,879 | 0,899 | "high" yalnızca ≈ 220 m'den sonra, dik bir geçişle başlıyor. Bu, menzil sınırına çok yakın araçları ayırıyor. |
| hız | 0,021 | 0,263 | 0,282 | 0,416 | Hız MF'leri 0–17 m/s'ye sıkışmış. 17 m/s üstü bağıl hız zaten "high". |
| boyut | 0,178 | 0,271 | 0,588 | 0,919 | "low" dar (< 2,7 Mb), "medium" geniş. |
| öncelik | 0,428 | 0,493 | 0,532 | 0,637 | Geçişler 0,43–0,64 aralığında dik. Öncelik neredeyse ikili bir eşik gibi davranıyor. |

### 5.3 Gözlemler
- **En iyi birey 0. nesildeki rastgele bir birey ve 12 nesil boyunca hiç değişmedi.** Popülasyon ortalaması ise yükseldi (1,211 → 1,224). Bu iki şeye işaret ediyor:
  - Uygunluk yüzeyi düz veya gürültülü. 3 seed × 2 senaryo ile ölçülen fitness'ın standart hatası, bireyler arası farklarla aynı mertebede.
  - Mutasyon adımı (σ = 0,08, 2 gen) iyi bölgeden kaçmayı zorlaştırıyor.
- **Gün 4 için ayar önerileri:**
  - Eğitim seed sayısını 5'e çıkarmak (gürültüyü azaltır).
  - Popülasyonu 24'e, nesil sayısını 20'ye çıkarmak.
  - Uyarlanabilir mutasyon (σ'yı durağanlıkta artırmak).

  Bu ayarlarla tahmini süre ≈ 6–8 dk.

### 5.4 Test seed'lerinde ön kontrol (seed 1–10, 300 s)
`experiments/proposed/ga_pilot_holdout.py`

| Senaryo | Varyant | Fitness | Tamamlama | Acil tamamlama | Gecikme (s) |
|---|---|---|---|---|---|
| normal | Elle FIS | 1,2978 | 0,9513 | 0,9189 | 6,358 |
| normal | GA-FIS | 1,3019 | 0,9556 | 0,9196 | 6,388 |
| yüksek yük | Elle FIS | 1,0998 | 0,8505 | 0,7704 | 7,645 |
| yüksek yük | GA-FIS | 1,1088 | 0,8549 | 0,7783 | 7,607 |

- Test seed'lerinde iyileşme küçük ama iki senaryoda da aynı yönde: tamamlama +0,004; yüksek yükte acil görevlerde +0,008.
- Eğitimdeki fitness kazancı (+0,027), testtekinden (+0,004 / +0,009) belirgin biçimde büyük. **Bu, beklenen iyimserlik yanlılığının (aşırı uyum) bir göstergesi.** Eğitim/test ayrımının neden gerekli olduğunu gösteren iyi bir örnek; raporda tartışılacak.
- Bu tablo yalnızca 10 seed'lik bir ön kontrol, anlamlılık testi yapılmadı. Asıl sonuç Gün 4'te 30 test seed'i ve Wilcoxon testiyle üretilecek.

## 6. Çalıştırma
```bash
python -m pytest -q                                              # 34 test
python -m experiments.baseline.run_sweep --exp density --reps 30 # E1, ~2,5 dk (2 çekirdek)
python -m experiments.baseline.run_sweep --exp speed   --reps 30 # E2, ~1,5 dk
python -m experiments.baseline.compare_with_paper --reps 30      # karşılaştırma tabloları
python -m src.fuzzy.ga_tuning --smoke                            # GA kod kontrolü, ~5 s
python -m src.fuzzy.ga_tuning --pop 16 --gens 12 --tag ga_pilot  # pilot GA, ~2,5 dk
python -m experiments.proposed.ga_pilot_holdout --tag ga_pilot   # test seed ön kontrolü, ~1 dk
```

## 7. Sınırlılıklar (bu aşama)
- Makale şekilleri henüz sayısallaştırılmadı, bu yüzden karşılaştırma nitel düzeyde (eğilim ve sıralama).
- GA yalnızca MF'leri ayarlıyor; kural tabanı ve çıktı MF'leri sabit.
- Pilot GA tek GA seed'iyle koşuldu. GA'nın kendi rastgeleliğine duyarlılık Gün 4'te 2–3 GA seed'iyle kontrol edilebilir.
