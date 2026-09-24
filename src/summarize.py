"""
Usa la API de OpenRouter para leer las entradas recopiladas de
fuentes fijas y redactar un informe de recomendaciones de ciberseguridad
en español, listo para convertir a PDF.
"""

from __future__ import annotations

import os

from openai import OpenAI

from .fetch_sources import Entry

# Copia aquí el nombre EXACTO del modelo desde openrouter.ai/models
# (los gratuitos terminan en ":free"; la lista cambia con el tiempo).
MODEL = "openai/gpt-oss-120b:free"

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
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Falta la variable de entorno OPENROUTER_API_KEY")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    material = build_source_material(entries)

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Material recopilado esta semana:\n\n{material}",
            },
        ],
    )

    text = response.choices[0].message.content
    if not text:
        raise RuntimeError("El modelo devolvió una respuesta vacía")
    return text.strip()