# Matt Pocock skills

Upstream: [mattpocock/skills](https://github.com/mattpocock/skills).

This directory vendors the skills under the engineering, productivity, miscellaneous, and in-progress categories. `source.json` records the upstream commit and SHA-256 hashes. The MIT license is included.

The harness installer copies each skill and its supporting files into the native Codex and Claude Code skill directories. The vendored files are the source of truth, so do not install a second independently managed copy with `npx skills@latest add mattpocock/skills` on the same machine.

`setup-matt-pocock-skills` is included. Run it once per target project when you want to configure issue tracking, labels, and documentation locations. Review each skill before granting it access to external systems; the catalog includes in-progress skills as well as stable engineering and productivity skills.
