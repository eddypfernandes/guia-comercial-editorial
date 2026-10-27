"""Seleciona pautas de um arquivo JSON local, sem pesquisar nem publicar na web.

Entrada: prototipo/entrada/pautas.json
Saída: prototipo/saida/relatorio-ciclo.json

Este módulo prepara e valida um ciclo. A coleta real de fontes será integrada
em etapa posterior; não simula pesquisa externa nem confirma fatos.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "prototipo" / "entrada" / "pautas.json"
OUTPUT_PATH = ROOT / "prototipo" / "saida" / "relatorio-ciclo.json"
CONFIG_PATH = ROOT / "config" / "editorial.json"
REQUIRED_FIELDS = {"id", "titulo", "pilar", "url_fonte", "consultado_em", "validade_ate", "status", "pontuacao"}
ALLOWED_STATUSES = {"coletado", "em_analise", "aprovado", "rejeitado", "retirado"}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def parse_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"'{field}' deve usar o formato AAAA-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"'{field}' inválida: {value!r}. Use AAAA-MM-DD.") from exc


def validate_candidate(item: object, pillars: set[str]) -> tuple[list[str], dict | None]:
    if not isinstance(item, dict):
        return ["Cada pauta precisa ser um objeto JSON."], None
    errors = [f"campo obrigatório ausente: {field}" for field in sorted(REQUIRED_FIELDS - item.keys())]
    if errors:
        return errors, None

    if not isinstance(item["id"], str) or not item["id"].strip():
        errors.append("'id' precisa ser um texto não vazio.")
    if not isinstance(item["titulo"], str) or len(item["titulo"].strip()) < 12:
        errors.append("'titulo' precisa ter pelo menos 12 caracteres.")
    if item["pilar"] not in pillars:
        errors.append(f"pilar desconhecido: {item['pilar']!r}.")
    if not isinstance(item["url_fonte"], str):
        errors.append("'url_fonte' precisa ser uma URL.")
    else:
        parsed = urlparse(item["url_fonte"])
        if parsed.scheme != "https" or not parsed.netloc:
            errors.append("'url_fonte' deve ser uma URL HTTPS válida.")
    if item["status"] not in ALLOWED_STATUSES:
        errors.append(f"status inválido: {item['status']!r}.")
    if not isinstance(item["pontuacao"], (int, float)) or isinstance(item["pontuacao"], bool) or not 0 <= item["pontuacao"] <= 100:
        errors.append("'pontuacao' deve ser um número entre 0 e 100.")
    try:
        consulted = parse_date(item["consultado_em"], "consultado_em")
        expiry = parse_date(item["validade_ate"], "validade_ate")
        if expiry < consulted:
            errors.append("'validade_ate' não pode ser anterior a 'consultado_em'.")
    except ValueError as exc:
        errors.append(str(exc))
    if errors:
        return errors, None
    return [], item


def select_cycle(candidates: list[dict], pillars: list[str], today: date) -> dict:
    selected: list[dict] = []
    rejected: list[dict] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    active_per_pillar = {pillar: 0 for pillar in pillars}

    # Maior pontuação primeiro; desempate pelo título para resultado reproduzível.
    ordered = sorted(candidates, key=lambda item: (-item["pontuacao"], normalize(item["titulo"]), item["id"]))
    for item in ordered:
        reasons: list[str] = []
        normalized_url = item["url_fonte"].rstrip("/").casefold()
        normalized_title = normalize(item["titulo"])

        if item["id"] in seen_ids:
            reasons.append("id duplicado")
        if normalized_url in seen_urls:
            reasons.append("URL de fonte duplicada")
        if normalized_title in seen_titles:
            reasons.append("título duplicado")
        if parse_date(item["validade_ate"], "validade_ate") < today:
            reasons.append("pauta expirada")
        if item["status"] in {"rejeitado", "retirado"}:
            reasons.append(f"status não elegível: {item['status']}")
        if item["status"] not in {"aprovado", "em_analise", "coletado"}:
            if not reasons:
                reasons.append("status não elegível")
        if item["pilar"] in active_per_pillar and active_per_pillar[item["pilar"]] >= 2:
            reasons.append("limite de 2 pautas por pilar atingido")
        if item["pilar"] not in active_per_pillar:
            reasons.append("pilar desconhecido")

        # Registrar identificadores mesmo quando a pauta não é selecionada
        # ajuda a detectar duplicidades dentro da entrada do ciclo.
        seen_ids.add(item["id"])
        seen_urls.add(normalized_url)
        seen_titles.add(normalized_title)

        if reasons:
            rejected.append({"id": item["id"], "titulo": item["titulo"], "motivos": reasons})
            continue

        selected.append({
            "id": item["id"],
            "titulo": item["titulo"],
            "pilar": item["pilar"],
            "url_fonte": item["url_fonte"],
            "consultado_em": item["consultado_em"],
            "validade_ate": item["validade_ate"],
            "pontuacao": item["pontuacao"],
            "status": "em_analise",
            "aviso": "Pauta selecionada para revisão; fatos e fonte ainda precisam ser verificados editorialmente."
        })
        active_per_pillar[item["pilar"]] += 1

    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_referencia": today.isoformat(),
        "modo": "protótipo",
        "publicacao_oficial": False,
        "aviso": "Este relatório não representa pesquisa externa nem validação factual das pautas.",
        "resumo_por_pilar": {
            pillar: {
                "selecionadas": active_per_pillar[pillar],
                "meta_referencia": "1 a 2; não preencher artificialmente"
            }
            for pillar in pillars
        },
        "selecionadas": selected,
        "nao_selecionadas": rejected
    }


def main() -> int:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("Entrada ainda não existe. Crie prototipo/entrada/pautas.json usando pautas.exemplo.json.")
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERRO de leitura JSON: {exc}")
        return 1

    if config.get("official_publication_enabled") is not False:
        print("ERRO: publicação oficial deve permanecer desativada.")
        return 1
    if not isinstance(data, list):
        print("ERRO: a entrada precisa ser uma lista JSON de pautas.")
        return 1

    valid: list[dict] = []
    has_errors = False
    pillars = set(config.get("pillars", []))
    for index, candidate in enumerate(data, start=1):
        errors, item = validate_candidate(candidate, pillars)
        if errors:
            has_errors = True
            print(f"Pauta {index}: " + "; ".join(errors))
        elif item is not None:
            valid.append(item)

    if has_errors:
        print("Ciclo interrompido: corrija as pautas inválidas antes de gerar o relatório.")
        return 1

    report = select_cycle(valid, config["pillars"], date.today())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Ciclo preparado: {len(report['selecionadas'])} pauta(s) selecionada(s).")
    print(f"Relatório: {OUTPUT_PATH.relative_to(ROOT)}")
    print("Nenhum conteúdo foi publicado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
