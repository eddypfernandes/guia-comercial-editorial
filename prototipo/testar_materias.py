import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))
from gerar_materias import extract_json, validate_articles


class ArticleValidationTests(unittest.TestCase):
    def setUp(self):
        self.source = [{
            "pilar": "lazer",
            "fonte_publicadora": "Jornal Exemplo",
            "url_final": "https://example.org/noticia",
            "titulo_pagina": "Notícia original",
            "publicado_em_rss": "2026-10-27",
            "texto_extraido": "Texto da fonte " * 50,
            "status_verificacao": "pagina_original_extraida_revisao_factual_pendente",
        }]
        self.body = "Este é um texto editorial de teste, baseado no material fornecido pela fonte original. " * 5

    def test_extract_json(self):
        self.assertEqual(
            extract_json({"candidates": [{"content": {"parts": [{"text": '{"materias": []}'}]}}]}),
            {"materias": []},
        )

    def test_accepts_article_with_exact_source_url(self):
        data = {"materias": [{
            "pilar": "lazer",
            "titulo": "Uma notícia útil para a comunidade",
            "linha_fina": "Resumo claro com contexto para o leitor local.",
            "corpo": self.body,
            "url_fonte": "https://example.org/noticia",
        }]}
        result = validate_articles(data, self.source)
        self.assertEqual(result["total_materias_validas"], 1)
        self.assertEqual(result["materias"][0]["url_fonte"], "https://example.org/noticia")
        self.assertFalse(result["publicacao_oficial"])

    def test_rejects_unknown_source_wrong_pillar_and_short_text(self):
        data = {"materias": [
            {"pilar": "lazer", "titulo": "Uma notícia útil para a comunidade", "linha_fina": "Resumo claro com contexto para o leitor local.", "corpo": self.body, "url_fonte": "https://invented.example/news"},
            {"pilar": "pet", "titulo": "Uma notícia útil para a comunidade", "linha_fina": "Resumo claro com contexto para o leitor local.", "corpo": self.body, "url_fonte": "https://example.org/noticia"},
            {"pilar": "lazer", "titulo": "Uma notícia útil para a comunidade", "linha_fina": "Resumo claro com contexto para o leitor local.", "corpo": "curto", "url_fonte": "https://example.org/noticia"},
        ]}
        result = validate_articles(data, self.source)
        self.assertEqual(result["total_materias_validas"], 0)
        self.assertEqual(result["respostas_rejeitadas"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
