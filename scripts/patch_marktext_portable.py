#!/usr/bin/env python3
"""Fail-closed MarkText develop-branch crash directory patch.

Runs only against source checked out on GitHub's temporary Windows runner.
Does not alter the clean fork repository.
"""
from __future__ import annotations
import argparse
import pathlib
import re
import sys

MARKER = 'MARKTEXT_PORTABLE_CRASHPAD_V1'
TARGET = pathlib.Path('packages/desktop/src/main/index.ts')

INSERT = """// MARKTEXT_PORTABLE_CRASHPAD_V1
// MarkText's setupEnvironment() has already selected the normal or portable
// userData directory. Crashpad otherwise independently creates a folder in
// %APPDATA%\\marktext on Windows even when marktext-user-data is portable.
// Set the paths before Electron's ready event and before crashReporter.start().
if (process.platform === 'win32' && app.isPackaged) {
  const portableProfile = app.getPath('userData')
  const portableCrashpad = path.join(portableProfile, 'Crashpad')
  const portableLogs = path.join(portableProfile, 'logs')
  fs.mkdirSync(portableCrashpad, { recursive: true })
  fs.mkdirSync(portableLogs, { recursive: true })
  app.setPath('sessionData', portableProfile)
  app.setPath('crashDumps', portableCrashpad)
  app.setPath('logs', portableLogs)
}
"""

def patch(text: str) -> str:
    # Use LF for matching but preserve the original newline convention.
    newline = '\r\n' if '\r\n' in text else '\n'
    s = text.replace('\r\n', '\n')
    if MARKER in s:
        raise ValueError('Patch marker already exists; refusing duplicate patch')

    old_import = "import path from 'path'\n"
    if s.count(old_import) != 1:
        raise ValueError('Expected the single path import in src/main/index.ts; inspect upstream changes')
    if re.search(r"^import\s+fs\s+from\s+['\"](?:node:)?fs['\"]", s, flags=re.M):
        raise ValueError('Source now imports fs already: adjust patch manually instead of duplicating')
    s = s.replace(old_import, old_import + "import fs from 'fs'\n", 1)

    anchor = "const appEnvironment = setupEnvironment(args as Record<string, unknown>)"
    if s.count(anchor) != 1:
        raise ValueError('setupEnvironment anchor missing or repeated; inspect upstream changes')
    if s.count('crashReporter.start({') != 1:
        raise ValueError('crash reporter initialization changed; inspect upstream changes')
    if s.index(anchor) >= s.index('crashReporter.start({'):
        raise ValueError('Startup ordering changed: environment must precede crash reporter')
    s = s.replace(anchor, anchor + '\n\n' + INSERT, 1)
    return s.replace('\n', newline)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True)
    args=ap.parse_args()
    target=pathlib.Path(args.root)/TARGET
    if not target.is_file():
        raise SystemExit(f'ERROR: Expected MarkText develop source missing: {target}')
    try:
        source=target.read_text(encoding='utf-8-sig')
        result=patch(source)
        target.write_text(result,encoding='utf-8',newline='')
        print('PASS: MarkText Crashpad, logs, and session paths now follow portable userData')
    except (OSError, ValueError) as exc:
        raise SystemExit('FAILED CLOSED: '+str(exc))

if __name__=='__main__': main()
