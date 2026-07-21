# Sipariş ve İş Takip Uygulaması

Bu proje, Excel üzerinden aktarılan haftalık iş yükünü `Y-STATK1` - `Y-STATK9` filtrelerine göre süzüp, mükerrer adımları ayıklayarak Firebase Firestore üzerinde takip etmeyi sağlar.

## Kurulum
1. `pip install flask openpyxl firebase-admin`
2. Firebase Console üzerinden `firebase_key.json` dosyasını indirip ana dizine koyun.
3. `python main.py` ile çalıştırın.