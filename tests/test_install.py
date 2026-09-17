import json
import os
from pathlib import Path
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def run_install(self, *args, extra_env=None, success=True):
        env = {k: v for k, v in os.environ.items() if not k.startswith('COOLIFY_')}
        env.update({'COOLIFY_API_TOKEN': 'synthetic-test-secret', 'COOLIFY_MCP_URL': 'https://coolify.example/mcp'})
        env.update(extra_env or {})
        result = subprocess.run([str(ROOT / 'install.sh'), '--home', str(self.home), *args], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        return result

    def test_dry_run_and_idempotence(self):
        self.run_install('--dry-run')
        self.assertEqual(list(self.home.iterdir()), [])
        self.run_install()
        files = {p: p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
        self.run_install()
        self.assertEqual(files, {p: p.read_bytes() for p in self.home.rglob('*') if p.is_file()})
        data = tomllib.loads((self.home / '.codex/config.toml').read_text())
        self.assertEqual(set(data['mcp_servers']), {'notion', 'coolify', 'context7', 'sentry'})
        self.assertIn(str(ROOT / 'instructions/security.md'), (self.home / '.claude/CLAUDE.md').read_text())
        for path in (self.home / '.claude/CLAUDE.md', self.home / '.codex/AGENTS.md'):
            installed = path.read_text()
            self.assertIn(str(ROOT / 'instructions/planning.md'), installed)
            self.assertIn('vendor/superpowers/skills/brainstorming/SKILL.md', installed)
            self.assertIn('vendor/superpowers/skills/writing-plans/SKILL.md', installed)
        codex_skills = {p.name for p in (self.home / '.codex/skills').iterdir() if p.is_dir()}
        claude_skills = {p.name for p in (self.home / '.claude/skills').iterdir() if p.is_dir()}
        self.assertEqual(codex_skills, claude_skills)
        self.assertIn('setup-matt-pocock-skills', codex_skills)
        self.assertIn('brainstorming', codex_skills)
        self.assertGreaterEqual(len(codex_skills), 39)

    def test_preserves_unrelated_and_backs_up(self):
        directory = self.home / '.codex'
        directory.mkdir()
        (directory / 'AGENTS.md').write_text('Existing instructions\n')
        (directory / 'config.toml').write_text('model = "custom"\n[mcp_servers.other]\nurl = "https://example.com/mcp"\n')
        (self.home / '.claude.json').write_text('{"preferences": {"keep": true}}')
        self.run_install()
        data = tomllib.loads((directory / 'config.toml').read_text())
        self.assertEqual(data['model'], 'custom')
        self.assertIn('other', data['mcp_servers'])
        self.assertTrue((directory / 'AGENTS.md').read_text().startswith('Existing instructions'))
        self.assertTrue(json.loads((self.home / '.claude.json').read_text())['preferences']['keep'])
        self.assertTrue(list((self.home / '.local/state/ai-harness/backups').rglob('*AGENTS.md')))

    def test_conflict_preflight_no_writes(self):
        (self.home / '.claude.json').write_text('{"mcpServers": {"notion": {"url": "https://other.example/mcp"}}}')
        self.run_install()
        self.assertEqual(json.loads((self.home / '.claude.json').read_text())['mcpServers']['notion']['url'], 'https://other.example/mcp')
        self.assertIn('coolify', json.loads((self.home / '.claude.json').read_text())['mcpServers'])

    def test_coolify_no_secret_in_config(self):
        self.run_install(extra_env={'COOLIFY_API_TOKEN': 'synthetic-test-secret', 'COOLIFY_MCP_URL': 'https://coolify.example/mcp'})
        for p in self.home.rglob('*'):
            if p.is_file():
                self.assertNotIn('synthetic-test-secret', p.read_text())
        data = tomllib.loads((self.home / '.codex/config.toml').read_text())
        self.assertEqual(data['mcp_servers']['coolify']['bearer_token_env_var'], 'COOLIFY_API_TOKEN')
        self.run_install()
        self.assertIn('coolify', tomllib.loads((self.home / '.codex/config.toml').read_text())['mcp_servers'])

    def test_missing_private_configuration_and_override(self):
        self.run_install(extra_env={'COOLIFY_MCP_URL': '', 'COOLIFY_API_TOKEN': ''}, success=False)
        self.assertEqual(list(self.home.iterdir()), [])
        (self.home / '.codex').mkdir()
        (self.home / '.codex/AGENTS.override.md').write_text('Override')
        self.run_install(success=False)
        self.assertFalse((self.home / '.claude').exists())

    def test_external_change_and_symlink_rejected(self):
        self.run_install('--agent', 'claude')
        path = self.home / '.claude.json'
        data = json.loads(path.read_text())
        data['mcpServers']['notion']['url'] = 'https://changed.example/mcp'
        path.write_text(json.dumps(data))
        self.run_install('--agent', 'claude', success=False)
        target = self.home / 'existing'
        target.write_text('preserve me')
        (self.home / '.codex').mkdir()
        (self.home / '.codex/AGENTS.md').symlink_to(target)
        self.run_install('--agent', 'codex', success=False)
        self.assertEqual(target.read_text(), 'preserve me')


if __name__ == '__main__':
    unittest.main()
