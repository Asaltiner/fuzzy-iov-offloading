# Literatür Araştırması

Referans çalışmanın konusu ve yöntemiyle ilişkili güncel çalışmalar.

| # | Çalışma | Problem | Bulanık yöntem | Ortam / veri | Temel sonuç | Bizim çalışmayla ilişkisi |
|---|---|---|---|---|---|---|
| 1 | Trabelsi vd., 2024 (referans) | V2V görev aktarma, gecikmeye duyarlı uygulamalar | ANFIS ile üretilmiş kural tabanı, Low/Med/High terimleri | Veins+SUMO, 3×3 km | Gecikme ve PDR'de en iyi, tamamlama oranı en yüksek | Yeniden gerçekleştirilecek yöntem |
| 2 | Sonmez, Ozgovde, Ersoy, 2019 | Edge'de iş yükü yönetimi (görev nerede çalışsın?) | Mamdani bulanık orkestratör | EdgeCloudSim | Farklı servis sınıflarında rekabetçi performans | Edge'de bulanık mantıkla kararın klasik örneği; Mamdani tercihimizin dayanağı |
| 3 | Xu vd., 2022 (F-TORA) | IoV görev aktarma ve kaynak tahsisi | Takagi–Sugeno bulanık sinir ağı (trafik tahmini) + oyun teorisi + Q-learning | Simülasyon | Kısıtlı edge kaynağında gecikme azalıyor | Neuro-fuzzy (Sugeno) alternatifi; Mamdani–Sugeno tartışması için |
| 4 | Men vd., 2024 | V2X'te ikili aktarma için kaynak araç seçimi | Bulanık mantık (hesap gücü + hareketlilik + bağlantı kalitesi) | Xi'an gerçek trafik ağı | Görev tamamlama süresi %37,5 azalıyor | Edge seçimi girdileri bizim seçimimize çok benziyor; doğrudan karşılaştırılabilir |
| 5 | Ehtisham vd., 2024 | VANET'te fog katmanına görev zamanlama | Bulanık mantık (gecikme, deadline, CPU, bant genişliği) | 5000+ değerlik veri, simülasyon | Turnaround %9, makespan %15 daha iyi | Bulanık zamanlama; deadline'ı girdi olarak kullanması bizim ek fikrimiz için |
| 6 | Zhang vd., 2025 | Kavşaklarda VEC görev aktarma | Bulanık karar verme ile yardımcı araç seçimi + Stackelberg oyunu + GA | Gerçek veri | Yürütme süresi %9,73 ve enerji %13,78 daha az | Bulanık mantık ile GA'nın bir arada kullanımı |
| 7 | Behera vd., 2023 | Edge'de dağıtık görev aktarma | Bulanık optimal karar | Simülasyon | — | Referans makalenin de atıf yaptığı bulanık MEC çalışması |
| 8 | Ullah vd., 2016 | Bulut kaynak sağlama | GA ile üyelik fonksiyonu parametre optimizasyonu | Bulut esneklik çatısı | Elle tasarlanmış MF'ye göre daha iyi performans | **Özgün katkımızın (GA ile MF ayarı) yöntemsel dayanağı** |

**Teori kaynakları:**
- Zadeh, 1965 (bulanık kümeler)
- Mamdani & Assilian, 1975 (Mamdani denetleyici)
- Takagi & Sugeno, 1985
- Jang, 1993 (ANFIS)

## IEEE formatında kaynakça (taslak)
[1] Z. Trabelsi, M. Ali, and T. Qayyum, "Fuzzy-based task offloading in Internet of Vehicles (IoV) edge computing for latency-sensitive applications," *Internet of Things*, vol. 28, Art. no. 101392, Dec. 2024, doi: 10.1016/j.iot.2024.101392.

[2] C. Sonmez, A. Ozgovde, and C. Ersoy, "Fuzzy workload orchestration for edge computing," *IEEE Trans. Netw. Serv. Manag.*, vol. 16, no. 2, pp. 769–782, Jun. 2019, doi: 10.1109/TNSM.2019.2901346.

[3] X. Xu *et al.*, "Game theory for distributed IoV task offloading with fuzzy neural network in edge computing," *IEEE Trans. Fuzzy Syst.*, vol. 30, no. 11, pp. 4593–4604, Nov. 2022, doi: 10.1109/TFUZZ.2022.3158000.

[4] R. Men, X. Fan, A. Shan, and G. Yuan, "Fuzzy logic based binary computation offloading scheme in V2X communication networks," *IEEE Access*, vol. 12, pp. 45507–45518, 2024, doi: 10.1109/ACCESS.2024.3376607.

[5] M. Ehtisham *et al.*, "Internet of Vehicles (IoV)-based task scheduling approach using fuzzy logic technique in fog computing enables vehicular ad hoc network (VANET)," *Sensors*, vol. 24, no. 3, Art. no. 874, 2024, doi: 10.3390/s24030874.

[6] L. Zhang, M. Wang, L. Wang, Z. Chen, and H. Zhang, "Optimizing vehicle edge computing task offloading at intersections: a fuzzy decision-making approach," *J. Supercomput.*, vol. 81, no. 1, Art. no. 29, 2025, doi: 10.1007/s11227-024-06477-z.

[7] S. R. Behera *et al.*, "A distributed fuzzy optimal decision making strategy for task offloading in edge computing environment," *IEEE Access*, vol. 11, pp. 33189–33204, 2023.

[8] A. Ullah, J. Li, A. Hussain, and Y. Shen, "Genetic optimization of fuzzy membership functions for cloud resource provisioning," in *Proc. IEEE Symp. Ser. Comput. Intell. (SSCI)*, Athens, Greece, 2016.

[9] L. A. Zadeh, "Fuzzy sets," *Inf. Control*, vol. 8, no. 3, pp. 338–353, 1965.

[10] E. H. Mamdani and S. Assilian, "An experiment in linguistic synthesis with a fuzzy logic controller," *Int. J. Man-Mach. Stud.*, vol. 7, no. 1, pp. 1–13, 1975.

[11] J.-S. R. Jang, "ANFIS: adaptive-network-based fuzzy inference system," *IEEE Trans. Syst., Man, Cybern.*, vol. 23, no. 3, pp. 665–685, 1993.
