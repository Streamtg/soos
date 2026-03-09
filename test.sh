#!/bin/bash

SCRATCH=/home/idies/workspace/Temporary/100895/scratch
APP=$SCRATCH/sonitranslate
VENV=$APP/venv

source $VENV/bin/activate

echo "Test sistema"

python -c "import torch; print('torch OK')"
python -c "import gradio; print('gradio OK')"
python -c "import faster_whisper; print('whisper OK')"
python -c "import edge_tts; print('edge-tts OK')"
python -c "import librosa; print('librosa OK')"
python -c "import soundfile; print('soundfile OK')"

ffmpeg -version

echo "Test terminado"
