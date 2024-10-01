#!/bin/sh

set -e

/opt/etherpad-lite/wait-for-it.sh "$DB_HOST":"$DB_PORT"

# Run the main container command.
exec "$@"
