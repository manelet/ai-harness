#!/usr/bin/env python3
"""Private header output for Claude Code only; never run in chat or log stdout."""
import json
import sys
from install import credentials

if len(sys.argv) != 2 or sys.argv[1] != 'COOLIFY_API_TOKEN':
    sys.exit('Unsupported credential reference')
try:
    token = credentials().get(sys.argv[1], '')
    if not token or any(c in token for c in '\r\n'):
        sys.exit('Missing or invalid Coolify credential')
    print(json.dumps({'Authorization': 'Bearer ' + token}))
except (ValueError, OSError):
    sys.exit('Unable to load local MCP credentials')
