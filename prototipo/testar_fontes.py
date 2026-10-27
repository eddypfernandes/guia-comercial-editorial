import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))
from verificar_fontes import extract_html, select_candidates, validate_public_url


class SourceVerificationTests(unittest.TestCase):
    def test_extracts_title_description_and_paragraphs(self):
        html = """<!doctype html><html><head><title>Notícia teste</title>
        <meta name="description" content="Resumo de teste"></head><body>
        <nav>Menu ignorado</nav><p>Texto principal da matéria.</p>
        <script>código ignorado</script></body></html>"""
        result = extract_html(html)
        self.assertEqual(result["titulo_pagina"], "Notícia teste")
        self.assertEqual(result["descricao_pagina"], "Resumo de teste")
        self.assertIn("Texto principal", result["texto_extraido"])
        self.assertNotIn("Menu ignorado", result["texto_extraido"])
        self.assertNotIn("código ignorado", result["texto_extraido"])


    def test_candidate_sample_is_balanced_without_gemini(self):
        items = []
        for pillar in ("pet", "lazer", "esportes", "saude", "fitness"):
            for number in range(4):
                items.append({"pilar": pillar, "titulo": f"{pillar}-{number}"})
        selected = select_candidates({"itens": items}, None)
        counts = {}
        for item in selected:
            counts[item["pilar"]] = counts.get(item["pilar"], 0) + 1
        self.assertEqual(len(selected), 10)
        self.assertEqual(set(counts), {"pet", "lazer", "esportes", "saude", "fitness"})
        self.assertTrue(all(count == 2 for count in counts.values()))

    def test_rejects_non_https_and_local_hosts(self):
        for url in ("http://example.com", "https://localhost/article", "https://127.0.0.1/article", "https://user:pass@example.com"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_public_url(url)


if __name__ == "__main__":
    unittest.main(verbosity=2)
