# Organigrama Studio

Sistema web para:

1. Recibir archivos en formato mp3, mp4 o wav.
2. Transcribir el contenido con Whisper.
3. Proponer un organigrama editable.
4. Dibujar la vista del organigrama en el navegador.
5. Exportar el resultado a formato draw.io (.drawio).

## Requisitos

- Python 3.11+
- ffmpeg instalado en el sistema (necesario para Whisper)

## Arquitectura

La arquitectura completa está documentada en:

- ARCHITECTURE.md

Despliegue operativo en AWS Debian:

- DEPLOY_AWS_DEBIAN.md

En Ubuntu:

```bash
sudo apt update && sudo apt install -y ffmpeg
```

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Abrir en navegador:

```text
http://localhost:8000
```

## Ejecución con Docker (recomendado para servidor)

```bash
docker compose up -d --build
```

Verificar salud:

```bash
curl http://localhost:8000/api/health
```

## Flujo de uso

1. Sube un archivo mp3/mp4/wav.
2. Elige tamaño de modelo Whisper.
3. Haz clic en "Transcribir y generar".
4. Revisa el JSON del organigrama y ajusta nodos/relaciones.
5. Haz clic en "Renderizar organigrama" para ver la vista previa.
6. Haz clic en "Exportar draw.io" para descargar el .drawio.

## Notas

- La inferencia de relaciones jerárquicas desde texto usa reglas simples en español.
- Si la transcripción no contiene relaciones claras, el sistema crea una plantilla base editable.
- Puedes mejorar la precisión cambiando el modelo a small o medium.