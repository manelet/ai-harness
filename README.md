# AI harness

A portable source of truth for personal agent instructions, private infrastructure context, and MCP definitions. Edit this repository, then run the installer on each computer.

## Install

Requires macOS or Linux (or WSL), Python 3.11+, and the clients you want to use installed separately. Keep the checkout at a stable path. Close clients before installing to avoid concurrent configuration writes. Before running the installer, configure `COOLIFY_MCP_URL` and `COOLIFY_API_TOKEN` as described below; all four MCP servers are always included.

```sh
git clone <YOUR_REPOSITORY_URL> ~/ai-harness
cd ~/ai-harness
./install.sh --dry-run
./install.sh
```

The default installs user-level instructions and the Notion, Coolify, Context7, and Sentry MCP definitions for both Codex and Claude Code. To select one client:

```sh
./install.sh --agent codex
./install.sh --agent claude
```

The installer does not install clients, select models, contact servers, or complete OAuth. Restart the clients after installation. In Codex, authenticate each server with `codex mcp login notion`, `codex mcp login context7`, and `codex mcp login sentry`. In Claude Code, use `/mcp` to authenticate. Account permissions and available tools still need verification after login.

This configures coding clients, not arbitrary chat websites. Model selection remains in each client; another client requires another adapter.

## Private configuration on each computer

Private context, credentials, and OAuth sessions do not travel through Git. Transfer them separately using a trusted channel or secret manager; local SSH key paths may differ between computers.

If absent, create `context/infrastructure.local.md` from `context/infrastructure.example.md` and complete it locally. Keep SSH settings and keys under `~/.ssh/`. Never overwrite an existing local file with the template.

For Coolify, create `mcp/.env` from `mcp/.env.example` if absent, restrict its permissions (`chmod 600 mcp/.env`), and fill in the HTTPS endpoint and a dedicated read-only API token. Alternatively, provide those variables through your environment or secret manager.

```sh
./install.sh --dry-run
./install.sh
```

Coolify is always installed. Missing or empty Coolify variables cause installation (including `--dry-run`) to fail before any writes.

Launch Codex through the helper when using `mcp/.env`, so the client receives its token environment variable:

```sh
~/ai-harness/scripts/run-agent codex
```

The helper preserves the current working directory and forwards client arguments. If your shell or secret manager already supplies `COOLIFY_API_TOKEN`, you can launch Codex normally. GUI clients must inherit that variable separately; the installer does not modify their launch environment.

Claude Code uses a dynamic header helper that reads the token locally when connecting; it can be launched normally. It requires a client version supporting `headersHelper`. The helper's stdout contains the authorization header for the client: never run it manually in a chat tool or log its output.

The dotenv reader accepts one `KEY=value` assignment per line, optional matching quotes, and full-line comments. Environment variables take precedence. It does not execute shell code, expand variables, support multiline values, or strip inline comments.

## Updates and portability

On each computer:

```sh
cd ~/ai-harness
git pull --ff-only
./install.sh
```

Rerun `./install.sh` when the Coolify URL or adapter configuration changes. Token rotation only requires updating the local secret and restarting/reconnecting the client. Rerun installation if you move the checkout: generated instructions and the Claude helper contain absolute paths resolved on that computer.

Generated instructions embed the shared global, security, and planning rules and point to context in the checkout. They are generated copies rather than directory symlinks so existing client files can be preserved. Rerun installation after changing shared instructions. Context files are read from the checkout on demand.

## What gets changed

| Client | User-level instructions | MCP configuration |
| --- | --- | --- |
| Codex | `~/.codex/AGENTS.md` | Managed block in `~/.codex/config.toml` |
| Claude Code | `~/.claude/CLAUDE.md` | Managed server entries in `~/.claude.json` |

Existing instruction text outside the marked harness block is preserved. Other MCP servers and client settings are preserved. Unmanaged MCP entries with colliding names are preserved verbatim and reported; externally changed managed MCP entries, target-file symlinks, malformed configuration, or a nonempty Codex `AGENTS.override.md` still stop installation. Resolve these explicitly rather than forcing an overwrite.

`CODEX_HOME` and `CLAUDE_CONFIG_DIR` are respected. `--home /some/test/directory` isolates all installation paths under that directory for testing and ignores these profile overrides.

