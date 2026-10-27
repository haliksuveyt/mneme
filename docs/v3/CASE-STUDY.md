# Source-linked continuity between agent sessions

[English](#the-problem) · [Türkçe](#türkçe)

## The problem

A new agent session needs the current decisions, open tasks and supporting sources. A useful handoff preserves those distinctions and gives the next agent an inspectable record.

## The contribution

The handoff layer builds bounded packets from Mneme's local Markdown memory. Accepted decisions, proposals and open tasks are classified using explicit metadata. Records retain source paths, SHA-256 hashes and revisions. `handoff-diff` reports source, metadata and excerpt changes between matching packet scopes.

Context budgeting clips excerpts while preserving source identity. Freshness, visibility and validity checks apply to the selected records. Packet membership and source lifecycle are tracked as distinct concepts.

## Run the demo

Python 3.11+ in the repository:

```bash
python scripts/evaluate_v3_handoff.py
python -m unittest discover -s tests -p "v3_handoff_diff_test.py"
```

The first command runs 60 deterministic source-contract scenarios. The second verifies packet-diff behavior. To create a packet from your own example notes, follow [HANDOFF.md](HANDOFF.md).

## Real Sol continuation evidence

Two isolated Codex CLI sessions requested `gpt-6.1-sol`. One received a handoff packet; the other received the same six source records as a flat list. Seven answer targets were frozen before the runs; source citations, quoted-instruction handling and tool-free execution were also evaluated.

| Input | Accepted checks |
|---|---:|
| Source-linked packet | 10/10 |
| Flat source records | 10/10 |

Both sessions preserved the current database decision, proposal/task distinctions and delivery evidence. The [full experiment record](../../reports/live-handoff-2026-10-27.json) includes prompts, answer targets, responses, usage and transport verification. The fixture covers one synthetic scenario per condition. LF-normalized preparation texts were 4,351 characters; Windows CRLF files were 4,484 and 5,828 bytes. These are continuation observations, with method details retained alongside the results.

[Source-contract results](../../reports/handoff-source-contracts-2026-10-26.json) · [Source format](MARKDOWN.md)

## Türkçe

Mneme'nin Markdown hafızası üzerinde kaynaklı devir ve paket farkı katmanı geliştirildi. Karar, öneri ve açık görev metadata ile ayrılır; kaynak yolu, hash ve revizyon korunur. Bütçeli paket, bir sonraki ajana işin izini taşır.

60 kaynak sözleşmesi senaryosu ve paket farkı testleri yerel olarak çalışır. Aynı altı yapay kaynakla iki gerçek Sol oturumunda paket ve düz kayıt koşulları 10'ar kabul kontrolünü geçti. Yöntem, girdi, yanıt ve Windows satır sonu ayrıntıları deney kaydında birlikte sunulur.
