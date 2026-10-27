"""Abre links de descoberta, extrai texto público e registra evidências técnicas.

A extração não comprova a veracidade das afirmações. Páginas bloqueadas,
paywalls ou conteúdo dependente de JavaScript ficam pendentes de revisão humana.
"""
from __future__ import annotations

import ipaddress
import json
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_PATH = ROOT / "prototipo" / "saida" / "descoberta-fontes.json"
TRIAGE_PATH = ROOT / "prototipo" / "saida" / "triagem-gemini.json"
OUTPUT_PATH = ROOT / "prototipo" / "saida" / "fontes-verificadas.json"
USER_AGENT = "GuiaComercialEditorialPrototype/0.2 (+https://github.com/eddypfernandes/guia-comercial-editorial)"
MAX_BYTES = 2_000_000
MAX_TEXT_CHARS = 12_000
MIN_TEXT_CHARS = 500
TIMEOUT = 18


def validate_public_url(url: str) -> str:
    """Aceita apenas HTTPS público e rejeita endereços locais/privados."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("URL bloqueada: somente HTTPS é permitido.")
    if parsed.username or parsed.password:
        raise ValueError("URL com credenciais embutidas não é permitida.")
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Host local não permitido.")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None and (not ip.is_global):
        raise ValueError("Endereço IP não público bloqueado.")
    if ip is None:
        try:
            addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
        except OSError as exc:
            raise ValueError("Não foi possível resolver o domínio da fonte.") from exc
        if not addresses or any(not ipaddress.ip_address(addr.split("%", 1)[0]).is_global for addr in addresses):
            raise ValueError("Domínio resolve para endereço não público; acesso bloqueado.")
    return url


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.description = ""
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self._in_title = False
        self._skip_depth = 0
        self._skip_tags = {"script", "style", "noscript", "svg", "nav", "footer", "header", "aside", "form"}
        self._paragraph_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag == "a" and not self._skip_depth and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag in self._skip_tags:
            self._skip_depth += 1
        if tag == "meta" and attrs.get("name", "").lower() in {"description", "og:description"}:
            self.description = attrs.get("content", "").strip()[:1000]
        if tag == "meta" and attrs.get("property", "").lower() == "og:description":
            self.description = attrs.get("content", "").strip()[:1000]
        if tag == "p" and not self._skip_depth:
            self._paragraph_depth += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in self._skip_tags and self._skip_depth:
            self._skip_depth -= 1
        if tag == "p" and self._paragraph_depth:
            self._paragraph_depth -= 1

    def handle_data(self, data):
        value = " ".join(data.split())
        if not value:
            return
        if self._in_title:
            self.title_parts.append(value)
        if not self._skip_depth and self._paragraph_depth:
            self.text_parts.append(value)


def extract_html(html: str) -> dict:
    parser = ArticleParser()
    parser.feed(html)
    text = " ".join(parser.text_parts)
    # Evita repetições triviais e mantém o limite de conteúdo enviado ao modelo.
    text = " ".join(text.split())[:MAX_TEXT_CHARS]
    return {
        "titulo_pagina": " ".join(parser.title_parts).strip()[:300],
        "descricao_pagina": parser.description,
        "texto_extraido": text,
        "caracteres_extraidos": len(text),
        "links": parser.links[:100],
    }


def fetch_page(url: str, opener=None) -> tuple[str, str, str]:
    validate_public_url(url)
    opener = opener or urllib.request.build_opener(SafeRedirectHandler())
    request = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
    })
    with opener.open(request, timeout=TIMEOUT) as response:
        final_url = response.geturl()
        validate_public_url(final_url)
        content_type = response.headers.get("Content-Type", "").lower()
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Página excedeu o limite de 2 MB.")
    if "html" not in content_type and not body.lstrip().lower().startswith((b"<!doctype html", b"<html", b"<head", b"<body")):
        raise ValueError("A URL final não retornou uma página HTML.")
    html = body.decode("utf-8", errors="replace")
    return final_url, content_type, html


def select_candidates(discovery: dict, triage: dict | None) -> list[dict]:
    if triage and isinstance(triage.get("itens"), list):
        return triage["itens"][:10]
    # Sem Gemini, manter amostra equilibrada: no máximo duas pautas por pilar.
    selected, counts = [], {}
    for item in discovery.get("itens", []):
        pillar = item.get("pilar", "")
        if counts.get(pillar, 0) >= 2:
            continue
        selected.append(item)
        counts[pillar] = counts.get(pillar, 0) + 1
        if len(selected) >= 10:
            break
    return selected


def verify_item(item: dict, opener=None) -> dict:
    started = time.monotonic()
    source_url = item.get("url_agregador") or item.get("url_fonte_publicadora", "")
    record = {
        "pilar": item.get("pilar", ""),
        "titulo_pauta": item.get("titulo", ""),
        "url_agregador": item.get("url_agregador", ""),
        "fonte_publicadora": item.get("fonte_publicadora", ""),
        "url_fonte_informada": source_url,
        "publicado_em_rss": item.get("publicado_em", ""),
        "consultado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status_verificacao": "pendente",
        "evidencia_tecnica": "Abertura de página e extração de texto não comprovam a veracidade das afirmações.",
    }
    try:
        final_url, content_type, html = fetch_page(source_url, opener=opener)
        extracted = extract_html(html)
        host_final = (urllib.parse.urlsplit(final_url).hostname or "").lower()
        if host_final == "news.google.com" or host_final.endswith(".news.google.com"):
            publisher_host = (urllib.parse.urlsplit(item.get("url_fonte_publicadora", "")).hostname or "").lower()
            candidates = []
            for href in extracted.get("links", []):
                candidate = urllib.parse.urljoin(final_url, href)
                parsed = urllib.parse.urlsplit(candidate)
                host = (parsed.hostname or "").lower()
                if parsed.scheme != "https" or not host or host == "google.com" or host.endswith(".google.com") or host == "news.google.com" or host.endswith(".news.google.com"):
                    continue
                candidates.append(candidate)
            candidates.sort(key=lambda url: 0 if publisher_host and (urllib.parse.urlsplit(url).hostname or "").lower().endswith(publisher_host) else 1)
            if candidates:
                source_url = candidates[0]
                final_url, content_type, html = fetch_page(source_url, opener=opener)
                extracted = extract_html(html)
                host_final = (urllib.parse.urlsplit(final_url).hostname or "").lower()
        record.update({
            "url_final": final_url,
            "content_type": content_type,
            "titulo_pagina": extracted["titulo_pagina"],
            "descricao_pagina": extracted["descricao_pagina"],
            "texto_extraido": extracted["texto_extraido"],
            "caracteres_extraidos": extracted["caracteres_extraidos"],
            "duracao_segundos": round(time.monotonic() - started, 2),
        })
        if host_final == "news.google.com" or host_final.endswith(".news.google.com"):
            record["status_verificacao"] = "pendente_link_agregador"
            record["erro"] = "O agregador não revelou um link externo para a matéria original."
        elif extracted["caracteres_extraidos"] < MIN_TEXT_CHARS:
            record["status_verificacao"] = "pendente_texto_insuficiente"
            record["erro"] = "Texto extraído insuficiente; revisar manualmente ou acessar a fonte."
        else:
            record["status_verificacao"] = "pagina_original_extraida_revisao_factual_pendente"
    except (OSError, ValueError, urllib.error.URLError, TimeoutError, socket.gaierror) as exc:
        record["erro"] = f"{type(exc).__name__}: {str(exc)[:300]}"
        record["duracao_segundos"] = round(time.monotonic() - started, 2)
    return record


def main() -> int:
    try:
        discovery = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))
        triage = json.loads(TRIAGE_PATH.read_text(encoding="utf-8")) if TRIAGE_PATH.exists() else None
        candidates = select_candidates(discovery, triage)
        if not isinstance(candidates, list):
            raise ValueError("Lista de candidatos inválida.")
        records = [verify_item(item) for item in candidates if isinstance(item, dict)]
        report = {
            "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total_candidatos": len(records),
            "total_com_texto_extraido": sum(1 for r in records if r.get("caracteres_extraidos", 0) >= MIN_TEXT_CHARS),
            "total_pendentes": sum(1 for r in records if not r.get("status_verificacao", "").startswith("pagina_original_extraida")),
            "publicacao_oficial": False,
            "aviso": "Extração técnica não é checagem factual. Toda pauta exige conferência humana de autoria, data, fatos, contexto e adequação antes da redação/publicação.",
            "itens": records,
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Candidatos analisados: {report['total_candidatos']}")
        print(f"Páginas com texto extraído: {report['total_com_texto_extraido']}")
        print(f"Pautas pendentes: {report['total_pendentes']}")
        for record in records:
            detail = record.get("erro", "texto extraído; revisão factual pendente")
            print(f"[{record.get('status_verificacao')}] {record.get('titulo_pauta', '')[:100]} — {detail}")
        print(f"Relatório: {OUTPUT_PATH.relative_to(ROOT)}")
        print("A extração não certifica fatos e nenhuma matéria foi publicada.")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERRO na verificação de fontes: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
