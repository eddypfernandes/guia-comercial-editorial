"""Coleta itens de descoberta por Google News RSS, sem redigir nem publicar.

Os resultados são pistas para revisão. O agregador não substitui a leitura da
matéria original e não é prova de que cada afirmação seja verdadeira.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import time
from email.utils import parsedate_to_datetime
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "fontes.json"
OUTPUT_PATH = ROOT / "prototipo" / "saida" / "descoberta-fontes.json"
HISTORY_PATH = ROOT / "prototipo" / "saida" / "historico-pautas.json"
HISTORY_DAYS = 30
USER_AGENT = "GuiaComercialEditorialPrototype/0.1 (+https://github.com/eddypfernandes/guia-comercial-editorial)"


def text_of(parent: ET.Element, name: str) -> str:
    child = parent.find(name)
    return (child.text or "").strip() if child is not None else ""


def make_feed_url(query: str, language: str, region: str, edition: str) -> str:
    # Evita que o Google News preencha o feed com resultados antigos.
    query = f"{query} when:7d"
    params = urllib.parse.urlencode({
        "q": query,
        "hl": language,
        "gl": region,
        "ceid": edition
    })
    return "https://news.google.com/rss/search?" + params


def parse_feed(xml_bytes: bytes, pillar: str, feed_url: str, fetched_at: str) -> list[dict]:
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        raise ValueError("RSS inválido: elemento channel ausente.")

    items: list[dict] = []
    for item in channel.findall("item"):
        title = text_of(item, "title")
        link = text_of(item, "link")
        source_node = item.find("source")
        source_name = (source_node.text or "").strip() if source_node is not None else ""
        source_url = source_node.attrib.get("url", "") if source_node is not None else ""
        if not title or not link:
            continue
        items.append({
            "pilar": pillar,
            "titulo": title,
            "url_agregador": link,
            "fonte_publicadora": source_name or "Fonte não identificada no RSS",
            "url_fonte_publicadora": source_url,
            "publicado_em": text_of(item, "pubDate"),
            "descricao_rss": text_of(item, "description"),
            "feed_consultado": feed_url,
            "consultado_em": fetched_at,
            "status_editorial": "descoberta_pendente_verificacao",
            "observacao": "Pista de pesquisa. Abrir a matéria original e verificar os fatos antes de usar."
        })
    return items


def fetch_feed(url: str, timeout: int, max_bytes: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        body = response.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise ValueError(f"Resposta excede o limite de {max_bytes} bytes.")
    if not body.lstrip().startswith(b"<"):
        raise ValueError(f"Resposta não parece XML RSS (Content-Type: {content_type}).")
    return body


def publication_timestamp(item: dict) -> float:
    """Converte pubDate em timestamp; datas ausentes/inválidas ficam no fim."""
    published = str(item.get("publicado_em", "")).strip()
    if not published:
        return float("-inf")
    try:
        parsed = parsedate_to_datetime(published)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (TypeError, ValueError, OverflowError):
        return float("-inf")


def sort_newest_first(items: list[dict]) -> list[dict]:
    """Prioriza a data original de publicação, não a ordem devolvida pelo RSS."""
    return sorted(items, key=publication_timestamp, reverse=True)


def deduplicate(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for item in items:
        key = item["url_agregador"].split("&", 1)[0].rstrip("/").casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result



def normalize_title(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "").casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def history_keys(item: dict) -> set[str]:
    pillar = str(item.get("pilar", "")).strip().casefold()
    url = str(item.get("url_agregador", "")).strip().split("&", 1)[0].rstrip("/").casefold()
    title = normalize_title(item.get("titulo", ""))
    keys = set()
    if url:
        keys.add("url:" + url)
    if pillar and title:
        keys.add("title:" + pillar + ":" + title)
    return keys


def filter_seen_pautas(items: list[dict], history: dict,
                        now: datetime | None = None) -> tuple[list[dict], dict]:
    """Retira pautas já descobertas nos últimos 30 dias."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    cutoff = now.timestamp() - HISTORY_DAYS * 86400
    records = []
    seen = set()
    for record in history.get("registros", []):
        if not isinstance(record, dict):
            continue
        try:
            registered = datetime.fromisoformat(record.get("registrado_em", "").replace("Z", "+00:00"))
            if registered.tzinfo is None:
                registered = registered.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
        if registered.timestamp() < cutoff:
            continue
        records.append(record)
        seen.update(record.get("chaves", []))

    fresh = []
    for item in items:
        keys = history_keys(item)
        if not keys or keys.intersection(seen):
            continue
        fresh.append(item)
        seen.update(keys)
        records.append({
            "pilar": item.get("pilar", ""),
            "titulo": item.get("titulo", "")[:300],
            "url_agregador": item.get("url_agregador", ""),
            "registrado_em": now.isoformat(timespec="seconds"),
            "chaves": sorted(keys),
        })
    return fresh, {
        "atualizado_em": now.isoformat(timespec="seconds"),
        "retencao_dias": HISTORY_DAYS,
        "total_registros": len(records),
        "registros": records,
    }


