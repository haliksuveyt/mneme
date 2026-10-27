# Devir paketi doğrulaması — 26 Ekim 2026

- Yeni `v3_handoff_test.py`: 13 test geçti. Temiz vault'a kurulum ve kurulu `mneme.py`
  üzerinden gerçek alt süreç çağrısı dahil.
  Fixture hash'inin Git CRLF/LF dönüşümünden etkilenmemesi de ayrı kontrol edilir.
- `evaluate_v3_handoff.py`: 60/60 sentetik kaynak-paketi senaryosu geçti. Ham kategori
  sonuçları: [JSON](handoff-source-contracts-2026-10-26.json). 0 model çağrısı, 0 canlı
  istemci oturumu; bu oran bir LLM cevap doğruluğu skoru değildir.
- `v3_stdlib_imports_test.py`: 4 test geçti. Yeni modül taşınabilir pakete giriyor;
  runtime üçüncü taraf bağımlılık eklemiyor.
- Mevcut `evaluate_v3.py`: 10 geliştirme + 6 holdout senaryosunun tüm kapıları geçti.
  Dondurulmuş mevcut fixture veya eşikleri değiştirilmedi.
- Geniş Windows V3 koşusu: 1020 test, 1 başarısızlık, 8 hata kaydı, 9 skip. Başarısız
  assertion, Git Bash'in PATH'te olmamasıydı. Diğer hata kayıtları geçici test dizinlerinin
  Windows'ta kopyalanması/temizlenmesi sırasında dosya kilidi/dizin varlığı hatalarıydı.
  Bu tam koşu yeşil diye raporlanmıyor.
- Hatalarla ilgili 6 hedefli kontrol değişiklik öncesi `2878dee` kaynakta Git Bash PATH'i
  düzeltilerek tekrar çalıştırıldı: 6/6 geçti. Dolayısıyla tüm geniş-koşu hataları için
  kalıcı bir baseline başarısızlığı iddia edilmiyor; Windows koşusundaki geçicilik ayrı tutuluyor.
- Aynı 6 kontrol geliştirme dalında tekrarlandığında yalnız OMP alias testinin geçici
  dizin temizliği kilitlendi. Testin `drive()` yardımcısı, `setUp` içinde istenen
  `MNEME_V3_NO_SPAWN=1` değerini `inherited_env()` ile düşürüyordu. Alt sürece bu değeri
  açıkça geçirerek yalnız test izolasyonu düzeltildi; üretim OMP davranışı değiştirilmedi.
  Düzeltme sonrası OMP modülündeki 9 testin tümü geçti.

Doğrulama kişisel vault'u güncellemedi ve model/API tüketimi başlatmadı. Kaynak geliştirme
sürümü için ölçümdür; release yayınlama ve gerçek istemci devam deneyi ayrı adımlardır.