Ownership metadata and backups live under `~/.local/state/ai-harness/`. Modified existing files receive a timestamped backup. Generated files and backups are written with owner-only permissions. Do not commit this state directory: backups can contain existing private client settings. Restore individual backups manually with clients closed, checking for newer changes first.

All configuration is validated before writes; individual writes are atomic. The complete installation is not a filesystem transaction: an I/O failure midway may require restoring a backup or rerunning. No automatic uninstall or pruning is provided; removed catalog entries remain installed until explicitly removed and their ownership metadata reconciled.

The installer does not alter approval, sandbox, or tool permission settings. Coolify read-only access must be enforced through the actual token permissions; catalog policy is not a permission boundary.

## Repository layout

- `instructions/`: canonical global and security rules.
- `context/`: public procedures and ignored private infrastructure context.
- `mcp/servers.json`: canonical MCP definitions; see `mcp/README.md`.
- `scripts/install.py`: Codex and Claude Code adapters and installation logic.
- `scripts/run-agent`: client launcher with local MCP variables.
- `scripts/vps`: read-only SSH diagnostics for the documented VPS.
- `AGENTS.md`: instructions for working on this repository.

The installer installs instructions, MCP definitions, the Superpowers planning subset, and all vendored Matt Pocock skills into the native skill directories of both clients. Other skills and operational scripts can be added as their workflows are defined. To support another client, add an adapter consuming the same source files and test it using an isolated home.

## VPS diagnostics

The read-only helper requires local environment configuration and never stores connection details:

```sh
export VPS_SSH_TARGET='personal-vps' # or root@host
export VPS_SSH_PORT=22
export VPS_SSH_IDENTITY="$HOME/.ssh/id_ed25519"
scripts/vps status
scripts/vps pocketbase
scripts/vps logs <container> 100
```

It enforces strict host-key checking, disables agent forwarding, and accepts only fixed diagnostic commands. It does not deploy, restart, modify, migrate, or delete anything. Do not paste sensitive application logs into public issues or commits.

## Planning with Superpowers

The harness includes the `brainstorming` and `writing-plans` skills from [obra/superpowers](https://github.com/obra/superpowers), pinned to the revision in `vendor/superpowers/source.json`. Upstream files and their MIT license are vendored; the installer verifies their hashes before making changes.

Run `./install.sh` and start a new client session to activate the planning instructions. The clients read the bundled skills through `instructions/planning.md`; no separate marketplace installation is needed. This is a planning subset, not the complete plugin or its automatic session hooks.

Example requests:

- “Use Superpowers to design this feature and write a spec.”
- “Create an implementation plan from this approved spec.”

Specs go in the target project's `docs/superpowers/specs/`; plans go in `docs/superpowers/plans/`, unless you request another location. Planning does not automatically start implementation, commits, or subagents. Integration boundaries and upstream workflow overrides are explicit in `instructions/planning.md`.

## Matt Pocock skills

The harness includes all skills under [mattpocock/skills](https://github.com/mattpocock/skills), including engineering, productivity, miscellaneous, and in-progress skills, pinned to `vendor/mattpocock/source.json`. The MIT license and source hashes are included. `setup-matt-pocock-skills` is included; run it once in each target project when you want to configure its issue tracker, labels, and documentation locations.

`install.sh` copies these skills and their supporting files into `~/.codex/skills/` and `~/.claude/skills/`. Existing unmanaged skill files, symlinks, or externally edited managed files cause a safe failure instead of an overwrite. Updating the harness updates only files it previously installed; removed upstream files are retained locally and are never pruned automatically.

The vendored copy is the source of truth. Do not use `npx skills@latest add mattpocock/skills` on the same machine unless you intentionally want a second, independently managed copy of these skills.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

Tests use temporary directories and synthetic credentials. They do not contact providers or modify real client configuration.

Adapter references: [Codex global instructions](https://developers.openai.com/codex/guides/agents-md), [Codex MCP](https://developers.openai.com/codex/mcp), [Claude Code memory](https://code.claude.com/docs/en/memory), and [Claude Code MCP](https://code.claude.com/docs/en/mcp). Formats checked on 2026-09-10.
