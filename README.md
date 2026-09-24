# Informe semanal de ciberseguridad

El proyecto recopila novedades de fuentes de ciberseguridad a diario, conserva una ventana de siete días y genera un PDF cada viernes a las 23:15, hora de Honduras. GitHub Actions guarda el archivo de recopilación entre ejecuciones y publica el PDF como artefacto descargable. El envío por correo es opcional.

## Activar GitHub Actions

1. Crea una clave gratuita en [OpenRouter](https://openrouter.ai/settings/keys).
2. En GitHub abre el repositorio y ve a **Settings → Secrets and variables → Actions → New repository secret**.
3. Pon `OPENROUTER_API_KEY` como nombre y pega allí la clave. El README anterior pedía `ANTHROPIC_API_KEY`, pero el código de este proyecto usa OpenRouter y necesita exactamente `OPENROUTER_API_KEY`.
4. En **Settings → Actions → General → Workflow permissions**, activa **Read and write permissions** para que la tarea pueda guardar la recopilación semanal.
5. Sube la carpeta `.github/workflows/weekly-report.yml` junto con los demás archivos.

El modelo predeterminado es `openrouter/free`. El nivel gratuito tiene límites de uso y disponibilidad variables; si el modelo no está disponible, el informe puede fallar y habrá que reintentarlo. [Modelos gratuitos y límites de OpenRouter](https://openrouter.ai/collections/free-models/).

El workflow corre diariamente a las 23:15 en Honduras. Cada ejecución recopila y conserva novedades de los últimos siete días. Los viernes genera el informe en `reportes/`, lo publica en **Actions → ejecución → Artifacts** y lo envía por correo solo si configuras los secretos `EMAIL_ADDRESS`, `EMAIL_PASSWORD` y `EMAIL_TO`. Una ejecución manual desde **Actions → Informe semanal de ciberseguridad → Run workflow** también crea un informe.

## Probar localmente

Necesitas Python 3.10 o posterior. En la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Pega tu clave de OpenRouter en `OPENROUTER_API_KEY` dentro de `.env`. No subas ese archivo a GitHub. Ejecuta la recopilación diaria:

```powershell
.\.venv\Scripts\python.exe main.py collect
```

Genera el PDF a partir de lo recopilado:

```powershell
.\.venv\Scripts\python.exe main.py report
```

## Fuentes y límites

Las fuentes se configuran en `src/fetch_sources.py`: CISA, NIST, OWASP, The Hacker News y Krebs on Security. Se conservan entradas de los últimos siete días y se deduplican por enlace. El informe prioriza recomendaciones defensivas basadas en esos resúmenes y enlaces; no descarga el texto completo de cada artículo. Las fuentes RSS pueden omitir publicaciones o dejar de estar disponibles.
