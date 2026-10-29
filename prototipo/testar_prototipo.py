"""Testes básicos do protótipo editorial, sem dependências externas."""
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))

from validar_config import validate_config
from ciclo_editorial import select_cycle, validate_candidate
from gerar_materias import merge_active_articles, compactar_titulo, compactar_texto


class ConfigTests(unittest.TestCase):
    def test_configuracao_segura_e_valida(self):
        config = {
            "mode": "prototype",
            "official_publication_enabled": False,
            "pillars": ["pet", "lazer", "esportes", "saude", "fitness"],
            "target_active_contents_per_pillar": {"minimum": 1, "maximum": 2},
            "local_focus": ["Núcleo Bandeirante"],
            "image_ai_disclosure": "Imagem criada por IA"
        }
        self.assertEqual(validate_config(config), [])

    def test_publicacao_ativa_e_rejeitada(self):
        config = {
            "mode": "prototype",
            "official_publication_enabled": True,
            "pillars": ["pet", "lazer", "esportes", "saude", "fitness"],
            "target_active_contents_per_pillar": {"minimum": 1, "maximum": 2},
            "local_focus": ["Núcleo Bandeirante"],
            "image_ai_disclosure": "Imagem criada por IA"
        }
        self.assertTrue(validate_config(config))


class CycleTests(unittest.TestCase):
    def candidate(self, id, title, score, pillar="pet", url=None, expiry="2026-12-01"):
        return {
            "id": id, "titulo": title, "pilar": pillar,
            "url_fonte": url or f"https://example.org/{id}",
            "consultado_em": "2026-10-27", "validade_ate": expiry,
            "status": "em_analise", "pontuacao": score
        }

    def test_selects_no_more_than_two_per_pillar(self):
        items = [
            self.candidate("a", "Pauta de cuidados com animais número um", 90),
            self.candidate("b", "Pauta de cuidados com animais número dois", 80),
            self.candidate("c", "Pauta de cuidados com animais número três", 70)
        ]
        report = select_cycle(items, ["pet", "lazer", "esportes", "saude", "fitness"], date(2026, 10, 27))
        self.assertEqual(len(report["selecionadas"]), 2)
        self.assertEqual(len(report["nao_selecionadas"]), 1)

    def test_expired_item_is_not_selected(self):
        item = self.candidate("old", "Pauta antiga sobre cuidados com animais", 99, expiry="2026-10-26")
        report = select_cycle([item], ["pet", "lazer", "esportes", "saude", "fitness"], date(2026, 10, 27))
        self.assertEqual(report["selecionadas"], [])
        self.assertIn("pauta expirada", report["nao_selecionadas"][0]["motivos"])

    def test_duplicate_source_url_is_flagged(self):
        items = [
            self.candidate("a", "Primeira pauta de cuidados com animais", 90, url="https://example.org/fonte"),
            self.candidate("b", "Segunda pauta de cuidados com animais", 80, url="https://example.org/fonte/")
        ]
        report = select_cycle(items, ["pet", "lazer", "esportes", "saude", "fitness"], date(2026, 10, 27))
        self.assertEqual(len(report["selecionadas"]), 1)
        self.assertIn("URL de fonte duplicada", report["nao_selecionadas"][0]["motivos"])

    def test_invalid_candidate_is_rejected(self):
        errors, item = validate_candidate({"id": "x"}, {"pet"})
        self.assertIsNone(item)
        self.assertTrue(errors)


