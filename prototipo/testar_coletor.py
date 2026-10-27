"""Testes do coletor RSS usando XML local; não dependem da internet."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))

from coletar_fontes import collect, make_feed_url, parse_feed

SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>Teste</title>
<item>
<title>Exemplo de notícia de saúde no Distrito Federal</title>
<link>https://news.google.com/rss/articles/example123</link>
<pubDate>Tue, 27 Oct 2026 10:00:00 GMT</pubDate>
<description>Resumo para teste, não é uma notícia factual.</description>
<source url="https://example.org/noticia">Fonte de teste</source>
</item>
</channel></rss>"""


class CollectorTests(unittest.TestCase):
    def test_feed_url_uses_encoded_query(self):
        url = make_feed_url("saúde Brasília", "pt-BR", "BR", "BR:pt-419")
        self.assertIn("news.google.com/rss/search?", url)
        self.assertIn("q=sa%C3%BAde", url)

    def test_parse_rss_records_source_and_warning_status(self):
        items = parse_feed(SAMPLE_RSS, "saude", "https://example.org/rss", "2026-10-27T10:00:00+00:00")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["fonte_publicadora"], "Fonte de teste")
        self.assertEqual(items[0]["status_editorial"], "descoberta_pendente_verificacao")

    def test_collect_records_feed_failure_without_crashing(self):
        def broken_opener(url, timeout, max_bytes):
            raise OSError("falha simulada")

        report = collect({
            "provider": "teste",
            "language": "pt-BR",
            "region": "BR",
            "edition": "BR:pt-419",
            "queries": [{"pillar": "pet", "query": "animais"}]
        }, opener=broken_opener)
        self.assertEqual(report["total_items"], 0)
        self.assertEqual(report["feeds_com_sucesso"], 0)
        self.assertEqual(report["feeds"][0]["status"], "erro")


if __name__ == "__main__":
    unittest.main(verbosity=2)
