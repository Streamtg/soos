#!/bin/bash

SCRATCH=/home/idies/workspace/Temporary/100895/scratch
APP=$SCRATCH/sonitranslate

echo "Eliminando instalación"

rm -rf $APP/venv
rm -rf $APP/cache

echo "Listo"
