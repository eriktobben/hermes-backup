#!/bin/bash
# Legger til 8G ekstra swap (/swapfile2) — totalt 14G swap på boksen.
# Kjør med sudo:  sudo bash ~/.hermes/scripts/add-swap.sh
set -euo pipefail

SIZE=8G
FILE=/swapfile2

if swapon --show | grep -q "$FILE"; then
  echo "$FILE er allerede aktiv:"
  swapon --show
  exit 0
fi

echo "Oppretter $FILE ($SIZE)..."
fallocate -l "$SIZE" "$FILE"
chmod 600 "$FILE"
mkswap "$FILE" >/dev/null
swapon "$FILE"

if ! grep -qF "$FILE" /etc/fstab; then
  echo "$FILE none swap sw 0 0" >> /etc/fstab
  echo "La til $FILE i /etc/fstab (overlever reboot)"
fi

echo ""
echo "=== Ferdig ==="
swapon --show
free -h | grep -i swap
