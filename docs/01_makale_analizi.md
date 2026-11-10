# Checkpoint 1 — Referans Makale Analizi

**Makale:** Z. Trabelsi, M. Ali, T. Qayyum, "Fuzzy-based task offloading in Internet of Vehicles (IoV) edge computing for latency-sensitive applications," *Internet of Things*, vol. 28, Art. no. 101392, Dec. 2024. doi: 10.1016/j.iot.2024.101392 (açık erişim)

## 1. Problem ve motivasyon
- Araç içi uygulamalar (çarpışma uyarısı, sürüş asistanı, görüntü işleme vb.) giderek daha fazla hesaplama gücü istiyor. Tek bir aracın işlemcisi bu talebi karşılamaya yetmiyor.
- Bu yüzden çözüm, görevleri komşu araçlara (V2V) **aktarmak (offloading)**. Görevi alan komşu araç *edge node (EN)*, görevi gönderen araç *user node (UN)* olarak adlandırılıyor.
- IoV'deki zorluklar: yüksek hareketlilik, sürekli değişen topoloji, değişken araç yoğunluğu ve görevlerin aciliyetlerinin birbirinden farklı olması.
- Klasik yöntemler (rastgele seçim, en hızlı düğüme açgözlü atama, FIFO kuyruk) bağlantı süresini ve görev aciliyetini birlikte dikkate almıyor.
- **Neden bulanık mantık?** "Yakın", "hızlı", "acil" gibi kavramların keskin eşikleri yok. Sensör ve konum verisi gürültülü. Uzman bilgisi IF-THEN kurallarıyla doğrudan modellenebiliyor ve karar hesabı hafif kalıyor.

## 2. Önerilen yöntem
### 2.1 Sistem modeli
- **Kanal:** Nakagami-m sönümleme modeli. Bağlantının başarılı olma olasılığı (Denk. 1):
  `P = e^(−λ r_T/Φ) · Σ_{k=0}^{λ−1} (λ r_T/Φ)^k / k!`
  Burada r_T alınan sinyal eşiği, Φ ortalama alınan güç, λ sönümleme parametresidir.
- **Sönümleme parametresi (Denk. 2):** d < 50 m için λ = 3; 50 ≤ d < 150 m için λ = 1,5; d ≥ 150 m için λ = 1.
- **Bağıl mesafe (Denk. 3):** β_i = Σ_j √((X_j−X_i)² + (Y_j−Y_i)²)
- **Ortalama hız farkı (Denk. 4):** v_i^avg = (1/N) Σ_j |v_i − v_j|

### 2.2 Edge seçimi (UN tarafı)
1. UN, komşu araçların periyodik beacon duyurularını dinler. Duyuruda konum, hız ve kaynak bilgisi bulunur.
2. Bağlantı süresinin uzun olacağı adayları tercih eder: yakın olan ve aynı yönde benzer hızla giden araçlar.
3. Hesaplama kaynağı yeterli olan EN'yi seçer, görevi gönderir ve görevi "pending" olarak işaretler.

### 2.3 Görev önceliklendirme (EN tarafı) — bulanık kısım
- **Girdiler:** mesafe, hız, görev boyutu, görev önceliği. Şekil 4'te düğüm kapasitesi olarak MIPS de geçiyor.
- **Dilsel terimler:** Low / Medium / High. MIPS için poor / average / good.
- **Örnek kural:** IF speed is Low AND distance is Medium THEN priority is High.
- **İşleyiş:** bulanıklaştırma → kural değerlendirme → birleştirme → durulaştırma → skor. EN kuyruğu bu skora göre sıralanır.
- **Toplam skor (Denk. 5–9):** `com_score = w_d·MF_dist + w_v·MF_speed + w_s·MF_size + w_p·MF_prio`. Ağırlıklar şöyle hesaplanır: w_x = I_x / ΣI (önem skorlarının normalize edilmiş hali).
- **Kural tabanının üretimi:** Kurallar MATLAB Fuzzy Logic Designer'da ANFIS ile, yaklaşık 500 düğümlük bir veriden üretilmiş: 600 epoch, 70/30 eğitim/test ayrımı, eğitim hatası 0,004, test hatası 0,005. Sonra VEINS/SUMO'ya entegre edilmiş.

## 3. Deney düzeneği (Tablo 3)
| Parametre | Değer |
|---|---|
| Simülatör | Veins + SUMO (+OMNeT++), OSM kent haritası |
| Alan | 3 km × 3 km, çift yönlü yollar |
| İletim menzili | 250 m |
| MAC / hız | IEEE 802.11p WAVE / 6 Mbps |
| Araç yoğunluğu | 50–350 araç/km |
| Araç hızı | 10–50 m/s |
| Simülasyon süresi / tekrar | 500 s / 50 |
| Beacon / acil mesaj boyutu | 194 B / 170 B |
| Araç uzunluğu / min. aralık | 2,5 m / 2,5 m |

