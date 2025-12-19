# Demo pipeline

This repo contains a small, deterministic "golden run" to generate demo outputs
for **Goal 1 Stage B** (enumeration / grounding).

The demo produces JSON artifacts under `out/` (gitignored) which can be used by
backend/frontend without requiring solver execution in the request path.

## Generate demo artifacts

From repo root:

```bash
venv/bin/python scripts/demo_goal1_stageb.py
```

Outputs:
- `out/demo_goal1_stageb_fwd.json`
- `out/demo_goal1_stageb_def.json`

Defaults:
- `--fwd-combo-ids 22`
- `--def-combo-ids 31`

You can override combo IDs:

```bash
venv/bin/python scripts/demo_goal1_stageb.py --fwd-combo-ids 22 --def-combo-ids 31
```

