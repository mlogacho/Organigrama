# Arquitectura del Sistema

## Resumen

Organigrama Studio es una aplicación web con arquitectura de una sola API backend y frontend estático embebido.

## Componentes

1. API Backend (FastAPI)
- Recibe archivos mp3, mp4 y wav.
- Ejecuta transcripción con Whisper.
- Infiera nodos y relaciones de organigrama desde texto.
- Exporta el organigrama a XML compatible con draw.io.

2. Frontend estático (HTML/CSS/JS)
- Formulario de carga de audio/video.
- Renderizado de organigrama con Mermaid.
- Editor manual de nodos/relaciones en JSON.
- Descarga de archivo .drawio.

3. Motor de transcripción
- Modelo Whisper local.
- Soporte para modelos tiny/base/small/medium.
- Requiere ffmpeg en sistema operativo.

4. Contenerización
- Imagen Docker basada en Python 3.11 slim.
- Servicio único publicado en puerto 8000.
- Healthcheck usando /api/health.

## Flujo End-to-End

1. Usuario sube archivo multimedia.
2. Frontend envía multipart a /api/transcribe.
3. Backend guarda temporalmente el archivo.
4. Whisper genera texto transcrito.
5. Parser de reglas genera JSON de organigrama.
6. Frontend renderiza el diagrama editable.
7. Usuario solicita exportación.
8. Backend genera XML y responde archivo .drawio.

## Estructura de Carpetas

- app/: backend FastAPI y lógica de negocio.
- static/: frontend estático.
- scripts/: automatización de bootstrap y despliegue.
- docker-compose.yml: definición de ejecución en servidor.
- Dockerfile: build de imagen productiva.

## Consideraciones Operativas

- Persistencia: el sistema no requiere base de datos para su flujo actual.
- Archivos temporales: se escriben en tmp_uploads y se eliminan al finalizar cada request.
- Escalabilidad vertical: subir workers de Gunicorn o recursos de EC2.
- Seguridad: se recomienda reverse proxy con TLS si se expone públicamente con dominio.
