#!/bin/sh
if [ ! -d "./env" ]
then
    echo ""
    echo "Environment not created. Creating it..."
    ./prepare-env.sh
    echo "Done"
fi

. env/bin/activate
python retag-resources/application/controller.py $@
deactivate
