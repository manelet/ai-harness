# Superpowers planning subset

Upstream: [obra/superpowers](https://github.com/obra/superpowers).

This directory vendors unmodified `brainstorming` and `writing-plans` skill directories plus the MIT license. `source.json` records the exact commit and SHA-256 hashes of the upstream files. The checkout is self-contained: installing on another computer does not download a moving branch or require a separate plugin installation.

The harness integration policy is in `../../instructions/planning.md`. It deliberately scopes these skills to planning/specification and explains the execution handoff differences. Upstream skills may refer to execution skills outside this subset; those are not installed. Bundled companion scripts are not executed by the installer.

`install.sh` embeds the planning policy in both clients' global instructions, with an absolute source path. Agents read these canonical skill files from the harness on demand. This is an instruction-based integration, not the complete Superpowers plugin: no session hooks, slash commands, or execution framework are installed. Avoid installing the full plugin alongside this subset unless you intentionally want its broader workflow.

To update, choose and review an upstream commit, download the same skill directories into a temporary location using the skill-installer helper, review the diff and referenced resources, then update this directory, its license, and `source.json` together. Never edit upstream files to customize behavior; put overrides in the harness planning policy. Run the tests and rerun `install.sh` on each computer.
