"""Testes básicos do protótipo editorial, sem dependências externas."""
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))

from validar_config import validate_config
from ciclo_editorial import select_cycle, validate_candidate


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
