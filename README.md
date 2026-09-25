# Boletín semanal de tecnología

El proyecto recopila noticias tecnológicas en español a diario, conserva las publicaciones de los últimos siete días y genera un boletín PDF cada viernes a las 23:15, hora de Honduras. El sitio presenta las noticias recientes con imágenes cuando la fuente RSS las incluye. GitHub Actions guarda las publicaciones y publica el PDF; el envío por correo es opcional.

## Fuentes

Las fuentes se configuran en `src/fetch_sources.py`: Xataka, Applesfera, MuyComputer e Hipertextual. Cubren novedades de software, inteligencia artificial, dispositivos, ciencia y cultura digital. Las publicaciones se deduplican por enlace. Cada noticia conserva su fecha, medio, resumen, imagen disponible y enlace a la publicación original.

## Activar el resumen con IA (opcional)

El boletín funciona sin una clave de IA y genera un resumen de respaldo a partir de los artículos recopilados. Para pedir una síntesis editorial más amplia, configura `OPENROUTER_API_KEY` en **Settings → Secrets and variables → Actions**. El modelo predeterminado es `openrouter/free`; su disponibilidad y límites pueden cambiar.

El workflow recopila fuentes diariamente. Los viernes genera el PDF en `reportes/`, guarda el archivo en `site/informe.pdf` y publica la web. Una ejecución manual desde **Actions → Boletín semanal de tecnología → Run workflow** también crea un boletín.

## Probar localmente

Necesitas Python 3.10 o posterior. En la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

La clave de OpenRouter es opcional. Recopila y genera el boletín así:

```powershell
.\.venv\Scripts\python.exe main.py collect
.\.venv\Scripts\python.exe main.py report
```

Los artículos enlazan a las fuentes originales. La selección y disponibilidad de imágenes dependen de la información incluida en cada feed RSS.
