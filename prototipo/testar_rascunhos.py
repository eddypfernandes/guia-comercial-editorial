import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))
from redigir_rascunhos import extract_json, validate_drafts


class DraftValidationTests(unittest.TestCase):
    def test_extract_json(self):
        self.assertEqual(extract_json({"candidates": [{"content": {"parts": [{"text": '{"rascunhos": []}'}]}}]}), {"rascunhos": []})

    def test_rejects_unknown_source_and_keeps_review_gate(self):
        source = [{
            "pilar": "lazer",
            "fonte_publicadora": "Jornal Exemplo",
            "url_final": "https://example.org/noticia",
            "status_verificacao": "pagina_original_extraida_revisao_factual_pendente",
        }]
        body = "Este é um rascunho de teste com texto suficiente para passar pela validação estrutural. " * 5
        drafts = {"rascunhos": [
            {"pilar": "lazer", "titulo": "Título válido", "corpo": body,
             "fontes": [{"nome": "Jornal Exemplo", "url": "https://example.org/noticia"}],
             "pontos_a_verificar": ["Confirmar data"], "apto_para_revisao": True},
            {"pilar": "lazer", "titulo": "Fonte inventada", "corpo": body,
             "fontes": [{"nome": "Outro", "url": "https://invented.example/article"}],
             "pontos_a_verificar": [], "apto_para_revisao": True}
        ]}
        result = validate_drafts(drafts, source)
        self.assertEqual(result["total_rascunhos_validos"], 1)
        self.assertEqual(result["respostas_rejeitadas"], 1)
        self.assertFalse(result["publicacao_oficial"])
        self.assertEqual(result["rascunhos"][0]["status_editorial"], "rascunho_nao_publicavel_revisao_humana_obrigatoria")


if __name__ == "__main__":
    unittest.main(verbosity=2)
