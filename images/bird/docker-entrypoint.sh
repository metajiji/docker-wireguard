#!/bin/sh

set -eu

[ "${BIRD_ENTRYPOINT_DEBUG:-0}" = 1 ] || set -x

if [ -z "${BIRD_ENTRYPOINT_QUIET_LOGS:-}" ]; then
    exec 3>&1
else
    exec 3>/dev/null
fi

_SELF=$(basename $0)

if [ "$1" = "bird" ]; then
    _template=/etc/bird-templates/bird.conf.template
    _output=/etc/bird/bird.conf

    if [ ! -w "$_output" -a -f "$_output" ]; then
        echo >&3 "$_SELF: ERROR: $_output is not writable"
        exit 1
    fi

    _envs=$(printf '${%s} ' $(env | cut -d= -f1))
    echo >&3 "$_SELF: Running envsubst on $_template to $_output"
    envsubst "$_envs" < "$_template" > "$_output"

    echo >&3 "$0: Configuration complete; ready for start up"
fi

exec "$@"
