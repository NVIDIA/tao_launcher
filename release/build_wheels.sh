#!/bin/bash

# Please make sure to run the command from the repo root.
PY_VER=('3.6', '3.7', '3.8')

LAUNCHER_ROOT=$PWD

shell_command="python /tao_launcher/release/tao/setup.py bdist_wheel \
&& mkdir -p /tao_launcher/dist && cp /dist/*.whl /tao_launcher/dist/ && rm -rf /tao_launcher/*.egg-info"
 
for ver in "${PY_VER[@]}"
do
    echo $LAUNCHER_ROOT, $ver
    docker run -it --rm -v $LAUNCHER_ROOT:/tao_launcher python:$ver bash -c "$shell_command"
done
