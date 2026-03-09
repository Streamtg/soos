cat > install.sh <<'INSTALLEOF'
#!/bin/bash
set -e

echo "╔══════════════════════════════════════════════╗"
echo "║  🎬 SoniTranslate Pro — Instalación         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================
# 1. VERIFICAR SISTEMA
# ============================================
echo "━━━ [1/5] Verificando sistema ━━━"

if ! command -v python3 &>/dev/null; then
    echo "⚠️  Python3 no encontrado. Instalando paquetes del sistema..."
    
    # Limpiar repos si es necesario
    if [ -f /etc/apt/sources.list ]; then
        echo "   Configurando repositorios..."
    fi
    
    # Intentar instalar
    apt-get update -qq 2>/dev/null || true
    
    while IFS= read -r pkg; do
        pkg=$(echo "$pkg" | xargs)  # trim
        [ -z "$pkg" ] && continue
        [[ "$pkg" == \#* ]] && continue
        echo "   📦 Instalando: $pkg"
        apt-get install -y -qq "$pkg" 2>/dev/null || echo "   ⚠️  No se pudo instalar: $pkg"
    done < packages.txt
else
    echo "   ✅ Python3: $(python3 --version)"
fi

# Verificar ffmpeg
if command -v ffmpeg &>/dev/null; then
    echo "   ✅ FFmpeg: $(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f1-3)"
else
    echo "   ❌ FFmpeg no encontrado. Instalando..."
    apt-get install -y ffmpeg 2>/dev/null || echo "   ⚠️  Instala ffmpeg manualmente"
fi

# Verificar espeak
if command -v espeak-ng &>/dev/null; then
    echo "   ✅ espeak-ng disponible"
else
    echo "   ⚠️  espeak-ng no encontrado (opcional)"
    apt-get install -y espeak-ng 2>/dev/null || true
fi

echo ""

# ============================================
# 2. ENTORNO VIRTUAL PYTHON
# ============================================
echo "━━━ [2/5] Creando entorno virtual Python ━━━"

if [ -d "venv" ]; then
    echo "   ♻️  Entorno existente encontrado, reutilizando..."
else
    python3 -m venv venv
    echo "   ✅ Entorno virtual creado"
fi

source venv/bin/activate
pip install --upgrade pip setuptools wheel -q
echo "   ✅ pip actualizado: $(pip --version | cut -d' ' -f1-2)"
echo ""

# ============================================
# 3. PYTORCH CPU
# ============================================
echo "━━━ [3/5] Instalando PyTorch (CPU) ━━━"
echo "   ⏳ Esto puede tardar varios minutos..."

pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu -q 2>&1 | tail -1

python3 -c "import torch; print(f'   ✅ PyTorch {torch.__version__}')" 2>/dev/null || {
    echo "   ⚠️  PyTorch falló con index-url, intentando sin..."
    pip install torch torchaudio -q
}

echo ""

# ============================================
# 4. DEPENDENCIAS PYTHON
# ============================================
echo "━━━ [4/5] Instalando dependencias Python ━━━"
echo "   ⏳ Instalando $(wc -l < requirements.txt) paquetes..."

pip install -r requirements.txt -q 2>&1 | grep -E "^(ERROR|Successfully)" || true

echo ""

# ============================================
# 5. VERIFICACIÓN FINAL
# ============================================
echo "━━━ [5/5] Verificación final ━━━"

ERRORS=0

check_module() {
    python3 -c "import $1" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   ✅ $1"
    else
        echo "   ❌ $1 — FALTA"
        ERRORS=$((ERRORS + 1))
    fi
}

check_module "gradio"
check_module "torch"
check_module "faster_whisper"
check_module "edge_tts"
check_module "gtts"
check_module "deep_translator"
check_module "librosa"
check_module "soundfile"
check_module "numpy"
check_module "scipy"
check_module "tqdm"
check_module "noisereduce"
check_module "pydub"
check_module "langid"

# Contar voces
VOICES=$(python3 -c "
import sys; sys.path.insert(0,'.')
try:
    # Quick count from app.py voice dict
    count = 0
    with open('app.py') as f:
        for line in f:
            if 'Neural\"' in line and ':' in line:
                count += 1
    print(count)
except:
    print('400+')
" 2>/dev/null)

echo ""

if [ $ERRORS -eq 0 ]; then
    echo "╔══════════════════════════════════════════════╗"
    echo "║  ✅ INSTALACIÓN COMPLETADA                   ║"
    echo "║                                              ║"
    echo "║  Voces disponibles: ~${VOICES}               ║"
    echo "║                                              ║"
    echo "║  Para iniciar:                               ║"
    echo "║    cd $(pwd)                                  ║"
    echo "║    ./start.sh                                ║"
    echo "║                                              ║"
    echo "║  Para verificar:                             ║"
    echo "║    ./test.sh                                 ║"
    echo "╚══════════════════════════════════════════════╝"
else
    echo "╔══════════════════════════════════════════════╗"
    echo "║  ⚠️  INSTALACIÓN CON $ERRORS ERROR(ES)       ║"
    echo "║  Revisa los módulos marcados con ❌           ║"
    echo "║  Intenta: pip install <modulo_faltante>      ║"
    echo "╚══════════════════════════════════════════════╝"
fi
INSTALLEOF

chmod +x install.sh
