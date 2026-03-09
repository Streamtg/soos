#!/bin/bash

SCRATCH=/home/idies/workspace/Temporary/100895/scratch
APP_DIR=$SCRATCH/sonitranslate
VENV_DIR=$APP_DIR/venv
BIN_DIR=$APP_DIR/bin
CACHE_DIR=$APP_DIR/cache

export PATH=$BIN_DIR:$PATH
export HF_HOME=$CACHE_DIR
export XDG_CACHE_HOME=$CACHE_DIR

cd $APP_DIR

source $VENV_DIR/bin/activate

echo "Iniciando SoniTranslate..."

python app.py
