#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

roots=[Path('source_documents'), Path('languages'), Path('domains'), Path('core/communication/history')]
violations=[]
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob('*.md'):
        if p.name == 'README.md':
            continue
        text=p.read_text(errors='ignore')
        if not text.startswith('---\n'):
            violations.append(f"missing frontmatter: {p}")
            continue
        if "# Objective" not in text:
            violations.append(f"missing objective section: {p}")

if violations:
    print('agent-native wrapper validation failed:')
    for v in violations:
        print('-', v)
    raise SystemExit(1)

print('agent-native wrapper validation passed')
PY
