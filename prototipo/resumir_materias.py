"""Resumo extrativo local para matérias editoriais, sem serviços externos."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEED_PATH = ROOT / "prototipo" / "saida" / "materias-editoriais.json"
MAX_SUMMARY_WORDS = 120
MAX_SUMMARY_PARAGRAPHS = 3
WORD_PATTERN = re.compile(r"(?u)\b[^\W_]+(?:[-’'][^\W_]+)*\b")

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


def contar_palavras(text: str) -> int:
    return len(WORD_PATTERN.findall(str(text or "")))


def formatar_paragrafos(sentences: list[str]) -> str:
    if not sentences:
        return ""

    paragraph_count = min(MAX_SUMMARY_PARAGRAPHS, max(1, (len(sentences) + 1) // 2))
    base_size, remainder = divmod(len(sentences), paragraph_count)
    paragraphs = []
    offset = 0

    for index in range(paragraph_count):
        size = base_size + (1 if index < remainder else 0)
        paragraph = " ".join(sentences[offset:offset + size]).strip()
        if paragraph:
            paragraphs.append(paragraph)
        offset += size

    return "\n\n".join(paragraphs)


def truncar_no_limite_de_palavras(text: str, max_palavras: int) -> str:
    matches = list(WORD_PATTERN.finditer(text))
    if len(matches) <= max_palavras:
        return text.strip()

    result = text[:matches[max_palavras - 1].end()].rstrip(" ,;:")
    if result and result[-1] not in ".!?…":
        result += "…"
    return result


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


def resumir_corpo(text: str, titulo: str = "", max_palavras: int = MAX_SUMMARY_WORDS) -> str:
    """Seleciona frases completas do corpo, limitando palavras e parágrafos."""
    raw_text = str(text or "").strip()
    if not raw_text or max_palavras <= 0:
        return ""

    sentences = []
    for paragraph in re.split(r"\n\s*\n", raw_text):
        sentences.extend(split_sentences(paragraph))
    sentences = [sentence for sentence in sentences if sentence]

    if not sentences:
        return truncar_no_limite_de_palavras(raw_text, max_palavras)

    if contar_palavras(" ".join(sentences)) <= max_palavras:
        return formatar_paragrafos(sentences)

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
    used_words = 0

    # A abertura é preservada sempre que não for texto de navegação ou publicidade.
    first = next(
        (
            i for i, sentence in enumerate(sentences)
            if not NOISE.search(sentence) and contar_palavras(sentence) <= max_palavras
        ),
        None,
    )
    if first is not None:
        chosen.add(first)
        used_words = contar_palavras(sentences[first])

    for index in ranked:
        if index in chosen or sentence_score(sentences[index], index, len(sentences), frequencies, title_terms) < 0:
            continue
        sentence_words = contar_palavras(sentences[index])
        if sentence_words and used_words + sentence_words <= max_palavras:
            chosen.add(index)
            used_words += sentence_words

    if not chosen:
        fallback = next((sentence for sentence in sentences if not NOISE.search(sentence)), sentences[0])
        return truncar_no_limite_de_palavras(fallback, max_palavras)

    selected = [sentences[index] for index in sorted(chosen)]
    result = formatar_paragrafos(selected)

    # Proteção final: nunca ultrapassar o orçamento configurado.
    while contar_palavras(result) > max_palavras and len(selected) > 1:
        selected.pop()
        result = formatar_paragrafos(selected)

    if contar_palavras(result) > max_palavras:
        result = truncar_no_limite_de_palavras(result, max_palavras)

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
                    "Resumo local de até 120 palavras, organizado em até três parágrafos "
                    "a partir de frases completas do texto extraído; não houve reescrita por IA "
                    "nem checagem factual independente. Consulte a fonte original."
                )
                total += 1
        data["aviso"] = (
            "Prévia editorial: o corpo das matérias é resumido localmente em até 120 palavras "
            "e três parágrafos, com frases extraídas do conteúdo original. "
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

