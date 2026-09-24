# Informe Semanal de Ciberseguridad con IA

Cada semana este proyecto:

1. Recopila novedades de fuentes oficiales de ciberseguridad (CISA, NIST, OWASP, The Hacker News, Krebs on Security).
2. Usa la API de Claude (Anthropic) para redactar un informe de recomendaciones en español.
3. Genera un PDF con el informe.
4. Lo envía por correo automáticamente y lo guarda en `reportes/`.

Todo corre solo, gratis, mediante **GitHub Actions** (no necesitas tener tu PC encendida).

## 1. Crear el repositorio en GitHub

1. Crea un repositorio nuevo (público o privado) en GitHub, por ejemplo `informe-ciberseguridad-ia`.
2. Sube estos archivos:

```bash
cd cyberreport
git init
git add .
git commit -m "Proyecto inicial: informe semanal de ciberseguridad"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/informe-ciberseguridad-ia.git
git push -u origin main
```

## 2. Configurar los secretos (Settings → Secrets and variables → Actions)

Agrega estos "Repository secrets":

| Nombre | Valor |
|---|---|
| `ANTHROPIC_API_KEY` | Tu API key de [console.anthropic.com](https://console.anthropic.com) |
| `EMAIL_ADDRESS` | El correo desde el que se enviará (ej. Gmail) |
| `EMAIL_PASSWORD` | Una "contraseña de aplicación" (no tu contraseña normal, ver abajo) |
| `EMAIL_TO` | El/los correo(s) que recibirán el PDF |

### Cómo obtener una "contraseña de aplicación" de Gmail
1. Activa la verificación en dos pasos en tu cuenta de Google.
2. Ve a https://myaccount.google.com/apppasswords
3. Genera una contraseña para "Correo" y úsala en `EMAIL_PASSWORD`.

## 3. Activar el workflow

El workflow (`.github/workflows/weekly-report.yml`) ya está configurado para correr:
- **Automáticamente** todos los lunes a las 08:00 UTC.
- **Manualmente** cuando quieras, desde la pestaña **Actions → Informe semanal de ciberseguridad → Run workflow**.

Para probarlo de inmediato: ve a la pestaña "Actions" del repo y ejecútalo manualmente una vez, así verificas que los secretos estén bien puestos antes de esperar al lunes.

## 4. Probarlo en tu computadora (opcional)

```bash
python -m venv venv
source venv/bin/activate   # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # y rellena tus datos reales
python main.py
```

## Estructura del proyecto

```
cyberreport/
├── main.py                          # Orquesta todo el flujo
├── src/
│   ├── fetch_sources.py             # Descarga noticias de fuentes fijas (RSS)
│   ├── summarize.py                 # Usa Claude para redactar el informe
│   ├── generate_pdf.py              # Convierte el informe a PDF
│   └── send_email.py                # Envía el PDF por correo
├── reportes/                        # Aquí se guardan los PDFs generados
├── .github/workflows/weekly-report.yml  # Automatización semanal
├── requirements.txt
└── .env.example
```

## Personalizar

- **Cambiar el día/hora de ejecución**: edita el `cron` en `weekly-report.yml` ([ayuda con cron](https://crontab.guru/)).
- **Agregar más fuentes**: edita el diccionario `SOURCES` en `src/fetch_sources.py`.
- **Cambiar el tono/formato del informe**: edita `SYSTEM_PROMPT` en `src/summarize.py`.
