#!/usr/bin/env bash
# Inicia desde la ubicación del script, con entorno ya preparado.
set -euo pipefail
# Ubica módulos y modelo.
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
# Usa el Python de la venv sin modificar instalaciones del sistema.
exec .venv/bin/python -m uvicorn servidor:app --host 0.0.0.0 --port 8001 --workers 1
