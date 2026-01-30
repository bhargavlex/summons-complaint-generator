#!/bin/sh
set -e

# Wait for MySQL to be ready (backend depends_on healthcheck may not be enough for app connect)
echo "Waiting for MySQL at mysql:3306..."
until python -c "
import socket
import sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('mysql', 3306))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "MySQL not ready yet, retrying in 2s..."
    sleep 2
done
echo "MySQL is up."

# Run DB init (creates tables + seeds templates)
echo "Running database init..."
python -m scripts.init_db_mysql || true

exec "$@"
