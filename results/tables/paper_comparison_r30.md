# Makaleyle karşılaştırma (30 tekrar)

## 1. Nitel iddialar

| iddia                                                        | kaynak     | bizim sonuç                                           | uyumlu   |
|:-------------------------------------------------------------|:-----------|:------------------------------------------------------|:---------|
| Önerilen yöntem tüm yoğunluklarda en düşük gecikme           | Şek. 9     | 7/7 noktada 1.                                        | ✅        |
| Önerilen yöntem tüm yoğunluk ve hızlarda en yüksek tamamlama | Şek. 11–12 | 12/12 noktada 1.                                      | ✅        |
| Yoğunluk ↑ → gecikme ↑                                       | Şek. 9     | anlamlı artış (ρ>0, p<0,05): RPA, CHGO, NF, FUZZY     | ✅        |
| CHGO hıza karşı tutarlı                                      | Şek. 12    | CHGO ρ(hız, tamamlama) = -0.96                        | ❌        |
| CHGO yoğun ağda zayıf                                        | Şek. 11    | CHGO ρ(yoğunluk, tamamlama) = -0.99                   | ✅        |
| NF yoğun bölgelerde güçlü/kararlı                            | Şek. 11    | |Δ tamamlama| 50→350: RPA 0.083, CHGO 0.250, NF 0.022 | ✅        |
| LPA en kötü yöntem                                           | Şek. 11–12 | LPA 0/12 noktada son; en kötü: {'RPA': 12}            | ❌        |
| Yüksek yoğunlukta RPA > LPA                                  | Şek. 11    | 350 araç/km: RPA 0.251, LPA 0.584                     | ❌        |

Uyum: **5/8**

## 2. Eğilim (Spearman ρ, koşu düzeyinde)

| exp         | method     | metric          |      rho |         p |   first |   last |   change |
|:------------|:-----------|:----------------|---------:|----------:|--------:|-------:|---------:|
| E1 yoğunluk | LPA        | avg_delay       | -0.0168  | 0.809     |   8.67  |  8.73  |  0.0531  |
| E1 yoğunluk | LPA        | completion_rate | -0.00695 | 0.92      |   0.588 |  0.584 | -0.00434 |
| E1 yoğunluk | RPA        | avg_delay       |  0.742   | 6.32e-38  |   9.84  | 10.4   |  0.523   |
| E1 yoğunluk | RPA        | completion_rate | -0.844   | 3.99e-58  |   0.333 |  0.251 | -0.0828  |
| E1 yoğunluk | CHGO       | avg_delay       |  0.982   | 2.92e-153 |   7.77  |  9.77  |  2       |
| E1 yoğunluk | CHGO       | completion_rate | -0.985   | 6.13e-161 |   0.623 |  0.372 | -0.25    |
| E1 yoğunluk | NF         | avg_delay       |  0.808   | 9.07e-50  |   7.38  |  8.44  |  1.06    |
| E1 yoğunluk | NF         | completion_rate | -0.324   | 1.62e-06  |   0.686 |  0.664 | -0.0219  |
| E1 yoğunluk | FUZZY      | avg_delay       |  0.742   | 5.98e-38  |   6.65  |  7.89  |  1.25    |
| E1 yoğunluk | FUZZY      | completion_rate | -0.777   | 9.16e-44  |   0.933 |  0.834 | -0.0993  |
| E1 yoğunluk | FUZZY_FIFO | avg_delay       |  0.742   | 4.95e-38  |   6.64  |  7.89  |  1.25    |
| E1 yoğunluk | FUZZY_FIFO | completion_rate | -0.795   | 5.53e-47  |   0.934 |  0.833 | -0.101   |
| E2 hız      | LPA        | completion_rate |  0       | 1         |   0.584 |  0.584 |  0       |
| E2 hız      | RPA        | completion_rate | -0.929   | 9.23e-66  |   0.421 |  0.276 | -0.145   |
| E2 hız      | CHGO       | completion_rate | -0.956   | 1.4e-80   |   0.698 |  0.476 | -0.222   |
| E2 hız      | NF         | completion_rate | -0.933   | 1.6e-67   |   0.888 |  0.641 | -0.247   |
| E2 hız      | FUZZY      | completion_rate | -0.155   | 0.0587    |   0.953 |  0.947 | -0.00525 |
| E2 hız      | FUZZY_FIFO | completion_rate | -0.107   | 0.193     |   0.952 |  0.947 | -0.00442 |

## 3. FUZZY vs. en iyi baseline (eşleştirilmiş Wilcoxon)

