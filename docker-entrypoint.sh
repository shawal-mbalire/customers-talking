#!/bin/sh
# Generate Angular runtime env from container environment variables.
# This file is written into the static folder before gunicorn starts.
cat > /app/static/env.js << ENVEOF
window.__env = {
  apiUrl: '',
  neonAuthUrl: '${NEON_AUTH_BASE_URL:-}',
};
ENVEOF

exec "$@"
