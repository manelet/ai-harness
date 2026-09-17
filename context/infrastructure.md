# Infrastructure

Private operational details live in `infrastructure.local.md` in this directory. Read that file and `../instructions/security.md` before remote work. If the local file is missing or required facts are unknown, ask the owner; never infer a destination from examples.

The local file is ignored by Git. On a new machine, copy `infrastructure.example.md` to `infrastructure.local.md` and complete it privately. Keep credentials outside this repository; prefer SSH aliases configured in `~/.ssh/config`.

Do not copy private connection details into tracked files, commits, or public output. Never force-add ignored local context.

## Operating procedure

1. Confirm the requested scope and verify server identity, effective SSH settings, user, paths, and current service state using read-only checks.
2. Identify the actual service management and storage configuration before changing it. Use the established management workflow; do not bypass it or modify unrelated services.
3. Prepare a minimal change, a recovery procedure, and appropriate backups. Obtain specific authorization for dangerous operations under the security instructions.
4. Execute in steps, stop on unexpected results, and verify service health afterward.

For an initial read-only check, use `scripts/vps status` and `scripts/vps pocketbase` after setting `VPS_SSH_TARGET`, `VPS_SSH_PORT`, and `VPS_SSH_IDENTITY` locally. The helper contains no connection details and performs no changes.

## Data migrations using rsync

- Confirm source and destination hosts, absolute paths, transfer direction, symlinks, and trailing-slash behavior. Never guess service data directories or volume mounts.
- Inspect a dry run with itemized changes before the actual transfer. Do not treat a dry run as a backup or proof of database consistency.
- Do not add `--delete`, overwrite existing persistent data, or remove source data without explicit authorization for the exact operation.
- Establish a verified backup and an application-appropriate consistency procedure before copying live database files. Coordinate any required write pause or service downtime with the owner.
- Verify the transferred data and application health before cutover. Keep the source and rollback copy until their removal is explicitly authorized.

Permissions, isolation, and tested backups must enforce operational limits; instructions alone cannot guarantee safety.