| param      |   x | metric          | best_baseline   |   fuzzy_mean |   baseline_mean |    diff |   wilcoxon_p | fuzzy_better   |
|:-----------|----:|:----------------|:----------------|-------------:|----------------:|--------:|-------------:|:---------------|
| density    |  50 | completion_rate | NF              |        0.933 |           0.686 |  0.248  |     1.86e-09 | True           |
| density    | 100 | completion_rate | NF              |        0.954 |           0.699 |  0.255  |     1.86e-09 | True           |
| density    | 150 | completion_rate | NF              |        0.948 |           0.699 |  0.249  |     1.86e-09 | True           |
| density    | 200 | completion_rate | NF              |        0.938 |           0.7   |  0.238  |     1.86e-09 | True           |
| density    | 250 | completion_rate | NF              |        0.916 |           0.69  |  0.225  |     1.86e-09 | True           |
| density    | 300 | completion_rate | NF              |        0.885 |           0.683 |  0.202  |     1.86e-09 | True           |
| density    | 350 | completion_rate | NF              |        0.834 |           0.664 |  0.17   |     1.73e-06 | True           |
| density    |  50 | avg_delay       | NF              |        6.65  |           7.38  | -0.733  |     1.86e-09 | True           |
| density    | 100 | avg_delay       | NF              |        6.37  |           7.35  | -0.982  |     1.86e-09 | True           |
| density    | 150 | avg_delay       | NF              |        6.35  |           7.43  | -1.07   |     1.86e-09 | True           |
| density    | 200 | avg_delay       | NF              |        6.52  |           7.55  | -1.03   |     1.86e-09 | True           |
| density    | 250 | avg_delay       | NF              |        6.88  |           7.79  | -0.914  |     1.86e-09 | True           |
| density    | 300 | avg_delay       | NF              |        7.32  |           8.07  | -0.749  |     1.86e-09 | True           |
| density    | 350 | avg_delay       | NF              |        7.89  |           8.44  | -0.547  |     1.86e-09 | True           |
| mean_speed |  10 | completion_rate | NF              |        0.953 |           0.888 |  0.0647 |     1.86e-09 | True           |
| mean_speed |  20 | completion_rate | NF              |        0.95  |           0.775 |  0.175  |     1.86e-09 | True           |
| mean_speed |  30 | completion_rate | NF              |        0.948 |           0.699 |  0.249  |     1.86e-09 | True           |
| mean_speed |  40 | completion_rate | NF              |        0.948 |           0.653 |  0.294  |     1.86e-09 | True           |
| mean_speed |  50 | completion_rate | NF              |        0.947 |           0.641 |  0.306  |     1.86e-09 | True           |

## Sıralama — E1 tamamlama (1 = en iyi)

|   density |   LPA |   RPA |   CHGO |   NF |   FUZZY |
|----------:|------:|------:|-------:|-----:|--------:|
|        50 |     4 |     5 |      3 |    2 |       1 |
|       100 |     3 |     5 |      4 |    2 |       1 |
|       150 |     3 |     5 |      4 |    2 |       1 |
|       200 |     3 |     5 |      4 |    2 |       1 |
|       250 |     3 |     5 |      4 |    2 |       1 |
|       300 |     3 |     5 |      4 |    2 |       1 |
|       350 |     3 |     5 |      4 |    2 |       1 |

## Sıralama — E1 gecikme

|   density |   LPA |   RPA |   CHGO |   NF |   FUZZY |
|----------:|------:|------:|-------:|-----:|--------:|
|        50 |     4 |     5 |      3 |    2 |       1 |
|       100 |     4 |     5 |      3 |    2 |       1 |
|       150 |     4 |     5 |      3 |    2 |       1 |
|       200 |     3 |     5 |      4 |    2 |       1 |
|       250 |     3 |     5 |      4 |    2 |       1 |
|       300 |     3 |     5 |      4 |    2 |       1 |
|       350 |     3 |     5 |      4 |    2 |       1 |

## Sıralama — E2 tamamlama

|   mean_speed |   LPA |   RPA |   CHGO |   NF |   FUZZY |
|-------------:|------:|------:|-------:|-----:|--------:|
|           10 |     4 |     5 |      3 |    2 |       1 |
|           20 |     4 |     5 |      3 |    2 |       1 |
|           30 |     3 |     5 |      4 |    2 |       1 |
|           40 |     3 |     5 |      4 |    2 |       1 |
|           50 |     3 |     5 |      4 |    2 |       1 |

## 4. Sayısallaştırılmış şekiller

`data/paper_digitized/*.csv` boş olduğu için sayısal Spearman karşılaştırması yapılamadı. CSV'ler doldurulduğunda bu betik yeniden çalıştırılınca bölüm otomatik oluşur.
