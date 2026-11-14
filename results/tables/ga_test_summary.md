# GA-FIS ve elle tasarlanmış FIS: test seed'leri 1–30 (eşleştirilmiş Wilcoxon, Holm)

Seçilen GA koşusu: `ga_full_s1` (doğrulama seed'leri 201–210).

## Normal yük (150 araç/km, 0,015 görev/s)

| Ölçüt | Elle FIS (baseline) | GA-FIS | Değişim | p (Holm) | K/B/E |
|---|---|---|---|---|---|
| Tamamlama oranı | 0.9480 ± 0.0046 | 0.9515 ± 0.0042 | +0.0035 ± 0.0028 | 0.019 * | 19/3/8 |
| Acil görev tamamlama | 0.9142 ± 0.0077 | 0.9202 ± 0.0070 | +0.0060 ± 0.0050 | 0.023 * | 21/1/8 |
| Gecikme (s) | 6.3541 ± 0.0820 | 6.6215 ± 0.0785 | +0.2674 ± 0.0218 | 3.7e-09 * | 30/0/0 |
| Uygunluk F | 1.2922 ± 0.0094 | 1.2939 ± 0.0084 | +0.0017 ± 0.0050 | 0.404 | 19/0/11 |
| FIS süresi (ms/görev) | 0.1417 | 0.1449 | +2.2 % | – | – |

## Yüksek yük (100 araç/km, 0,035 görev/s)

| Ölçüt | Elle FIS (baseline) | GA-FIS | Değişim | p (Holm) | K/B/E |
|---|---|---|---|---|---|
| Tamamlama oranı | 0.8559 ± 0.0077 | 0.8697 ± 0.0072 | +0.0138 ± 0.0027 | 5.2e-08 * | 28/0/2 |
| Acil görev tamamlama | 0.7840 ± 0.0148 | 0.7959 ± 0.0120 | +0.0119 ± 0.0070 | 0.008 * | 21/1/8 |
| Gecikme (s) | 7.5789 ± 0.0730 | 7.6535 ± 0.0704 | +0.0746 ± 0.0188 | 5.6e-09 * | 29/0/1 |
| Uygunluk F | 1.1132 ± 0.0158 | 1.1316 ± 0.0140 | +0.0184 ± 0.0055 | 2.8e-06 * | 25/0/5 |
| FIS süresi (ms/görev) | 0.1343 | 0.1416 | +5.4 % | – | – |

K/B/E: GA-FIS'in elle FIS'ten iyi / eşit / kötü olduğu seed sayısı (gecikmede 'iyi' = artış; yorumlarken işarete dikkat). * : p_Holm < 0,05.

## Yoğunluk ve yük taramaları (GA-FIS − Elle FIS)

| Deney | x | ΔTamamlama | p | ΔAcil | p | ΔGecikme (s) | p |
|---|---|---|---|---|---|---|---|
| yoğunluk | 50 | +0.0017 | 0.584 | +0.0049 | 0.550 | +0.1602 | 7.5e-08* |
| yoğunluk | 100 | +0.0008 | 0.584 | +0.0029 | 0.550 | +0.2755 | 1.3e-08* |
| yoğunluk | 150 | +0.0035 | 0.056 | +0.0060 | 0.068 | +0.2674 | 1.3e-08* |
| yoğunluk | 200 | +0.0071 | 1.3e-04* | +0.0195 | 1.3e-06* | +0.1644 | 1.3e-08* |
| yoğunluk | 250 | +0.0123 | 3.2e-05* | +0.0225 | 3.2e-05* | +0.0637 | 2.1e-05* |
| yoğunluk | 300 | +0.0195 | 1.3e-08* | +0.0301 | 5.6e-08* | -0.0044 | 0.984 |
| yoğunluk | 350 | +0.0273 | 1.3e-08* | +0.0318 | 1.3e-08* | -0.0798 | 1.1e-07* |
| görev hızı | 0.015 | +0.0008 | 0.397 | +0.0029 | 0.353 | +0.2755 | 7.5e-09* |
| görev hızı | 0.025 | +0.0087 | 1.6e-05* | +0.0098 | 0.009* | +0.1662 | 7.5e-09* |
| görev hızı | 0.035 | +0.0138 | 7.8e-08* | +0.0119 | 0.009* | +0.0746 | 1.1e-08* |
| görev hızı | 0.045 | +0.0189 | 7.5e-09* | +0.0132 | 9.3e-04* | +0.0211 | 0.007* |

## GA seed'ine duyarlılık (test seed'leri, ortalama uygunluk)

| Koşu | Eğitim F | Doğrulama F | Test F normal | Test F yüksek yük |
|---|---|---|---|---|
| ga_full_s1 | 1.2313 | 1.2045 | 1.2939 | 1.1316 |
| ga_full_s2 | 1.2285 | 1.2002 | 1.2966 | 1.1260 |
| ga_full_s3 | 1.2303 | 1.2036 | 1.2958 | 1.1339 |
| Elle FIS | 1.2034 | 1.1924 | 1.2922 | 1.1132 |
