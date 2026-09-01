#!/usr/bin/env bash
# Entry point used by our automated check. Keep this working: ./run.sh orders.csv payments.csv
exec python3 "$(dirname "$0")/reconcile.py" "$@"