def rotate_queries(queries: list[dict], cycle_number: int = 0) -> list[dict]:
    """Alterna o pilar inicial entre execuções sem alterar a configuração."""
    if not queries:
        return []
    offset = max(0, int(cycle_number)) % len(queries)
    return queries[offset:] + queries[:offset]


def collect(config: dict, opener=fetch_feed, cycle_number: int = 0, history: dict | None = None) -> dict:
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    all_items: list[dict] = []
    feed_status: list[dict] = []
    timeout = int(config.get("timeout_seconds", 20))
    max_bytes = int(config.get("max_response_bytes", 2_000_000))
    limit = int(config.get("max_items_per_pillar", 12))

    ordered_queries = rotate_queries(config.get("queries", []), cycle_number)
    for query_config in ordered_queries:
        pillar = query_config.get("pillar", "")
        query = query_config.get("query", "")
        if not pillar or not query:
            feed_status.append({"pilar": pillar, "status": "erro", "erro": "Pilar ou consulta ausente."})
            continue
        url = make_feed_url(query, config.get("language", "pt-BR"), config.get("region", "BR"), config.get("edition", "BR:pt-419"))
        started = time.monotonic()
        try:
            xml_bytes = opener(url, timeout, max_bytes)
            items = parse_feed(xml_bytes, pillar, url, fetched_at)
            # O Google News RSS pode devolver itens fora de ordem cronológica.
            # Ordenar antes do limite impede que notícias novas sejam descartadas.
            items = sort_newest_first(deduplicate(items))[:limit]
            all_items.extend(items)
            feed_status.append({
                "pilar": pillar,
                "status": "ok",
                "itens_encontrados": len(items),
                "duracao_segundos": round(time.monotonic() - started, 2)
            })
        except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError, OSError) as exc:
            feed_status.append({
                "pilar": pillar,
                "status": "erro",
                "erro": f"{type(exc).__name__}: {exc}",
                "duracao_segundos": round(time.monotonic() - started, 2)
            })

    all_items = deduplicate(all_items)
    fresh_items, updated_history = filter_seen_pautas(all_items, history or {})
    return {
        "gerado_em": fetched_at,
        "modo": "descoberta por RSS; revisão editorial obrigatória",
        "provedor": config.get("provider", "RSS"),
        "total_itens": len(fresh_items),
        "itens_repetidos_ignorados": len(all_items) - len(fresh_items),
        "historico_pautas": updated_history,
        "total_feeds": len(feed_status),
        "ciclo_numero": max(0, int(cycle_number)),
        "ordem_pilares": [query.get("pillar", "") for query in ordered_queries],
        "feeds_com_sucesso": sum(1 for feed in feed_status if feed["status"] == "ok"),
        "aviso": "Os resultados são sugestões de pauta. Não representam verificação factual, aprovação editorial ou autorização de publicação.",
        "feeds": feed_status,
        "itens": fresh_items
    }


def main() -> int:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERRO ao ler {CONFIG_PATH.relative_to(ROOT)}: {exc}")
        return 1

    import os
    cycle_number = int(os.environ.get("EDITORIAL_CYCLE_NUMBER", "0"))
    try:
        history = json.loads(HISTORY_PATH.read_text(encoding="utf-8")) if HISTORY_PATH.exists() else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERRO ao ler histórico de pautas: {exc}")
        return 1
    report = collect(config, cycle_number=cycle_number, history=history)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(report.pop("historico_pautas"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Feeds consultados: {report['feeds_com_sucesso']}/{report['total_feeds']}")
    print(f"Itens descobertos: {report['total_itens']}")
    print(f"Relatório: {OUTPUT_PATH.relative_to(ROOT)}")
    print("Nenhuma matéria foi redigida ou publicada.")
    return 0 if report["feeds_com_sucesso"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
