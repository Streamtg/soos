#!/bin/bash
set -e

SCRATCH=/home/idies/workspace/Temporary/100895/scratch
APP_DIR=$SCRATCH/sonitranslate
VENV_DIR=$SCRATCH/sonitranslate/venv
BIN_DIR=$SCRATCH/sonitranslate/bin
CACHE_DIR=$SCRATCH/sonitranslate/cache

mkdir -p $APP_DIR $BIN_DIR $CACHE_DIR

export PATH=$BIN_DIR:$PATH
export HF_HOME=$CACHE_DIR
export XDG_CACHE_HOME=$CACHE_DIR

echo "━━━ Instalación sin root en SCRATCH ━━━"
echo "Directorio: $APP_DIR"
echo ""

cd $APP_DIR

# -------------------------
# Python venv
# -------------------------

echo "Creando entorno Python..."

python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

pip install --upgrade pip wheel setuptools

# -------------------------
# FFmpeg manual
# -------------------------

if ! command -v ffmpeg &>/dev/null; then

echo "Instalando FFmpeg..."

cd $BIN_DIR

wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

tar -xf ffmpeg-release-amd64-static.tar.xz

cp ffmpeg-*-static/ffmpeg .
cp ffmpeg-*-static/ffprobe .

chmod +x ffmpeg ffprobe

cd $APP_DIR

fi

# -------------------------
# espeak opcional
# -------------------------

if ! command -v espeak-ng &>/dev/null; then

echo "Instalando espeak-ng..."

cd $BIN_DIR

wget -q https://github.com/espeak-ng/espeak-ng/releases/download/1.51/espeak-ng-1.51-linux-x86_64.tar.gz || true

tar -xzf espeak-ng-*.tar.gz || true

cd $APP_DIR

fi

# -------------------------
# PyTorch CPU
# -------------------------

echo "Instalando PyTorch CPU..."

pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# -------------------------
# Dependencias
# -------------------------

echo "Instalando dependencias..."

pip install -r requirements.txt

echo ""
echo "Instalación completa."
