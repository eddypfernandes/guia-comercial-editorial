import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "prototipo"))
from resumir_materias import MAX_SUMMARY_WORDS, contar_palavras, resumir_corpo


class ResumidorLocalTests(unittest.TestCase):
    def test_limit_is_440_words(self):
        self.assertEqual(MAX_SUMMARY_WORDS, 440)

    def test_short_text_and_source_paragraphs_are_preserved(self):
        text = (
            "A primeira informação apresenta o fato principal. A segunda explica o contexto.\n\n"
            "O terceiro ponto detalha a decisão. A matéria termina com o resultado."
        )
        self.assertEqual(resumir_corpo(text, "Fato principal"), text)

    def test_navigation_question_is_removed_without_losing_context(self):
        text = (
            "O STF acolheu o pedido da defesa para suspender temporariamente as visitas. "
            "A decisão considerou a recomendação médica.\n\n"
            "A defesa poderá solicitar novos encontros quando houver melhora. Não chegou ainda?"
        )
        summary = resumir_corpo(text, "STF suspende visitas")
        self.assertNotIn("Não chegou ainda", summary)
        self.assertIn("A decisão considerou a recomendação médica.", summary)
        self.assertIn("novos encontros quando houver melhora.", summary)
        self.assertTrue(summary.endswith("melhora."))

    def test_over_limit_text_keeps_consecutive_sentences_in_source_order(self):
        sentences = [
            "Abertura " + ("contexto " * 99) + ".",
            "Segundo " + ("informação " * 99) + ".",
            "Terceiro " + ("detalhe " * 99) + ".",
            "Quarto " + ("resultado " * 99) + ".",
            "Quinto " + ("desdobramento " * 99) + ".",
        ]
        text = " ".join(sentences)
        summary = resumir_corpo(text, "Notícia contextualizada")
        self.assertEqual(contar_palavras(summary), 400)
        self.assertLessEqual(contar_palavras(summary), MAX_SUMMARY_WORDS)
        self.assertTrue(summary.startswith("Abertura"))
        self.assertIn("Quarto", summary)
        self.assertNotIn("Quinto", summary)
        self.assertTrue(summary.endswith("."))

    def test_oversized_single_sentence_is_cut_at_the_word_limit(self):
        text = " ".join(["conteúdo"] * 500)
        summary = resumir_corpo(text, "Conteúdo da matéria")
        self.assertEqual(contar_palavras(summary), MAX_SUMMARY_WORDS)
        self.assertTrue(summary.endswith("…"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
