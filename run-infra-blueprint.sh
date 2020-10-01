#!/bin/sh
CONFIG_PATH=$1

if [ ! -d "./env" ]
then
    echo ""
    echo "Environment not created. Creating it..."
    ./prepare-env.sh
    echo "Done"
fi

. env/bin/activate
python infra-blueprint/reporter/controller.py $CONFIG_PATH
deactivate
