#!/usr/bin/env bash
set -euo pipefail

SERVER_IP="${SERVER_IP:-3.139.102.241}"
SSH_USER="${SSH_USER:-admin}"
PEM_PATH="${PEM_PATH:-}"
REMOTE_DIR="${REMOTE_DIR:-/opt/organigrama}"

if [[ -z "${PEM_PATH}" ]]; then
  echo "Define PEM_PATH con la ruta de tu llave .pem" >&2
  exit 1
fi

if [[ ! -f "${PEM_PATH}" ]]; then
  echo "No existe el archivo PEM en: ${PEM_PATH}" >&2
  exit 1
fi

SSH_OPTS=("-o" "StrictHostKeyChecking=accept-new" "-i" "${PEM_PATH}")

echo "[1/4] Verificando acceso SSH..."
ssh "${SSH_OPTS[@]}" "${SSH_USER}@${SERVER_IP}" "echo 'SSH OK'"

echo "[2/4] Creando carpeta remota ${REMOTE_DIR}..."
ssh "${SSH_OPTS[@]}" "${SSH_USER}@${SERVER_IP}" "sudo mkdir -p ${REMOTE_DIR} && sudo chown -R ${SSH_USER}:${SSH_USER} ${REMOTE_DIR}"

echo "[3/4] Copiando proyecto al servidor..."
rsync -az --delete \
  -e "ssh -i ${PEM_PATH} -o StrictHostKeyChecking=accept-new" \
  --exclude ".git" \
  --exclude ".venv" \
  ./ "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/"

echo "[4/4] Construyendo y levantando contenedores..."
ssh "${SSH_OPTS[@]}" "${SSH_USER}@${SERVER_IP}" "cd ${REMOTE_DIR} && sudo docker compose up -d --build"

echo "Despliegue finalizado. Verifica en: http://${SERVER_IP}:8000"
