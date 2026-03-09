#!/bin/bash
set -e

SCRATCH=/home/idies/workspace/Temporary/100895/scratch
APP=$SCRATCH/sonitranslate
BIN=$APP/bin
CACHE=$APP/cache
VENV=$APP/venv

mkdir -p $APP $BIN $CACHE

export PATH=$BIN:$PATH
export HF_HOME=$CACHE
export XDG_CACHE_HOME=$CACHE

echo "Instalando en $APP"

cd $APP

python3 -m venv $VENV
source $VENV/bin/activate

pip install --upgrade pip wheel setuptools

echo "Instalando PyTorch CPU"
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

echo "Instalando dependencias"
pip install -r requirements.txt

if ! command -v ffmpeg &>/dev/null; then
echo "Instalando ffmpeg"
cd $BIN
wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar -xf ffmpeg-release-amd64-static.tar.xz
cp ffmpeg-*-static/ffmpeg .
cp ffmpeg-*-static/ffprobe .
chmod +x ffmpeg ffprobe
fi

echo "Instalación terminada"
