"""Triagem opcional de pautas com Gemini. Não redige nem publica artigos.

Requer GEMINI_API_KEY. O modelo recebe apenas metadados e resumos do RSS;
a avaliação é preliminar e não equivale à verificação da matéria.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "prototipo" / "saida" / "descoberta-fontes.json"
OUTPUT_PATH = ROOT / "prototipo" / "saida" / "triagem-gemini.json"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3.8-flash"
MAX_CANDIDATES = 20
REQUEST_TIMEOUT_SECONDS = 120
MAX_GEMINI_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (3, 8)
MAX_RESPONSE_BYTES = 1_000_000


def build_prompt(items: list[dict], pillars: list[str]) -> str:
    candidates = [{
        "pilar": item.get("pilar", ""),
        "titulo": item.get("titulo", ""),
        "url_agregador": item.get("url_agregador", ""),
        "fonte_publicadora": item.get("fonte_publicadora", ""),
        "url_fonte_publicadora": item.get("url_fonte_publicadora", ""),
        "publicado_em": item.get("publicado_em", ""),
        "descricao_rss": item.get("descricao_rss", "")[:600]
    } for item in items[:MAX_CANDIDATES]]
    return f"""Você faz a triagem preliminar de pautas do Guia Comercial, com foco no Núcleo Bandeirante e regiões próximas de Brasília/DF.

PILARES PERMITIDOS: {json.dumps(pillars, ensure_ascii=False)}

REGRAS:
- Use somente candidatos fornecidos. Não invente nem altere títulos, URLs, fontes ou datas.
- Avalie relevância local, atualidade aparente, utilidade e adequação ao pilar.
- Resumo de RSS não é prova de veracidade.
- Descarte clickbait, conteúdo sem utilidade clara ou fora do pilar.
- Saúde, veterinária, pet e exercício físico exigem revisão especializada adicional.
- Se os dados forem insuficientes, marque verificacao_insuficiente=true.
- Não invente fatos, citações, dados, estabelecimentos ou recomendações.
- Não escreva artigos nem publique. Não complete cotas com pautas fracas.
- No máximo 2 candidatos por pilar.
- Retorne somente JSON válido, sem Markdown:
{{"itens":[{{"url_agregador":"URL exata do candidato","pontuacao":0,"decisao":"revisar","motivos":["motivo breve"],"verificacao_insuficiente":true}}]}}
- decisão permitida: revisar ou descartar. Pontuação inteira 0–100. Inclua apenas candidatos com possível valor editorial.

