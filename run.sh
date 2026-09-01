#!/usr/bin/env bash
# Entry point used by our automated check. Keep this working: ./run.sh orders.csv payments.csv
exec node "$(dirname "$0")/reconcile.js" "$@"
