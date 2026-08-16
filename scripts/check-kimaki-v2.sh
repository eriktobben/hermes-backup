#!/usr/bin/env bash
# Sjekk om Kimaki har fått OpenCode v2-støtte
# Kjøres daglig via cron

KIMAKI_CURRENT="0.25.0"
KIMAKI_LATEST=$(npm view kimaki version 2>/dev/null)

if [ -z "$KIMAKI_LATEST" ]; then
    echo "❌ Kunne ikke hente Kimaki-versjon fra npm"
    exit 1
fi

if [ "$KIMAKI_LATEST" = "$KIMAKI_CURRENT" ]; then
    # Ingen endring — stille
    exit 0
fi

# Ny versjon funnet — sjekk om den har v2-støtte
echo "🔔 Kimaki oppdatert: $KIMAKI_CURRENT → $KIMAKI_LATEST"

# Sjekk dependency-endringer
npm view kimaki@latest dependencies 2>/dev/null | grep -i "opencode"

echo ""
echo "📦 Installer for å se om v2-støtte er lagt til:"
echo "   npm install -g kimaki@$KIMAKI_LATEST"
echo ""
echo "🔗 Sjekk: https://www.npmjs.com/package/kimaki"
