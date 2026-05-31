# Despliegue en AWS Debian

## Objetivo

Desplegar Organigrama Studio en un servidor EC2 Debian con acceso administrativo.

IP objetivo: 3.139.102.241

## Prerrequisitos locales

1. Tener la llave PEM disponible en tu máquina local.
2. Tener instalados: ssh, rsync, git.
3. Haber clonado este repositorio localmente.

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

## 4) Operación diaria

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

## 5) Recomendaciones de producción

1. Configurar Security Group para exponer solo puertos necesarios.
2. Colocar reverse proxy con TLS (Nginx/Caddy) si usarás dominio.
3. Habilitar backups de instancia o AMI.
4. Monitorear uso de CPU/RAM por cargas de Whisper.
