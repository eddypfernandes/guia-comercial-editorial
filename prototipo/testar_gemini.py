import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))
from curar_com_gemini import extract_json, validate_triage


class GeminiTriageTests(unittest.TestCase):
    def test_extract_json(self):
        self.assertEqual(extract_json({"candidates": [{"content": {"parts": [{"text": '{"itens": []}'}]}}]}), {"itens": []})

    def test_only_known_urls_and_max_two_per_pillar(self):
        sources = [
            {"pilar": "pet", "titulo": "Pauta um", "url_agregador": "https://example.org/1"},
            {"pilar": "pet", "titulo": "Pauta dois", "url_agregador": "https://example.org/2"},
            {"pilar": "pet", "titulo": "Pauta três", "url_agregador": "https://example.org/3"}
        ]
        data = {"itens": [
            {"url_agregador": "https://example.org/1", "pontuacao": 90, "decisao": "revisar", "motivos": []},
            {"url_agregador": "https://example.org/2", "pontuacao": 80, "decisao": "revisar", "motivos": []},
            {"url_agregador": "https://example.org/3", "pontuacao": 70, "decisao": "revisar", "motivos": []},
            {"url_agregador": "https://invented.example/", "pontuacao": 99, "decisao": "revisar", "motivos": []}
        ]}
        result = validate_triage(data, sources, ["pet", "lazer", "esportes", "saude", "fitness"])
        self.assertEqual(len(result["itens"]), 2)
        self.assertEqual(result["respostas_rejeitadas_por_validacao"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