**Karşılaştırılan yöntemler:**
- **LPA/APA:** görev yerelde işlenir.
- **RPA:** görev rastgele bir araca gönderilir.
- **CHGO:** merkezi açgözlü yöntem; işlem gecikmesi en düşük düğüm seçilir.
- **NF (Next Fit):** düğümler işlem gücüne göre sıralanır ve sırayla denenir.

**Metrikler:**
- sistem gecikmesi
- kuyruk gecikmesi
- kuyruk boyu
- ortalama gecikme (Şek. 9)
- PDR (Şek. 10)
- görev tamamlama oranı – yoğunluğa göre (Şek. 11)
- görev tamamlama oranı – hıza göre (Şek. 12)
- araç başına beacon sayısı

## 4. Sonuçlar (yazarların raporladığı)
- Önerilen yöntem tüm yoğunluklarda en düşük gecikmeyi ve en yüksek PDR'yi veriyor. Tüm hızlarda en yüksek görev tamamlama oranı da onda.
- Yoğunluk arttıkça gecikme ve kuyruk boyu artıyor. LPA en kötü sonucu veriyor. Yüksek yoğunlukta RPA, LPA'dan iyi. CHGO hızlara karşı tutarlı ama yoğun ağda merkezi kararları yüzünden zayıflıyor. NF yoğun bölgelerde güçlü.
- **Sonuçlar metinde sayısal olarak verilmemiş, yalnızca grafiklerde var.** Sayısal karşılaştırma için Şek. 9–12'den WebPlotDigitizer ile değer okunacak (`data/paper_digitized/`).

## 5. Eleştirel değerlendirme (rapor ve sunum için)
**Güçlü yönler**
- Hareketlilik (hız, mesafe) ile görev aciliyetini aynı karar mekanizmasında birleştiriyor.
- Yorumlanabilir bir kural tabanı var.
- Gerçekçi bir trafik simülatörü (SUMO) kullanılmış.

**Eksik ve tutarsızlıklar (yeniden üretimi zorlaştıranlar)**
1. Üyelik fonksiyonlarının tipi ve parametreleri metinde yok, sadece şekillerde gösteriliyor.
2. Kural sayısı ve kuralların tam listesi verilmemiş.
3. Mamdani mi Sugeno mu kullanıldığı ve durulaştırma yöntemi belirtilmemiş. ANFIS kullanıldığı söylendiği için muhtemelen Sugeno, ama bu kesin değil.
4. ANFIS'in eğitildiği "500 düğümlük veri" paylaşılmamış.
5. Ağırlıkların önem skorları (I_x) verilmemiş.
6. Görev boyutu, CPU/MIPS değerleri ve görevlerin teslim süreleri (deadline) belirtilmemiş.
7. Notasyon tutarsız: w_s/w_si ve LPA/APA iki farklı şekilde yazılıyor. Tabloda "Packet interval" satırının birimi m/s olarak verilmiş.
8. Sonuçlar sayısal değil ve istatistiksel bir anlamlılık analizi yok (50 tekrarın varyansı raporlanmamış).

**Yazarların kendi belirttiği sınırlılıklar**
- Bulanık çıkarımın getirdiği hesaplama yükü.
- Kural tabanının ölçeklenebilirliği.
- Ani topoloji değişimlerine tepki.
- Güvenlik ve gizlilik.
- Düğümleri katılıma teşvik edecek bir mekanizma eksikliği.

**Yazarların önerdiği gelecek çalışma**
- Üyelik fonksiyonlarını ve kural setlerini GA veya DRL ile otomatik ayarlamak. **Bizim özgün katkımızın gerekçesi bu öneri.**

## 6. Projedeki kapsam (MRR)
Veins/OMNeT++ ortamının kurulumu ve kalibrasyonu proje kapsamını aşıyor. Bu yüzden şunu yapacağız:
- Python'da tohum kontrollü, sadeleştirilmiş bir ayrık zamanlı simülatör yazacağız. İçinde araç hareketi, 250 m V2V menzili, Nakagami-m bağlantı başarısı, beacon tabanlı edge seçimi ve EN kuyruğunda bulanık önceliklendirme olacak.
- Dört baseline uygulanacak: LPA, RPA, CHGO, NF.
- Yeniden üretilecek deneyler: Şek. 9 (gecikme – yoğunluk), Şek. 11 (tamamlama oranı – yoğunluk), Şek. 12 (tamamlama oranı – hız).
- Karşılaştırma, eğilim ve yöntem sıralaması düzeyinde yapılacak. Mutlak değerler simülatör farkı nedeniyle birebir beklenmiyor; bu durum raporda tartışılacak.
