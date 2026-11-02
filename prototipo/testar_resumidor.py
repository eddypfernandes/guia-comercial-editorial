import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))
from resumir_materias import resumir_corpo, wrapped_line_count


class ResumidorLocalTests(unittest.TestCase):
    def test_short_text_is_preserved(self):
        text = "A primeira informação apresenta o fato principal. A segunda explica o contexto."
        self.assertEqual(resumir_corpo(text, "Fato principal"), text)

    def test_long_text_is_reduced_to_at_most_25_lines(self):
        sentences = [
            "O projeto anunciado reúne medidas para ampliar o atendimento e melhorar os serviços oferecidos à população.",
            "A iniciativa prevê investimentos em espaços públicos e ações voltadas à comunidade.",
            "Segundo os organizadores, o cronograma será divulgado nos próximos dias.",
            "O programa também inclui atividades gratuitas para diferentes faixas etárias.",
            "A medida foi apresentada durante evento realizado nesta semana.",
        ]
        text = " ".join(sentences * 12)
        summary = resumir_corpo(text, "Projeto amplia atendimento e serviços")
        self.assertLess(len(summary), len(text))
        self.assertLessEqual(wrapped_line_count(summary), 25)

    def test_summary_uses_only_complete_sentences_from_original(self):
        sentences = [
            "A prefeitura anunciou a reforma de três espaços públicos nesta terça-feira.",
            "As obras incluem melhorias de acessibilidade, iluminação e áreas de convivência.",
            "O investimento total informado é de R$ 2 milhões.",
            "Os trabalhos devem começar no próximo mês, segundo o comunicado oficial.",
            "A conclusão está prevista para o segundo semestre."
        ]
        text = " ".join(sentences * 10)
        summary = resumir_corpo(text, "Prefeitura anuncia reforma de espaços públicos")
        for sentence in [part.strip() for part in summary.replace("\n\n", " ").split(".") if part.strip()]:
            self.assertTrue(any(sentence in original for original in sentences), sentence)
        self.assertTrue(summary.endswith("."))

    def test_title_relevance_changes_sentence_selection(self):
        text = (
            "A programação cultural terá apresentações gratuitas durante o fim de semana. "
            "O evento também contará com oficinas para crianças e adultos. "
            "A organização informou que haverá mudanças no trânsito nas ruas próximas. "
        ) * 12
        summary = resumir_corpo(text, "Programação cultural e oficinas gratuitas")
        self.assertIn("programação cultural", summary.casefold())


if __name__ == "__main__":
    unittest.main(verbosity=2)
