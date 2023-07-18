#!/bin/bash

# setting bash source.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: This script should be sourced into the current shell.  Use the following syntax:"
    echo ""
    echo "    . scripts/envsetup.sh"
    echo ""
    exit 1
fi

export NV_TAO_LAUNCHER_TOP="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

$NV_TAO_LAUNCHER_TOP/scripts/git-hooks/install_hooks.sh