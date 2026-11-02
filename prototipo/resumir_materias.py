"""Resumo extrativo local para matérias editoriais, sem serviços externos."""
from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "prototipo" / "saida" / "materias-editoriais.json"
MAX_SUMMARY_LINES = 25
LINE_WIDTH = 42

STOP_WORDS = set("""
a à ao aos as até com como da das de dela dele deles delas do dos e é ela elas ele eles em entre era eram essa esse essas esses esta este estas estes eu foi foram há isso isto já lhe lhes mais mas me mesmo minha minhas meu meus na nas não nem no nos nós nossa nossas nosso nossos num numa o os ou para pela pelas pelo pelos por qual quando que quem se sem ser seu seus sua suas são só também tem têm ter um uma umas uns vai vão você vocês sobre após antes durante segundo conforme ainda então onde muito muita muitos muitas cada todo toda todos todas
""".split())

NOISE = re.compile(
    r"(?i)(aceite os cookies|política de privacidade|termos de uso|"
    r"compartilhe esta notícia|siga nossas redes|assine nossa newsletter|"
    r"publicidade|anúncio|leia também|mais lidas|todos os direitos reservados|"
    r"carregando\.\.\.|clique aqui|cadastre-se para receber)"
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


def wrapped_line_count(text: str, width: int = LINE_WIDTH) -> int:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text or "") if part.strip()]
    if not paragraphs:
        return 0
    return sum(max(1, len(textwrap.wrap(p, width=width, break_long_words=False, break_on_hyphens=False))) for p in paragraphs) + len(paragraphs) - 1


def sentence_score(sentence: str, index: int, total: int, frequencies: dict[str, int], title_terms: set[str]) -> float:
    words = re.findall(r"[a-záàâãéêíóôõúüç]{3,}", sentence.casefold())
    terms = [word for word in words if word not in STOP_WORDS]
    if not terms or NOISE.search(sentence):
        return -100.0
    distinct = set(terms)
    frequency_score = sum(min(frequencies.get(word, 1), 3) for word in distinct) / (len(distinct) ** 0.5)
    title_score = 2.5 * len(distinct & title_terms)
    position_score = max(0.0, 1.25 - (index / max(total, 1)) * 0.9)
    length_score = 0.7 if 70 <= len(sentence) <= 280 else (-0.8 if len(sentence) < 45 else -0.2)
    return frequency_score + title_score + position_score + length_score


def resumir_corpo(text: str, titulo: str = "", max_linhas: int = MAX_SUMMARY_LINES) -> str:
    """Seleciona frases completas e relevantes, mantendo a ordem original e o contexto."""
    original = re.sub(r"\s+", " ", str(text or "")).strip()
    if not original:
        return ""
    if wrapped_line_count(original) <= max_linhas:
        return original

    sentences = split_sentences(original)
    if len(sentences) <= 2:
        return original

    frequencies: dict[str, int] = {}
    for sentence in sentences:
        for word in set(re.findall(r"[a-záàâãéêíóôõúüç]{3,}", sentence.casefold())):
            if word not in STOP_WORDS:
                frequencies[word] = frequencies.get(word, 0) + 1

    title_terms = {
        word for word in re.findall(r"[a-záàâãéêíóôõúüç]{3,}", str(titulo).casefold())
        if word not in STOP_WORDS
    }
    ranked = sorted(
        range(len(sentences)),
        key=lambda index: sentence_score(sentences[index], index, len(sentences), frequencies, title_terms),
        reverse=True,
    )

    chosen: set[int] = set()
    used_lines = 0

    # A abertura é preservada sempre que não for texto de navegação ou publicidade.
    first = next((i for i, sentence in enumerate(sentences) if not NOISE.search(sentence)), None)
    if first is not None:
        lines = max(1, len(textwrap.wrap(sentences[first], width=LINE_WIDTH, break_long_words=False, break_on_hyphens=False)))
        if lines <= max_linhas:
            chosen.add(first)
            used_lines = lines

    for index in ranked:
        if index in chosen or sentence_score(sentences[index], index, len(sentences), frequencies, title_terms) < 0:
            continue
        lines = max(1, len(textwrap.wrap(sentences[index], width=LINE_WIDTH, break_long_words=False, break_on_hyphens=False)))
        extra = lines + (1 if chosen else 0)
        if used_lines + extra <= max_linhas:
            chosen.add(index)
            used_lines += extra

    if not chosen:
        chosen.add(0)

    selected = [sentences[index] for index in sorted(chosen)]
    paragraphs = []
    for start in range(0, len(selected), 2):
        paragraphs.append(" ".join(selected[start:start + 2]))
    result = "\n\n".join(paragraphs).strip()

    # Proteção final: nunca ultrapassar o limite configurado.
    while wrapped_line_count(result) > max_linhas and len(selected) > 1:
        selected.pop()
        paragraphs = [" ".join(selected[start:start + 2]) for start in range(0, len(selected), 2)]
        result = "\n\n".join(paragraphs).strip()
    return result


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
                    "Resumo automático por seleção de frases completas do texto extraído; "
                    "não houve reescrita por IA nem checagem factual independente. Consulte a fonte original."
                )
                total += 1
        data["aviso"] = (
            "Prévia editorial: textos resumidos localmente em até 25 linhas aproximadas, "
            "com frases extraídas do conteúdo original. Publicação oficial permanece desativada."
        )
        FEED_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Resumo local aplicado a {total} matéria(s); limite de {MAX_SUMMARY_LINES} linhas.")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERRO ao resumir matérias: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