CANDIDATOS:
{json.dumps(candidates, ensure_ascii=False)}
"""


def extract_json(response: dict) -> dict:
    try:
        data = json.loads(response["candidates"][0]["content"]["parts"][0]["text"])
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Resposta Gemini ausente ou não é JSON válido.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("itens"), list):
        raise ValueError("Resposta Gemini não contém a lista 'itens'.")
    return data


def validate_triage(data: dict, source_items: list[dict], pillars: list[str]) -> dict:
    source_by_url = {item.get("url_agregador"): item for item in source_items if item.get("url_agregador")}
    selected, seen_urls = [], set()
    rejected = 0

    for result in data["itens"]:
        if not isinstance(result, dict):
            rejected += 1
            continue
        url = result.get("url_agregador")
        source = source_by_url.get(url)
        if source is None or url in seen_urls:
            rejected += 1
            continue
        seen_urls.add(url)
        score, decision, reasons = result.get("pontuacao"), result.get("decisao"), result.get("motivos", [])
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
            rejected += 1
            continue
        if decision not in {"revisar", "descartar"} or not isinstance(reasons, list):
            rejected += 1
            continue
        pillar = source.get("pilar")
        if pillar not in pillars:
            rejected += 1
            continue
        if decision == "descartar":
            continue
        if sum(1 for item in selected if item["pilar"] == pillar) >= 2:
            rejected += 1
            continue
        selected.append({
            "pilar": pillar,
            "titulo": source.get("titulo", ""),
            "url_agregador": url,
            "fonte_publicadora": source.get("fonte_publicadora", ""),
            "url_fonte_publicadora": source.get("url_fonte_publicadora", ""),
            "publicado_em": source.get("publicado_em", ""),
            "pontuacao_gemini": score,
            "motivos_triagem": [str(reason)[:240] for reason in reasons[:5]],
            "verificacao_insuficiente": result.get("verificacao_insuficiente") is not False,
            "status_editorial": "triagem_pendente_verificacao_da_fonte_original"
        })
    selected.sort(key=lambda item: (-item["pontuacao_gemini"], item["pilar"], item["titulo"].casefold()))
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "modo": "triagem assistida por IA; sem verificação factual",
        "publicacao_oficial": False,
        "total_candidatos_recebidos": len(source_items),
        "total_recomendados_para_revisao": len(selected),
        "respostas_rejeitadas_por_validacao": rejected,
        "resumo_por_pilar": {pillar: sum(1 for item in selected if item["pilar"] == pillar) for pillar in pillars},
        "aviso": "O Gemini avaliou apenas metadados e resumos RSS. Abra a matéria original, confira fatos e datas e registre a verificação antes de redigir ou publicar.",
        "itens": selected
    }


def call_gemini(api_key: str, model: str, prompt: str) -> dict:
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
    }).encode("utf-8")
    request = urllib.request.Request(
        API_URL.format(model=model), data=payload, method="POST",
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"}
    )

    retryable_statuses = {408, 429, 500, 502, 503, 504}
    last_error = None

    for attempt in range(1, MAX_GEMINI_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise RuntimeError("Resposta do Gemini excedeu o limite permitido.")
            return json.loads(body.decode("utf-8"))

        except urllib.error.HTTPError as exc:
            details = exc.read(2000).decode("utf-8", errors="replace").replace("\\n", " ").replace("\\r", " ")
            last_error = RuntimeError(f"Gemini respondeu HTTP {exc.code}: {details[:1200]}")
            if exc.code not in retryable_statuses:
                raise last_error from exc

        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = RuntimeError(f"Não foi possível acessar o Gemini: {type(exc).__name__}.")
        
        if attempt < MAX_GEMINI_ATTEMPTS:
            delay = RETRY_DELAYS_SECONDS[attempt - 1]
            print(f"Gemini temporariamente indisponível; nova tentativa em {delay}s ({attempt + 1}/{MAX_GEMINI_ATTEMPTS}).")
            time.sleep(delay)

    raise RuntimeError(
        f"Gemini não respondeu após {MAX_GEMINI_ATTEMPTS} tentativas. Último erro: {last_error}"
    ) from last_error


def main() -> int:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("GEMINI_API_KEY ausente; triagem Gemini não executada.")
        print("A descoberta RSS continua válida e nenhum conteúdo foi publicado.")
        return 0
    try:
        report = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
        config = json.loads((ROOT / "config" / "editorial.json").read_text(encoding="utf-8"))
        items = report.get("itens", [])
        if not isinstance(items, list):
            raise ValueError("O relatório RSS não contém uma lista de itens.")
        response = call_gemini(api_key, os.environ.get("GEMINI_MODEL", DEFAULT_MODEL), build_prompt(items, config["pillars"]))
        result = validate_triage(extract_json(response), items, config["pillars"])
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Candidatos recebidos: {len(items)}")
        print(f"Pautas recomendadas para revisão: {result['total_recomendados_para_revisao']}")
        print(f"Relatório: {OUTPUT_PATH.relative_to(ROOT)}")
        print("Nenhum artigo foi redigido ou publicado.")
        return 0
    except (OSError, json.JSONDecodeError, KeyError, ValueError, RuntimeError) as exc:
        print(f"ERRO na triagem Gemini: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
