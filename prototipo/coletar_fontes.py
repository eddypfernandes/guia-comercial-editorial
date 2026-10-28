"""Coleta itens de descoberta por Google News RSS, sem redigir nem publicar.

Os resultados são pistas para revisão. O agregador não substitui a leitura da
matéria original e não é prova de que cada afirmação seja verdadeira.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "fontes.json"
OUTPUT_PATH = ROOT / "prototipo" / "saida" / "descoberta-fontes.json"
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


def collect(config: dict, opener=fetch_feed) -> dict:
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    all_items: list[dict] = []
    feed_status: list[dict] = []
    timeout = int(config.get("timeout_seconds", 20))
    max_bytes = int(config.get("max_response_bytes", 2_000_000))
    limit = int(config.get("max_items_per_pillar", 12))

    for query_config in config.get("queries", []):
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
            items = deduplicate(items)[:limit]
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
    return {
        "gerado_em": fetched_at,
        "modo": "descoberta por RSS; revisão editorial obrigatória",
        "provedor": config.get("provider", "RSS"),
        "total_itens": len(all_items),
        "total_feeds": len(feed_status),
        "feeds_com_sucesso": sum(1 for feed in feed_status if feed["status"] == "ok"),
        "aviso": "Os resultados são sugestões de pauta. Não representam verificação factual, aprovação editorial ou autorização de publicação.",
        "feeds": feed_status,
        "itens": all_items
    }


def main() -> int:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERRO ao ler {CONFIG_PATH.relative_to(ROOT)}: {exc}")
        return 1

    report = collect(config)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Feeds consultados: {report['feeds_com_sucesso']}/{report['total_feeds']}")
    print(f"Itens descobertos: {report['total_itens']}")
    print(f"Relatório: {OUTPUT_PATH.relative_to(ROOT)}")
    print("Nenhuma matéria foi redigida ou publicada.")
    return 0 if report["feeds_com_sucesso"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
