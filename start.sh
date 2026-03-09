#!/bin/bash

SCRATCH=/home/idies/workspace/Temporary/100895/scratch
APP=$SCRATCH/sonitranslate
BIN=$APP/bin
CACHE=$APP/cache
VENV=$APP/venv

export PATH=$BIN:$PATH
export HF_HOME=$CACHE
export XDG_CACHE_HOME=$CACHE

cd $APP

source $VENV/bin/activate

echo "Iniciando SoniTranslate"

python app.py
