#!/usr/bin/env bash
# Run a command inside the IIC-OSIC-TOOLS container with the SKY130 PDK selected
# and this repo mounted at /work.
#
#   scripts/eda.sh ls '$PDK_ROOT'      # check sky130A is there
#   scripts/eda.sh                     # interactive shell
#
# Override the image with:  IMAGE=hpretl/iic-osic-tools:latest scripts/eda.sh ...
set -euo pipefail
IMAGE="${IMAGE:-hpretl/iic-osic-tools:chipathon26}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TTY=(); [ -t 0 ] && [ -t 1 ] && TTY=(-t)
CMD="${*:-bash}"
exec docker run --rm -i ${TTY[@]+"${TTY[@]}"} \
    -v "$ROOT":/work -w /work \
    -e PDK=sky130A \
    --entrypoint bash "$IMAGE" -lc "$CMD"
