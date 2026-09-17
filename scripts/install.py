#!/usr/bin/env python3
"""Install canonical harness files without replacing unrelated configuration."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import sys
import tempfile
import time
import tomllib
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def credentials():
    values = {}
    path = ROOT / 'mcp/.env'
    if path.exists():
        for number, line in enumerate(path.read_text().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, sep, value = line.partition('=')
            if not sep or not re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
                raise ValueError(f'Invalid dotenv assignment on line {number}')
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in '\"\'':
                value = value[1:-1]
            values[key] = value
    values.update(os.environ)
    return values


def read(path):
    if path.is_symlink():
        raise ValueError(f'Refusing to replace symlink: {path}')
    return path.read_text() if path.exists() else ''


def block(old, content, comment):
    begin, end = (f'{comment} BEGIN AI-HARNESS', f'{comment} END AI-HARNESS')
    if comment == '<!--':
        begin += ' -->'
        end += ' -->'
    replacement = begin + '\n' + content.rstrip() + '\n' + end
    if begin in old or end in old:
        if old.count(begin) != 1 or old.count(end) != 1 or old.index(begin) > old.index(end):
            raise ValueError('Invalid harness block markers')
        start, finish = old.index(begin), old.index(end) + len(end)
        return old[:start] + replacement + old[finish:]
    return old + ('\n\n' if old else '') + replacement + '\n'


def atomic_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix='.ai-harness-')
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(value)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=['codex', 'claude', 'all'], default='all')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--home', type=Path, help='Alternate installation home (also isolates profile paths)')
    args = parser.parse_args()
    home = (args.home or Path.home()).expanduser().resolve()
    codex_dir = home / '.codex' if args.home else Path(os.environ.get('CODEX_HOME', home / '.codex')).expanduser().resolve()
    claude_dir = home / '.claude' if args.home else Path(os.environ.get('CLAUDE_CONFIG_DIR', home / '.claude')).expanduser().resolve()
    claude_json = home / '.claude.json' if args.home or not os.environ.get('CLAUDE_CONFIG_DIR') else claude_dir / '.claude.json'
    state_path = home / '.local/state/ai-harness/install.json'
    state = json.loads(read(state_path) or '{}')
    changes = []
    preserved_conflicts = []

    def plan(path, new):
        old = read(path)
        if old != new:
            changes.append((path, old, new, path.exists()))

    def plan_skills(skill_root, previous):
        """Copy vendored skill files while refusing unmanaged destination files."""
        current = dict(previous)
        for source_dir in sorted(p for p in skill_root.iterdir() if p.is_dir()):
            if not (source_dir / 'SKILL.md').is_file():
                raise ValueError(f'Skill directory has no SKILL.md: {source_dir.name}')
            destination_dir = skill_root_target / source_dir.name
            for source_file in sorted(p for p in source_dir.rglob('*') if p.is_file()):
                relative = source_file.relative_to(source_dir).as_posix()
                destination = destination_dir / relative
                source_hash = hashlib.sha256(source_file.read_bytes()).hexdigest()
                previous_hash = previous.get(str(destination))
                if destination.exists() and destination.is_symlink():
                    raise ValueError(f'Refusing to replace skill symlink: {destination}')
                if destination.exists() and previous_hash is None:
                    raise ValueError(f'Unmanaged skill file exists: {destination}; resolve it before installing')
                if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != previous_hash:
                    raise ValueError(f'Installed skill was changed externally: {destination}; resolve it before installing')
                if not destination.exists() or destination.read_bytes() != source_file.read_bytes():
                    plan(destination, source_file.read_text())
                current[str(destination)] = source_hash
        return current

    catalog = json.loads((ROOT / 'mcp/servers.json').read_text())
    if catalog['version'] != 1:
        raise ValueError('Unsupported catalog version')
    env = credentials()
    selected = {}
    for name, server in catalog['servers'].items():
        if not re.fullmatch(r'[a-z][a-z0-9_-]*', name) or server['transport'] != 'streamable-http':
            raise ValueError('Unsupported server name or transport')
        url = server.get('url') or env.get(server.get('url_env', ''))
        parsed = urlsplit(url or '')
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f'{name}: a valid HTTPS endpoint without credentials is required')
        if server['auth']['type'] == 'bearer':
            token = env.get(server['auth']['token_env'], '')
            if not token or any(c in token for c in '\r\n'):
                raise ValueError(f'{name}: missing or invalid token environment variable')
        elif server['auth']['type'] != 'oauth':
            raise ValueError(f'{name}: unsupported authentication type')
        selected[name] = (server, url)

    for vendor_name in ('superpowers', 'mattpocock'):
        vendor = ROOT / 'vendor' / vendor_name
        source = json.loads((vendor / 'source.json').read_text())
        for relative, expected in source['sha256'].items():
            path = (vendor / relative).resolve()
            if not path.is_relative_to(vendor.resolve()):
                raise ValueError(f'Invalid {vendor_name} source path')
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError(f'{vendor_name} source verification failed: {relative}')

    instructions = '\n\n'.join(
        f'Source: `{ROOT / relative}`\n\n{(ROOT / relative).read_text().strip()}'
        for relative in ('instructions/global.md', 'instructions/security.md', 'instructions/planning.md')
    )
    instructions += f'\n\nResolve all source-relative references against their source file above.\nBefore infrastructure work read `{ROOT / "context/infrastructure.md"}`.\nBefore MCP work read `{ROOT / "mcp/README.md"}`.\n'

    for agent in ('codex', 'claude'):
        if args.agent not in (agent, 'all'):
            continue
        directory = codex_dir if agent == 'codex' else claude_dir
        instruction_path = directory / ('AGENTS.md' if agent == 'codex' else 'CLAUDE.md')
        if agent == 'codex' and (directory / 'AGENTS.override.md').exists() and (directory / 'AGENTS.override.md').read_text().strip():
            raise ValueError('Codex AGENTS.override.md would shadow the harness; resolve it first')
        plan(instruction_path, block(read(instruction_path), instructions, '<!--'))
        config = codex_dir / 'config.toml' if agent == 'codex' else claude_json
        old = read(config)
        parsed_config = (tomllib.loads(old) if agent == 'codex' else json.loads(old or '{}'))
        key = 'mcp_servers' if agent == 'codex' else 'mcpServers'
        existing = parsed_config.get(key, {})
        previous = state.get(str(config), {})
        definitions = dict(previous)
        for name, (server, url) in selected.items():
            entry = {'url': url}
            if agent == 'claude':
                entry['type'] = 'http'
            if server['auth']['type'] == 'bearer':
                if agent == 'codex':
                    entry['bearer_token_env_var'] = server['auth']['token_env']
                else:
                    entry['headersHelper'] = shlex.join([sys.executable, str(ROOT / 'scripts/mcp_headers.py'), server['auth']['token_env']])
            if name in existing and name not in previous:
                # A manually configured server may contain credentials. Preserve it
                # verbatim rather than adopting, rewriting, or storing its secret.
                preserved_conflicts.append(f'{agent}/{name}')
                continue
            definitions[name] = entry
        for name in definitions:
            if name in existing and existing[name] != previous.get(name):
                raise ValueError(f'Unmanaged or externally changed MCP entry: {agent}/{name}; resolve it before installing')
        if agent == 'codex':
            content = ''
            for name, entry in definitions.items():
                content += f'\n[mcp_servers.{name}]\n'
                content += ''.join(f'{k} = {json.dumps(v)}\n' for k, v in entry.items())
            new = block(old, content, '#')
            tomllib.loads(new)
        else:
            parsed_config.setdefault(key, {}).update(definitions)
            new = json.dumps(parsed_config, indent=2) + '\n'
        plan(config, new)
        state[str(config)] = definitions
        skill_root_target = directory / 'skills'
        source_skill_roots = [ROOT / 'vendor/superpowers/skills', ROOT / 'vendor/mattpocock/skills']
        previous_skills = state.get(f'skills:{skill_root_target}', {})
        managed_skills = dict(previous_skills)
        for source_root in source_skill_roots:
            managed_skills = plan_skills(source_root, managed_skills)
        state[f'skills:{skill_root_target}'] = managed_skills
    plan(state_path, json.dumps(state, indent=2) + '\n')
    for path, _, _, _ in changes:
        print(f'{"Would update" if args.dry_run else "Update"}: {path}')
    if not args.dry_run:
        # Recheck the complete plan before the first write. Close clients during installation.
        for path, old, _, existed in changes:
            if path.exists() != existed or read(path) != old:
                raise ValueError('Configuration changed during planning; retry with clients closed')
        stamp = str(time.time_ns())
        for index, (path, old, new, existed) in enumerate(changes):
            if existed:
                backup = home / '.local/state/ai-harness/backups' / stamp / f'{index}-{path.name}'
                atomic_write(backup, old)
                print(f'Backup: {backup}')
            atomic_write(path, new)
    print('No changes needed.' if not changes else 'Plan complete.' if args.dry_run else 'Installation complete. Restart your clients and authenticate OAuth servers.')
    for entry in preserved_conflicts:
        print(f'Preserved existing unmanaged MCP entry: {entry}', file=sys.stderr)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # Do not echo parser errors: malformed private configuration can contain secrets.
        print(str(exc) if type(exc) is ValueError else f'Installation failed ({type(exc).__name__}); inspect local files privately.', file=sys.stderr)
        sys.exit(1)
