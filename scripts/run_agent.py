#!/usr/bin/env python3
"""Launch a client with local MCP environment variables without sourcing shell code."""
import os
import sys
from install import credentials

if len(sys.argv) < 2 or sys.argv[1] not in ('codex', 'claude'):
    sys.exit('Usage: scripts/run-agent {codex|claude} [client arguments...]')
try:
    env = dict(os.environ)
    values = credentials()
    for key in ('COOLIFY_API_TOKEN', 'COOLIFY_MCP_URL'):
        if key in values:
            env[key] = values[key]
    os.execvpe(sys.argv[1], sys.argv[1:], env)
except (ValueError, OSError):
    sys.exit('Unable to launch client; check installation and local MCP configuration.')
