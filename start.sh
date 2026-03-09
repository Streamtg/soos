cat > start.sh <<'STARTEOF'
#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════╗"
echo "║  🎬 SoniTranslate Pro                        ║"
echo "╚══════════════════════════════════════════════╝"

# Activar entorno
if [ ! -d "venv" ]; then
    echo "❌ Entorno no encontrado. Ejecuta primero: ./install.sh"
    exit 1
fi

source venv/bin/activate

# Verificación rápida
python3 -c "import gradio, torch, faster_whisper, edge_tts" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependencias faltantes. Ejecuta: ./install.sh"
    exit 1
fi

# Detectar IP local
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="localhost"
fi

echo ""
echo "  🌐 URL Local:   http://localhost:7860"
echo "  🌐 URL Red:     http://${LOCAL_IP}:7860"
echo ""
echo "  Ctrl+C para detener"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ejecutar con manejo de errores
python3 app.py 2>&1 || {
    echo ""
    echo "❌ La aplicación se detuvo con error"
    echo "   Revisa los mensajes anteriores"
    echo "   O ejecuta: ./test.sh"
}
STARTEOF

chmod +x start.sh
