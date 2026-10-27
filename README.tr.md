<p align="center"><img src="docs/img/hero.svg" alt="mneme — Ajanların değişir. Bilgin kalır." width="100%"></p>

<p align="center"><a href="README.md">English</a> · <strong>Türkçe</strong></p>

<p align="center"><a href="https://github.com/haliksuveyt/mneme/actions/workflows/v3.yml"><img src="https://github.com/haliksuveyt/mneme/actions/workflows/v3.yml/badge.svg" alt="CI"></a> <a href="https://github.com/haliksuveyt/mneme/releases/latest"><img src="https://img.shields.io/github/v/release/haliksuveyt/mneme?color=8172c2" alt="Release"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-64748b" alt="MIT license"></a></p>


# Ajanlarının ortak ikinci beyni

Proje kararlarını, kişisel bağlamını ve öğrendiklerini kendi klasöründe tut. Mneme, kaynaklı bilgiyi bir sonraki yapay zekâ oturumuna taşır; neyin değiştiğini ve hangi işin açık kaldığını görünür kılar.

**Claude Code · Codex · Antigravity · Hermes · OpenCode · OMP**

| Bilgin | Çalışma biçimin | Sonraki oturumun |
|---|---|---|
| Her yerde açabileceğin **düz Markdown** | Ortak not ve kurallardan **otomatik bağlam** | Karar ve açık işleri koruyan **kaynaklı devir** |

## Bir klasör. Bir mesaj.

Python **3.11+**. Not klasörünü kullandığın yapay zekâ istemcisinde aç ve gönder:

> https://raw.githubusercontent.com/haliksuveyt/mneme/main/mneme.md adresini oku. Bu klasöre ikinci beynimi kur. Mevcut notlarımı koru, resmî sürümün checksum değerini doğrula, kurulumu ve sağlık kontrolünü tamamla. Sonunda örnek bir bilgiyi kaydedip yeni oturumda geri okuyarak doğrulayalım.

Ajanın taşınabilir resmî paketi kurar ve istemciyi ortak hafızaya bağlar. İstemcinin workspace/hook güven incelemesini tamamla, ardından yeni oturum aç.

### Elle kurulum

[Son sürümden](https://github.com/haliksuveyt/mneme/releases/latest) `mneme-v3-3.12.0.zip` ve `.sha256` dosyasını indir, checksum'u doğrula ve ZIP'i aç. Paket klasöründe:

```bash
# Windows
py -3 scripts/install_v3.py --vault "C:\Notlar\Beynim"
# macOS / Linux
python3 scripts/install_v3.py --vault "/tam/yol/Notlarım"
```

Mevcut kullanıcılar vault klasöründe `py -3 mneme.py update` çalıştırabilir; macOS/Linux'ta `python3 mneme.py update` kullanılır. [Adım adım kurulum →](KURULUM.md)

## İşin hafızası seninle gelsin

<img src="docs/img/workflow.svg" alt="Markdown notlardan kaynaklı bağlama, devir paketine ve sonuç kayıtlarına" width="100%">

- **İşe uygun bağlam.** İlgili metin, kaynak yolu ve revizyonla, ayarlanabilir bütçe içinde gelir.
- **Karar ile öneri ayrı.** Devir paketi kabul edilmiş kararları, önerileri ve açık görevleri metadata üzerinden ayırır.
- **Değişiklik görünür.** İki paket arasında kaynak, metadata ve metin farkını incele.
- **İşin izi kalır.** Kaynak bağlantılı receipt, revizyon kontrollü görev güncellemesi ve oturum kartı birlikte çalışır.
- **Klasör senin.** Yerel hafıza motoru Python standart kütüphanesini kullanır. Yapay zekâ erişimi seçtiğin istemcide kalır.

```bash
py -3 mneme.py context "proje kararları"
py -3 mneme.py handoff "Orbit" --project orbit --to codex
py -3 mneme.py handoff-diff --before once.json --after sonra.json
```

## Kaynak merkezli çalışma

Gerçek kaynak Markdown dosyalarıdır. Sync yerel indeksi günceller; arama güncellik, görünürlük ve geçerlilik alanlarını dikkate alır. Kabul edilmiş kararlar açık metadata'dan gelir. Receipt, iş sonucunu dayanaklarıyla kaydeder.

[Devir rehberi](docs/v3/HANDOFF.md) · [Kaynak formatı](docs/v3/MARKDOWN.md) · [Tercihler](docs/v3/PREFERENCES.md) · [Güncelleme ve geri alma](docs/v3/UPDATE.md)

## Çalışırken gör

[Tanıtım videosu](https://youtu.be/weSUupkkIJ8) · [Mühendislik vaka incelemesi](docs/v3/CASE-STUDY.md) · [3.12.0 sürüm notları](docs/v3/releases/3.12.0.md)

Devir katmanı **60 kaynak sözleşmesi senaryosu**, paket farkı testleri ve gerçek Sol oturumlarıyla incelendi. CI; Linux, macOS ve Windows'ta Python 3.11/3.13 matrisini çalıştırır. Deneyin yöntemi ve tasarım kararları [vaka incelemesinde](docs/v3/CASE-STUDY.md).

## İstemcini seç

[MCP](docs/v3/MCP.md) · [Hermes](docs/v3/HERMES.md) · [OpenCode](docs/v3/OPENCODE.md) · [OMP](docs/v3/OMP.md) · [Birden çok makine](docs/v3/MULTI-MACHINE.md)

[Halik Suveyt](https://github.com/haliksuveyt) tarafından geliştirildi. [MIT lisansı](LICENSE) · [Sorun bildir](https://github.com/haliksuveyt/mneme/issues)
