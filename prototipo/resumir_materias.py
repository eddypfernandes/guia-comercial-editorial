"""Resumo local com continuidade textual e limpeza de ruído editorial."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "prototipo" / "saida" / "materias-editoriais.json"
MAX_SUMMARY_WORDS = 440
WORD_PATTERN = re.compile(r"(?u)\b[^\W_]+(?:[-’'][^\W_]+)*\b")

NOISE = re.compile(
    r"(?i)(aceite os cookies|política de privacidade|termos de uso|"
    r"compartilhe esta notícia|siga nossas redes|assine nossa newsletter|"
    r"publicidade|anúncio|leia também|mais lidas|todos os direitos reservados|"
    r"carregando\.{3}|clique aqui|cadastre-se para receber|"
    r"não chegou ainda|leia no poder360|"
    r"pressione enter para buscar|esc para fechar|"
    r"receba novidades, eventos e benefícios)"
)

ABBREVIATIONS = (
    "Sr", "Sra", "Srta", "Dr", "Dra", "Prof", "Profa", "etc",
    "p.ex", "aprox", "art", "arts", "av", "nº", "n.º",
)


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if not text:
        return []
    marker = "\uE000"
    pattern = re.compile(
        r"(?i)(?<!\w)(?:" + "|".join(re.escape(value) for value in ABBREVIATIONS) + r")\."
    )
    protected = pattern.sub(lambda match: match.group(0)[:-1] + marker, text)
    parts = re.findall(r"""[^.!?]+[.!?]+(?:["'”’»)]*)|[^.!?]+$""", protected)
    return [part.strip().replace(marker, ".") for part in parts if part.strip()]


def contar_palavras(text: str) -> int:
    return len(WORD_PATTERN.findall(str(text or "")))


def truncar_no_limite_de_palavras(text: str, max_palavras: int) -> str:
    matches = list(WORD_PATTERN.finditer(text))
    if len(matches) <= max_palavras:
        return text.strip()

    result = text[:matches[max_palavras - 1].end()].rstrip(" ,;:")
    if result and result[-1] not in ".!?…":
        result += "…"
    return result


def resumir_corpo(text: str, titulo: str = "", max_palavras: int = MAX_SUMMARY_WORDS) -> str:
    """Preserva parágrafos e sequência, removendo ruído e limitando a 440 palavras."""
    raw_text = str(text or "").strip()
    if not raw_text or max_palavras <= 0:
        return ""

    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", raw_text):
        sentences = [
            sentence
            for sentence in split_sentences(paragraph)
            if sentence and not NOISE.search(sentence)
        ]
        if sentences:
            paragraphs.append(sentences)

    total_words = sum(contar_palavras(sentence) for group in paragraphs for sentence in group)
    if total_words <= max_palavras:
        return "\n\n".join(" ".join(group) for group in paragraphs)

    selected_paragraphs = []
    used_words = 0

    # Se exceder o limite, mantém um trecho contínuo em ordem de origem.
    for group in paragraphs:
        selected = []
        for sentence in group:
            sentence_words = contar_palavras(sentence)
            if not sentence_words:
                continue
            if used_words + sentence_words > max_palavras:
                if not selected_paragraphs and not selected:
                    return truncar_no_limite_de_palavras(sentence, max_palavras)
                if selected:
                    selected_paragraphs.append(" ".join(selected))
                return "\n\n".join(selected_paragraphs)
            selected.append(sentence)
            used_words += sentence_words
        if selected:
            selected_paragraphs.append(" ".join(selected))

    return "\n\n".join(selected_paragraphs)


def main() -> int:
    try:
        data = json.loads(FEED_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("materias"), list):
            raise ValueError("Feed editorial inválido: lista 'materias' ausente.")
        total = 0
        for article in data["materias"]:
            if not isinstance(article, dict):
                continue
            original = str(article.get("corpo", "")).strip()
            summary = resumir_corpo(original, str(article.get("titulo", "")))
            if summary:
                article["corpo"] = summary
                article["aviso_editorial"] = (
                    "Texto organizado localmente em até 440 palavras, preservando a sequência "
                    "e os parágrafos do material extraído; chamadas de navegação são removidas. "
                    "Não há reescrita por IA nem checagem factual independente. Consulte a fonte original."
                )
                total += 1
        data["aviso"] = (
            "Prévia editorial: corpos organizados localmente em até 440 palavras, com a sequência "
            "e os parágrafos do material preservados e ruídos de navegação removidos. "
            "Títulos e subtítulos são preservados; publicação oficial permanece desativada."
        )
        FEED_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Resumo local aplicado a {total} matéria(s); limite de {MAX_SUMMARY_WORDS} palavras.")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERRO ao resumir matérias: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
