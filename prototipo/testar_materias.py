import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))
from gerar_materias import build_fallback_report, extract_json, validate_articles, merge_active_articles


class ArticleValidationTests(unittest.TestCase):
    def setUp(self):
        self.source = [{
            "pilar": "lazer",
            "fonte_publicadora": "Jornal Exemplo",
            "url_final": "https://example.org/noticia",
            "titulo_pagina": "Notícia original",
            "publicado_em_rss": "2026-10-27",
            "texto_extraido": "Texto da fonte " * 50,
            "imagem_url": "https://example.org/img/noticia.jpg",
            "status_verificacao": "pagina_original_extraida_revisao_factual_pendente",
        }]
        self.body = "Este é um texto editorial de teste, baseado no material fornecido pela fonte original. " * 5

    def test_fallback_creates_automatically_approved_preview_content_without_ai(self):
        result = build_fallback_report(self.source, "quota excedida")
        self.assertEqual(result["total_materias_validas"], 1)
        self.assertFalse(result["publicacao_oficial"])
        article = result["materias"][0]
        self.assertEqual(article["url_fonte"], "https://example.org/noticia")
        self.assertEqual(article["imagem_url"], "https://example.org/img/noticia.jpg")
        self.assertEqual(article["status_editorial"], "apto_para_publicacao")
        self.assertTrue(article["corpo"].startswith("Texto da fonte"))
        self.assertIn("prévia de testes", article["aviso_editorial"])
        self.assertIn("quota excedida", result["aviso"])
        self.assertIn("publicação simulada", result["aviso"])

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
            "titulo_carrossel": "Notícia útil para a comunidade",
            "linha_fina_carrossel": "Resumo conciso para a chamada da home.",
            "corpo": self.body,
            "url_fonte": "https://example.org/noticia",
            "imagem_url": "https://example.org/img/noticia.jpg",
        }]}
        result = validate_articles(data, self.source)
        self.assertEqual(result["total_materias_validas"], 1)
        self.assertEqual(result["materias"][0]["url_fonte"], "https://example.org/noticia")
        self.assertEqual(result["materias"][0]["imagem_url"], "https://example.org/img/noticia.jpg")
        self.assertEqual(result["materias"][0]["status_editorial"], "apto_para_publicacao")
        self.assertIn("não garante a veracidade independente", result["materias"][0]["aviso_editorial"])
        self.assertFalse(result["publicacao_oficial"])

    def test_rejects_unknown_source_wrong_pillar_and_short_text(self):
        data = {"materias": [
            {"pilar": "lazer", "titulo": "Uma notícia útil para a comunidade", "linha_fina": "Resumo claro com contexto para o leitor local.", "titulo_carrossel": "Notícia útil para a comunidade", "linha_fina_carrossel": "Resumo conciso para a chamada da home.", "corpo": self.body, "url_fonte": "https://invented.example/news"},
            {"pilar": "pet", "titulo": "Uma notícia útil para a comunidade", "linha_fina": "Resumo claro com contexto para o leitor local.", "titulo_carrossel": "Notícia útil para a comunidade", "linha_fina_carrossel": "Resumo conciso para a chamada da home.", "corpo": self.body, "url_fonte": "https://example.org/noticia"},
            {"pilar": "lazer", "titulo": "Uma notícia útil para a comunidade", "linha_fina": "Resumo claro com contexto para o leitor local.", "titulo_carrossel": "Notícia útil para a comunidade", "linha_fina_carrossel": "Resumo conciso para a chamada da home.", "corpo": "curto", "url_fonte": "https://example.org/noticia"},
        ]}
        result = validate_articles(data, self.source)
        self.assertEqual(result["total_materias_validas"], 0)
        self.assertEqual(result["respostas_rejeitadas"], 3)


    def test_merge_preserves_recent_approved_articles_and_removes_expired(self):
        now = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
        current = {
            "gerado_em": now.isoformat(),
            "total_materias_validas": 1,
            "materias": [{
                "id": "nova", "pilar": "lazer", "titulo": "Nova matéria válida",
                "url_fonte": "https://example.org/nova", "publicado_em_fonte": "Tue, 27 Oct 2026 12:00:00 GMT",
                "status_editorial": "apto_para_publicacao"
            }]
        }
        previous = {"materias": [
            {"id": "antiga-recente", "pilar": "pet", "titulo": "Matéria anterior ainda válida",
             "url_fonte": "https://example.org/pet/", "publicado_em_fonte": "Mon, 26 Oct 2026 12:00:00 GMT",
             "status_editorial": "apto_para_publicacao"},
            {"id": "vencida", "pilar": "saude", "titulo": "Matéria antiga vencida",
             "url_fonte": "https://example.org/antiga", "publicado_em_fonte": "Mon, 1 Sep 2026 12:00:00 GMT",
             "status_editorial": "apto_para_publicacao"},
            {"id": "rascunho", "pilar": "fitness", "titulo": "Rascunho não aprovado",
             "url_fonte": "https://example.org/rascunho", "publicado_em_fonte": "Tue, 27 Oct 2026 12:00:00 GMT",
             "status_editorial": "rascunho_automatico_sem_ia_revisao_obrigatoria"}
        ]}
        result = merge_active_articles(current, previous, now=now)
        urls = [item["url_fonte"] for item in result["materias"]]
        self.assertIn("https://example.org/nova", urls)
        self.assertIn("https://example.org/pet/", urls)
        self.assertNotIn("https://example.org/antiga", urls)
        self.assertNotIn("https://example.org/rascunho", urls)
        self.assertEqual(result["total_materias_validas"], 2)
        self.assertTrue(all(item.get("validade_ate") for item in result["materias"]))

    def test_merge_deduplicates_same_source_and_requires_publication_date(self):
        now = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)
        new_article = {
            "id": "nova", "pilar": "lazer", "titulo": "Versão nova da matéria",
            "url_fonte": "https://example.org/noticia?utm_source=rss",
            "publicado_em_fonte": "Tue, 27 Oct 2026 12:00:00 GMT",
            "status_editorial": "apto_para_publicacao"
        }
        old_article = {
            "id": "antiga", "pilar": "lazer", "titulo": "Versão anterior da matéria",
            "url_fonte": "https://example.org/noticia/",
            "publicado_em_fonte": "Tue, 27 Oct 2026 12:00:00 GMT",
            "status_editorial": "apto_para_publicacao"
        }
        undated = {
            "id": "sem-data", "pilar": "pet", "titulo": "Matéria sem data confiável",
            "url_fonte": "https://example.org/sem-data",
            "status_editorial": "apto_para_publicacao"
        }
        result = merge_active_articles({"materias": [new_article]}, {"materias": [old_article, undated]}, now=now)
        self.assertEqual(len(result["materias"]), 1)
        self.assertEqual(result["materias"][0]["id"], "nova")


if __name__ == "__main__":
    unittest.main(verbosity=2)
