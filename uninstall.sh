cat > uninstall.sh <<'UNINSTEOF'
#!/bin/bash

echo "🗑️  Desinstalar SoniTranslate Pro"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

read -p "¿Eliminar entorno virtual y caché? (s/N): " confirm
if [[ "$confirm" =~ ^[sS]$ ]]; then
    echo "  Eliminando entorno virtual..."
    rm -rf "$SCRIPT_DIR/venv"
    
    echo "  Limpiando caché temporal..."
    rm -rf /tmp/sonitranslate
    
    echo "  Limpiando caché de modelos..."
    rm -rf ~/.cache/huggingface/hub/models--Systran--faster-whisper-*
    
    echo "  ✅ Limpieza completada"
    echo "  ℹ️  Los archivos del proyecto siguen en: $SCRIPT_DIR"
    echo "  ℹ️  Para reinstalar: ./install.sh"
else
    echo "  Cancelado"
fi
UNINSTEOF

chmod +x uninstall.sh