class FeedMergeTests(unittest.TestCase):
    def article(self, identifier, pillar, url, published):
        return {
            "id": identifier,
            "pilar": pillar,
            "titulo": "Título editorial suficientemente claro",
            "linha_fina": "Resumo editorial usado para validar o feed.",
            "titulo_carrossel": "Chamada editorial",
            "linha_fina_carrossel": "Resumo curto da chamada editorial.",
            "corpo": "Conteúdo de teste.",
            "url_fonte": url,
            "publicado_em_fonte": published,
            "status_editorial": "apto_para_publicacao",
            "validade_ate": "2026-11-05",
        }

    def test_articles_expire_after_72_hours_even_if_explicit_expiry_is_later(self):
        now = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
        article = self.article(
            "old", "pet", "https://example.org/old",
            "Sun, 25 Oct 2026 11:59:00 GMT"
        )
        article["validade_ate"] = "2026-11-05"
        result = merge_active_articles(
            {"materias": []}, previous_feed={"materias": [article]}, now=now
        )
        self.assertEqual(result["materias"], [])

    def test_retains_up_to_four_per_pillar_and_twenty_total(self):
        now = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
        pillars = ["pet", "lazer", "esportes", "saude", "fitness"]
        articles = []
        for pillar in pillars:
            for index in range(6):
                articles.append(self.article(
                    f"{pillar}-{index}", pillar,
                    f"https://example.org/{pillar}/{index}",
                    f"Wed, 28 Oct 2026 {11-index:02d}:00:00 GMT"
                ))
        result = merge_active_articles(
            {"materias": []}, previous_feed={"materias": articles}, now=now
        )
        self.assertEqual(len(result["materias"]), 20)
        counts = {}
        for article in result["materias"]:
            counts[article["pilar"]] = counts.get(article["pilar"], 0) + 1
        self.assertTrue(all(count <= 4 for count in counts.values()))

    def test_merge_sorts_newest_first_and_assigns_unique_stable_ids(self):
        now = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
        older = self.article("rascunho-01", "pet", "https://example.org/pet", "Tue, 27 Oct 2026 10:00:00 GMT")
        newer = self.article("rascunho-01", "lazer", "https://example.org/lazer", "Wed, 28 Oct 2026 11:00:00 GMT")
        same_source_duplicate = self.article("rascunho-01", "pet", "https://EXAMPLE.org/pet/", "Tue, 27 Oct 2026 10:00:00 GMT")

        result = merge_active_articles(
            {"materias": [older, newer, same_source_duplicate]},
            previous_feed={},
            now=now,
        )

        self.assertEqual([item["url_fonte"] for item in result["materias"]],
                         ["https://example.org/lazer", "https://example.org/pet"])
        ids = [item["id"] for item in result["materias"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(item_id.startswith("materia-") for item_id in ids))
        self.assertFalse(result["publicacao_oficial"])

        repeated = merge_active_articles(
            {"materias": [older, newer]},
            previous_feed={},
            now=now,
        )
        self.assertEqual(
            {item["url_fonte"]: item["id"] for item in result["materias"]},
            {item["url_fonte"]: item["id"] for item in repeated["materias"]},
        )


class CarouselTextTests(unittest.TestCase):
    def test_long_title_prefers_a_complete_lead_sentence(self):
        title = "Quem é Renato Cariani? Conheça o influenciador fitness que pode pegar até 51 anos de prisão - Na Hora da Notícia"
        result = compactar_titulo(title)
        self.assertEqual(result, "Quem é Renato Cariani?")
        self.assertLessEqual(len(result), 65)

    def test_colon_title_keeps_subject_and_avoids_cutting_a_connector(self):
        title = "Santos x Palmeiras: veja escalações para a partida pela 33ª rodada do Brasileirão Logo UOL UOL Flash"
        result = compactar_titulo(title)
        self.assertTrue(result.startswith("Santos x Palmeiras:"))
        self.assertLessEqual(len(result), 65)
        self.assertNotRegex(result, r"\b(de|do|da|para|pela|com|e|que)$")

    def test_long_summary_uses_a_complete_sentence(self):
        summary = "Renato Cariani, de 50 anos, é um dos nomes mais conhecidos do universo fitness brasileiro. Empresário, fisiculturista e influenciador digital, ele conquistou"
        result = compactar_texto(summary, 140)
        self.assertEqual(result, "Renato Cariani, de 50 anos, é um dos nomes mais conhecidos do universo fitness brasileiro.")
        self.assertLessEqual(len(result), 140)

    def test_summary_without_safe_sentence_uses_complete_neutral_copy(self):
        result = compactar_texto("A resposta pode estar nos genes mas também passa pela vida social e pelo acesso à saúde", 140)
        self.assertEqual(result, "")

    def test_merge_uses_body_when_source_summary_is_truncated(self):
        now = datetime(2026, 10, 28, 12, tzinfo=timezone.utc)
        article = self.article(
            "body-fallback", "pet", "https://example.org/body-fallback",
            "Wed, 28 Oct 2026 11:00:00 GMT"
        )
        article["linha_fina"] = "A descrição foi cortada antes de terminar"
        article["corpo"] = "A notícia explica como os moradores podem participar da iniciativa. O restante dos detalhes está disponível na fonte original."
        result = merge_active_articles(
            {"materias": []}, previous_feed={"materias": [article]}, now=now
        )
        self.assertEqual(
            result["materias"][0]["linha_fina_carrossel"],
            "A notícia explica como os moradores podem participar da iniciativa."
        )

    def test_summary_skips_measurement_fragment_and_uses_next_complete_sentence(self):
        text = "O negócio cresceu até se tornar uma indústria com aproximadamente 4.500 m² em Osasco, na Grande São Paulo. Hoje, atende academias, estúdios, clubes, hotéis e condomínios."
        self.assertEqual(
            compactar_texto(text, 140),
            "Hoje, atende academias, estúdios, clubes, hotéis e condomínios."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
