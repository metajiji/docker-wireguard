#!/bin/bash

set -xeu

_term() {
  echo "Caught SIGTERM signal!"
  wg-quick down wg0
}

trap _term SIGTERM

# modprobe ip_tables
# modprobe iptable_filter

wg-quick up wg0

sleep infinity &

wait
