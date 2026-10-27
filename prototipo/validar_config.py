"""Valida a configuração não secreta do agente editorial."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "editorial.json"
EXPECTED_PILLARS = {"pet", "lazer", "esportes", "saude", "fitness"}


def validate_config(config: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(config, dict):
        return ["A configuração precisa ser um objeto JSON."]

    pillars = config.get("pillars")
    if not isinstance(pillars, list) or not pillars:
        errors.append("'pillars' precisa ser uma lista não vazia.")
    elif set(pillars) != EXPECTED_PILLARS or len(pillars) != len(EXPECTED_PILLARS):
        errors.append("Os pilares devem ser exatamente: pet, lazer, esportes, saude e fitness.")

    if config.get("mode") != "prototype":
        errors.append("'mode' deve permanecer como 'prototype'.")
    if config.get("official_publication_enabled") is not False:
        errors.append("A publicação oficial precisa permanecer desativada.")

    targets = config.get("target_active_contents_per_pillar")
    if not isinstance(targets, dict):
        errors.append("'target_active_contents_per_pillar' precisa ser um objeto.")
    else:
        minimum = targets.get("minimum")
        maximum = targets.get("maximum")
        if not isinstance(minimum, int) or not isinstance(maximum, int):
            errors.append("Os limites mínimo e máximo precisam ser números inteiros.")
        elif minimum < 0 or maximum < minimum or maximum > 2:
            errors.append("Limites inválidos: máximo permitido por pilar é 2.")

    if not isinstance(config.get("local_focus"), list) or not config["local_focus"]:
        errors.append("'local_focus' precisa listar as regiões atendidas.")
    if not isinstance(config.get("image_ai_disclosure"), str) or not config["image_ai_disclosure"].strip():
        errors.append("'image_ai_disclosure' precisa conter a identificação de imagens de IA.")
    return errors


def main() -> int:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERRO: não foi possível ler {CONFIG_PATH.relative_to(ROOT)}: {exc}")
        return 1

    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERRO: {error}")
        return 1

    print("Configuração editorial válida.")
    print("Modo: protótipo; publicação oficial desativada.")
    print(f"Pilares: {', '.join(config['pillars'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
