cat > test.sh <<'TESTEOF'
#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════╗"
echo "║  🧪 SoniTranslate Pro — Test                 ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

source venv/bin/activate 2>/dev/null || {
    echo "❌ Entorno virtual no encontrado"
    echo "   Ejecuta primero: ./install.sh"
    exit 1
}

PASS=0
FAIL=0

test_cmd() {
    if command -v "$1" &>/dev/null; then
        echo "  ✅ $1: $($1 --version 2>&1 | head -1)"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $1: no encontrado"
        FAIL=$((FAIL + 1))
    fi
}

test_py() {
    result=$(python3 -c "$2" 2>&1)
    if [ $? -eq 0 ]; then
        echo "  ✅ $1: $result"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $1: $result"
        FAIL=$((FAIL + 1))
    fi
}

echo "━━━ Sistema ━━━"
test_cmd "python3"
test_cmd "ffmpeg"
test_cmd "espeak-ng"

echo ""
echo "━━━ Python Core ━━━"
test_py "PyTorch" "import torch; print(f'{torch.__version__} (CPU)')"
test_py "Gradio" "import gradio; print(gradio.__version__)"
test_py "Faster-Whisper" "from faster_whisper import WhisperModel; print('OK')"
test_py "CTranslate2" "import ctranslate2; print(ctranslate2.__version__)"

echo ""
echo "━━━ TTS ━━━"
test_py "Edge-TTS" "import edge_tts; print('OK')"
test_py "gTTS" "from gtts import gTTS; print('OK')"

echo ""
echo "━━━ Audio ━━━"
test_py "Librosa" "import librosa; print(librosa.__version__)"
test_py "SoundFile" "import soundfile; print(soundfile.__version__)"
test_py "NumPy" "import numpy; print(numpy.__version__)"
test_py "PyDub" "from pydub import AudioSegment; print('OK')"
test_py "NoiseReduce" "import noisereduce; print('OK')"

echo ""
echo "━━━ Traducción ━━━"
test_py "Deep-Translator" "from deep_translator import GoogleTranslator; print('OK')"

echo ""
echo "━━━ Utils ━━━"
test_py "yt-dlp" "import yt_dlp; print(yt_dlp.version.__version__)"
test_py "LangID" "import langid; print('OK')"

echo ""
echo "━━━ Test de Edge-TTS (genera audio) ━━━"
python3 -c "
import asyncio, tempfile, os
async def test():
    import edge_tts
    out = tempfile.mktemp(suffix='.mp3')
    c = edge_tts.Communicate('Test de voz exitoso', voice='es-ES-AlvaroNeural')
    await c.save(out)
    size = os.path.getsize(out)
    os.remove(out)
    return size
size = asyncio.run(test())
print(f'Audio generado: {size} bytes')
" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Edge-TTS genera audio correctamente"
    PASS=$((PASS + 1))
else
    echo "  ❌ Edge-TTS falló al generar audio"
    FAIL=$((FAIL + 1))
fi

echo ""
echo "━━━ Test de Whisper (carga modelo tiny) ━━━"
python3 -c "
from faster_whisper import WhisperModel
m = WhisperModel('tiny', device='cpu', compute_type='int8')
print('Modelo tiny cargado correctamente')
del m
" 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Whisper tiny funciona"
    PASS=$((PASS + 1))
else
    echo "  ⚠️  Whisper tiny falló (se descargará en primer uso)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Resultados: ✅ $PASS pasaron | ❌ $FAIL fallaron"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "  🎉 ¡Todo perfecto! Ejecuta: ./start.sh"
else
    echo ""
    echo "  ⚠️  Hay $FAIL problemas. Revisa e intenta:"
    echo "     pip install <paquete_faltante>"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TESTEOF

chmod +x test.sh
