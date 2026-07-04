#!/usr/bin/env bash
# build-dist.sh — copy index.html → dist/index.html and inject the backend URL.
#
# Usage:
#   ./build-dist.sh https://mbs-v8bxla.fly.dev
#
# If no argument is given, the last known API_BASE in dist/index.html is kept.

set -euo pipefail

API_URL="${1:-}"

cp index.html dist/index.html

if [[ -n "$API_URL" ]]; then
  python3 -c "
import re, sys
with open('dist/index.html', 'r') as f:
    content = f.read()
content = re.sub(r\"const API_BASE = '[^']*'\", \"const API_BASE = '${API_URL}'\", content)
with open('dist/index.html', 'w') as f:
    f.write(content)
print('Built dist/index.html with API_BASE = ${API_URL}')
"
else
  echo "Copied dist/index.html (API_BASE unchanged)"
fi
