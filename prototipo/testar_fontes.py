import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))
from verificar_fontes import extract_html, select_candidates, validate_public_url


class SourceVerificationTests(unittest.TestCase):
    def test_extracts_title_description_and_paragraphs(self):
        html = """<!doctype html><html><head><title>Notícia teste</title>
        <meta name="description" content="Resumo de teste">
        <meta property="og:image" content="/img/noticia.jpg"></head><body>
        <nav>Menu ignorado</nav><p>Texto principal da matéria.</p>
        <script>código ignorado</script></body></html>"""
        result = extract_html(html, "https://example.org/noticia")
        self.assertEqual(result["titulo_pagina"], "Notícia teste")
        self.assertEqual(result["descricao_pagina"], "Resumo de teste")
        self.assertEqual(result["imagem_url"], "https://example.org/img/noticia.jpg")
        self.assertIn("Texto principal", result["texto_extraido"])
        self.assertNotIn("Menu ignorado", result["texto_extraido"])
        self.assertNotIn("código ignorado", result["texto_extraido"])

    def test_selects_up_to_three_sources_per_pillar_in_balanced_rounds(self):
        pillars = ("pet", "lazer", "esportes", "saude", "fitness")
        items = []
        for number in range(4):
            for pillar in pillars:
                items.append({
                    "pilar": pillar,
                    "titulo": f"{pillar}-{number}",
                    "url_agregador": f"https://news.google.com/rss/articles/{pillar}-{number}",
                })
        items.append({
            "pilar": "outro",
            "titulo": "Pauta fora dos pilares editoriais",
            "url_agregador": "https://news.google.com/rss/articles/outro-1",
        })
        selected = select_candidates({"itens": items}, None)
        counts = {}
        for item in selected:
            counts[item["pilar"]] = counts.get(item["pilar"], 0) + 1
        self.assertEqual(len(selected), 15)
        self.assertEqual(set(counts), set(pillars))
        self.assertTrue(all(count == 3 for count in counts.values()))
        self.assertEqual(
            [item["titulo"] for item in selected[:5]],
            [f"{pillar}-0" for pillar in pillars],
        )

    def test_triage_candidates_remain_authoritative_and_duplicates_are_removed(self):
        discovery_items = [
            {
                "pilar": "pet",
                "titulo": "Descoberta",
                "url_agregador": "https://news.google.com/rss/articles/discovery",
            }
        ]
        triage_items = [
            {
                "pilar": "pet",
                "titulo": "Triagem 1",
                "url_agregador": "https://news.google.com/rss/articles/one",
            },
            {
                "pilar": "pet",
                "titulo": "Duplicada",
                "url_agregador": "https://news.google.com/rss/articles/one/",
            },
            {
                "pilar": "pet",
                "titulo": "Triagem 2",
                "url_agregador": "https://news.google.com/rss/articles/two",
            },
        ]
        selected = select_candidates(
            {"itens": discovery_items},
            {"itens": triage_items},
        )
        self.assertEqual(
            [item["titulo"] for item in selected],
            ["Triagem 1", "Triagem 2"],
        )

    def test_rejects_non_https_and_local_hosts(self):
        for url in (
            "http://example.com",
            "https://localhost/article",
            "https://127.0.0.1/article",
            "https://user:pass@example.com",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_public_url(url)


if __name__ == "__main__":
    unittest.main(verbosity=2)
