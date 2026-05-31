# Despliegue en AWS Debian

## Objetivo

Desplegar Organigrama Studio en un servidor EC2 Debian con acceso administrativo.

IP objetivo: 3.139.102.241

## Prerrequisitos locales

1. Tener la llave PEM disponible en tu máquina local.
2. Tener instalados: ssh, rsync, git.
3. Haber clonado este repositorio localmente.
4. Tener un dominio apuntando por registro A al servidor (ej: organigrama.nexaflow-ia.com -> 3.139.102.241).

## 1) Preparar el servidor (una sola vez)

Conéctate como admin y ejecuta bootstrap de Docker:

```bash
ssh -i /RUTA/A/TU/KEY.pem admin@3.139.102.241
```

Luego en el servidor:

```bash
sudo bash -c 'cat > /tmp/bootstrap.sh' < scripts/bootstrap_debian_docker.sh
sudo bash /tmp/bootstrap.sh
```

Nota: el script instala Docker/Compose y `rsync` (requerido por `deploy_remote.sh`).

Alternativa recomendada: copiar el script y ejecutarlo:

```bash
scp -i /RUTA/A/TU/KEY.pem scripts/bootstrap_debian_docker.sh admin@3.139.102.241:/tmp/bootstrap_debian_docker.sh
ssh -i /RUTA/A/TU/KEY.pem admin@3.139.102.241 "sudo bash /tmp/bootstrap_debian_docker.sh"
```

## 2) Desplegar aplicación

En tu máquina local, dentro del repositorio:

```bash
export PEM_PATH="/RUTA/A/TU/KEY.pem"
export SERVER_IP="3.139.102.241"
export SSH_USER="admin"
./scripts/deploy_remote.sh
```

Esto realiza:

1. Verificación SSH.
2. Sincronización del código en /opt/organigrama.
3. Build y levantamiento con docker compose.

## 3) Verificar estado

En el servidor:

```bash
sudo docker ps
sudo docker compose -f /opt/organigrama/docker-compose.yml logs -f
curl http://localhost:8000/api/health
```

Desde navegador:

```text
http://3.139.102.241:8000
```

## 4) Publicar con dominio en puerto 80 (Nginx reverse proxy)

En el servidor Debian:

```bash
sudo apt-get update
sudo apt-get install -y nginx
```

Crear sitio Nginx:

```bash
sudo tee /etc/nginx/sites-available/organigrama > /dev/null <<'EOF'
server {
	listen 80;
	listen [::]:80;
	server_name organigrama.nexaflow-ia.com;

	location / {
		proxy_pass http://127.0.0.1:8000;
		proxy_http_version 1.1;
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;
		proxy_read_timeout 300;
	}
}
EOF

sudo ln -sf /etc/nginx/sites-available/organigrama /etc/nginx/sites-enabled/organigrama
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

Prueba local en servidor:

```bash
curl -H 'Host: organigrama.nexaflow-ia.com' http://127.0.0.1/api/health
```

## 5) Habilitar HTTPS con Let's Encrypt

Prerrequisito: Security Group con puerto 80 abierto para validación ACME.

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d organigrama.nexaflow-ia.com --agree-tos --email TU_EMAIL@DOMINIO.COM --non-interactive --redirect
sudo nginx -t
sudo systemctl reload nginx
```

Validación:

```bash
curl -I https://organigrama.nexaflow-ia.com
curl https://organigrama.nexaflow-ia.com/api/health
```

Renovación automática:

```bash
systemctl list-timers --all | grep certbot
```

## 6) Operación diaria

Actualizar despliegue:

```bash
./scripts/deploy_remote.sh
```

Reiniciar servicio:

```bash
ssh -i /RUTA/A/TU/KEY.pem admin@3.139.102.241 "cd /opt/organigrama && sudo docker compose restart"
```

Parar servicio:

```bash
ssh -i /RUTA/A/TU/KEY.pem admin@3.139.102.241 "cd /opt/organigrama && sudo docker compose down"
```

Ver logs de app:

```bash
ssh -i /RUTA/A/TU/KEY.pem admin@3.139.102.241 "cd /opt/organigrama && sudo docker compose logs -f"
```

Ver logs de Nginx:

```bash
ssh -i /RUTA/A/TU/KEY.pem admin@3.139.102.241 "sudo tail -f /var/log/nginx/error.log"
```

## 7) Troubleshooting

Error `rsync: command not found`:

```bash
ssh -i /RUTA/A/TU/KEY.pem admin@3.139.102.241 "sudo apt-get update && sudo apt-get install -y rsync"
```

Error de build Whisper `ModuleNotFoundError: No module named 'pkg_resources'`:

1. Verificar que el Dockerfile incluya `pip install --no-build-isolation`.
2. Verificar `setuptools<81` en el paso de instalación.

Error `No space left on device` durante build:

1. Ejecutar limpieza de Docker en servidor: `sudo docker system prune -af`.
2. Usar `torch` CPU-only en `requirements.txt`.
3. Considerar ampliar volumen EBS si el disco está al límite.

Timeout al abrir dominio:

1. Confirmar DNS A -> IP del servidor.
2. Abrir Security Group inbound en 80/443.
3. Confirmar Nginx escuchando en `0.0.0.0:80` y `0.0.0.0:443`.

## 8) Recomendaciones de producción

1. Configurar Security Group para exponer solo puertos necesarios (80/443).
2. Mantener reverse proxy con TLS (Nginx/Certbot).
3. Habilitar backups de instancia o AMI.
4. Monitorear uso de CPU/RAM por cargas de Whisper.
