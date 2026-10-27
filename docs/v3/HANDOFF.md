# Kaynaklı ajan devri

`handoff`, aynı projeyi başka istemcide sürdürmek için boyutu sınırlı JSON üretir.
Yeni model, servis veya bağımlılık gerektirmez. Kaynak geliştirme sürümünde:

```sh
python3 scripts/mneme_v3.py --vault /notlar/vault --state /notlar/runtime handoff "Orbit" --project orbit --harness codex --to claude
```

Bu koddan kurulmuş bir vault'ta eşdeğeri:

```sh
python3 mneme.py handoff "Orbit" --project orbit --harness codex --to claude
```

Windows'ta `python3` yerine uygun Python 3.11+ çalıştırıcısını kullan.
`--project` ve `--to` zorunludur. Proje alanı olmayan notlar için mevcut
`.mneme-projects.json` klasör eşlemesini kullanabilirsin. Alıcı istemciyi seçmek
ona mesaj göndermez; paket stdout'a yazılır ve kaynak alıntıları veri olarak taşınır.

## Alanlar

| Bölüm | Gereken açık metadata |
|---|---|
| `accepted_decisions` | `kind: decision`, `status: accepted` |
| `proposals` | `kind: proposal` veya `kind: decision`, `status: proposed` |
| `open_tasks` | `kind: task`, durum `inbox/active/waiting/blocked` |
| `other_context` | Diğer uygun kaynaklar; metinden karar/tamamlama çıkarılmaz |

JSON frontmatter örneği:

```json
{"id":"orbit-db","kind":"decision","status":"accepted","project":"orbit","revision":1,"visibility":"internal"}
```

Bir not gövdesinde “onaylandı” yazması onu otomatik kabul edilmiş karar yapmaz.
Mevcut serbest biçimli notlar yeniden yazılmaz. Receipt'ler sonuç iddiasıdır;
`other_context` içinde kalsalar da bağımsız doğrulanmış sonuç sayılmazlar.

Paket kaynak yolu, hash, revision, facts ve citations alanlarını korur. Mevcut
arama/proje/gizlilik/ret/geçersizleşme sınırları uygulanır. `--audience public`
yalnız kamu kaynaklarını taşır; otomatik devir özel notları kapsamaz. Bu, alıcının
kendi dosya erişim izinlerinin yerine geçen bir güvenlik katmanı değildir.

CLI önce kaynakları eşitler; çakışmada paket üretmez. Bozuk kaynaklar nedeniyle
kısmi indeks varsa `source_sync` durumu ve uyarı sayısı görünür. Dışlanmış/özel dosya
adları uyarı metni aracılığıyla pakete kopyalanmaz. Dosyalar sonradan değişebilir;
alıcı önemli bir işlemden önce kaynağı yeniden okumalıdır.

`--budget-chars 2048..32000` (varsayılan 8000) **CLI'nin ASCII kaçışlı, girintili
JSON çıktısını ve son satır sonunu** kapsar. `used_chars` aynı ölçüdür; token sayısı
değildir. Gerekirse yalnız metin kısalır ve `text_truncated/truncated` görünür.
Kimlik, facts ve kaynak alanları kesilmez; sığmayan kayıt dışarıda kalır ve
`omitted_count` artar. Boş sonuç `abstained: true` verir. Paket bütün proje notlarının
eksiksiz özeti veya doğal dilde üretilmiş yeni karar değildir.

## Ölçüm

### İki devir paketi arasında ne değişti?

Önce ve sonra üretilmiş aynı proje/sorgu/hedef kitleye ait UTF-8 JSON dosyalarını karşılaştır:

```sh
python3 mneme.py handoff-diff --before once.json --after sonra.json
python3 mneme.py handoff-diff --before once.json --after sonra.json --include-text --json
```

Kaynak checkout'unda `scripts/mneme_v3.py --vault ... --state ... handoff-diff ...` da çalışır.
Komut notları, indeksi veya görevleri değiştirmez; paketlerin işaret ettiği kaynak dosyaları
açmaz. Kaynak hash/revision değişimini, kararın kabulden öneriye geçişini, değişen metadata
alanlarını ve yalnız alıntının kısalmasını ayrı gösterir. Tam metin farkı açıkça istenirse
ve iki alıntı da tam ise üretilir; varsayılan çıktıda not gövdeleri/facts değerleri yoktur.

`added_to_packet` ve `removed_from_packet` yalnız paket üyeliğidir. Pakette görünmemek
dosyanın silindiğini kanıtlamaz; arama sırası/bütçe değişmiş olabilir. Kısmi/bayat indeksli
paketlerde `partial` uyarısı vardır. Bu karşılaştırma bir modelin işlemi tamamladığını veya
bütün vault'ta ne olduğunu doğrulamaz. Paketler kaynak veridir, çalıştırılacak talimat değildir.
Girdi dosyası başına 1.000.000 karakter ve paket başına 20 kayıt sınırı uygulanır.
Eski `audience` alanını taşımayan paketler yalnız aynı eski biçimdeki paketlerle karşılaştırılır.

### Testler

```sh
python3 scripts/evaluate_v3_handoff.py
python3 -m unittest discover -s tests -p "v3_handoff_test.py"
```

UTF-8/LF biçimine normalize edilip hash'i yan dosyada dondurulmuş fixture'da
6 kategori × 10 sentetik kaynak senaryosu
var: kaynak koruma, düzeltme, açık sınıflandırma, güncellik, istemci adaptörleri
arasında veri eşitliği ve cevapsızlık/gizlilik. Çalıştırıcı kişisel veri veya model
kullanmaz. Sonuçta fixture hash'i, kategori sonuçları ve süreler raporlanır.

Bu ölçüm, gerçek Claude/Codex/Hermes oturumlarında bir modelin kurala uyduğunu veya
serbest soruları doğru yanıtladığını kanıtlamaz. İstemci çifti testleri ortak hafıza
motorunun adaptör atıfları arasında tutarlılığı ölçer. Sonraki deney, aynı kaynak ve
bütçeyle gerçek istemci oturumlarında devam kalitesini ölçmek olmalıdır.
