#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || true)

if [ -n "$script_dir" ] && [ -f "$script_dir/bin/install.js" ]; then
  exec node "$script_dir/bin/install.js" "$@"
fi

exec npx -y github:MichelKazi/slopbliterator "$@"
