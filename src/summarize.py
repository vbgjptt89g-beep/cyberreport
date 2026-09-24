"""
Usa la API de Claude (Anthropic) para leer las entradas recopiladas de
fuentes fijas y redactar un informe de recomendaciones de ciberseguridad
en español, listo para convertir a PDF.
"""

from __future__ import annotations

import os

import anthropic

from .fetch_sources import Entry

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """\
Eres un analista senior de ciberseguridad. Recibes una lista de titulares y \
resúmenes recopilados de fuentes oficiales (CISA, NIST, OWASP, etc.) de la \
última semana. Tu tarea es producir un informe en español, claro y accionable, \
con esta estructura exacta en Markdown:

# Informe semanal de ciberseguridad

## Resumen ejecutivo
(3-5 líneas con lo más relevante de la semana)

## Recomendaciones principales
(Lista de 5 a 10 recomendaciones concretas y priorizadas, cada una en 1-2 líneas)

## Amenazas y vulnerabilidades destacadas
(Lista de las alertas/CVEs/incidentes más relevantes con una breve explicación)

## Buenas prácticas para reforzar esta semana
(3-5 acciones prácticas que un equipo de TI o una persona pueden aplicar ya)

No inventes CVEs ni datos que no estén respaldados por el material recibido. \
Si el material es escaso, sé honesto y da recomendaciones generales de buenas \
prácticas vigentes. No uses markdown de tablas.
"""


def build_source_material(entries: list[Entry]) -> str:
    if not entries:
        return "No se encontraron publicaciones nuevas esta semana en las fuentes monitoreadas."

    lines = []
    for e in entries:
        lines.append(f"- [{e.source}] {e.title}\n  Resumen: {e.summary}\n  Link: {e.link}")
    return "\n".join(lines)


def generate_report(entries: list[Entry]) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Falta la variable de entorno ANTHROPIC_API_KEY")

    client = anthropic.Anthropic(api_key=api_key)
    material = build_source_material(entries)

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Material recopilado esta semana:\n\n{material}",
            }
        ],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts).strip()
