#!/usr/bin/env python3
"""MarkText develop, Windows portable Electron path fix, v1.1.

Only edits the transient GitHub Actions checkout of the clean fork.
Fails closed if current upstream startup structure no longer matches.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

MARKER = 'MARKTEXT_PORTABLE_CRASHPAD_V11'
TARGET = Path('packages/desktop/src/main/index.ts')
INSERT = r'''// MARKTEXT_PORTABLE_CRASHPAD_V11
// MarkText's own configuration/profile resolver is distinct from Electron's
// built-in `userData` value. The previous patch used app.getPath('userData')
// as its input, which can still point at %APPDATA%\\marktext.
//
// For a ZIP build, the existing marktext-user-data folder beside marktext.exe
// is the trusted portable-mode marker. Respect an explicit CLI profile path.
// Do not redirect installed/non-portable builds without one of those markers.
if (process.platform === 'win32' && app.isPackaged) {
  const explicitProfileArg = args['--user-data-dir']
  const adjacentProfile = path.join(path.dirname(process.execPath), 'marktext-user-data')
  const explicitProfile = typeof explicitProfileArg === 'string' && explicitProfileArg.trim()
    ? path.resolve(explicitProfileArg)
    : null
  const portableProfile = explicitProfile || (fs.existsSync(adjacentProfile) ? adjacentProfile : null)

  if (portableProfile) {
    const portableCrashpad = path.join(portableProfile, 'Crashpad')
    const portableLogs = path.join(portableProfile, 'logs')
    fs.mkdirSync(portableProfile, { recursive: true })
    fs.mkdirSync(portableCrashpad, { recursive: true })
    fs.mkdirSync(portableLogs, { recursive: true })

    // All four Electron paths must be pinned before app.ready and before
    // crashReporter.start(), independent of MarkText's own preferences code.
    app.setPath('userData', portableProfile)
    app.setPath('sessionData', portableProfile)
    app.setPath('logs', portableLogs)
    app.setPath('crashDumps', portableCrashpad)

    // This file is intentionally stored in the portable profile. It records
    // the *actual* Electron paths at runtime and contains no preferences.
    const portablePathReport = [
      'MarkText v1.1 portable path report',
      `time=${new Date().toISOString()}`,
      `exe=${process.execPath}`,
      `userData=${app.getPath('userData')}`,
      `sessionData=${app.getPath('sessionData')}`,
      `logs=${app.getPath('logs')}`,
      `crashDumps=${app.getPath('crashDumps')}`,
      `marktextLogPath=${appEnvironment.paths.logPath}`,
      '',
    ].join('\n')
    fs.writeFileSync(path.join(portableProfile, 'portable-paths.txt'), portablePathReport, 'utf8')
  }
}
'''


def patch(text: str) -> str:
    newline = '\r\n' if '\r\n' in text else '\n'
    src = text.replace('\r\n', '\n')
    if MARKER in src:
        raise ValueError('v1.1 marker already present; refusing double patch')
    if 'MARKTEXT_PORTABLE_CRASHPAD_V1\n' in src:
        raise ValueError('v1.0 patch found in checkout. Build from CLEAN MarkText fork, not a patched tree.')
    old_import = "import path from 'path'\n"
    if src.count(old_import) != 1:
        raise ValueError('Expected one path import in main/index.ts; inspect upstream')
    if re.search(r"^import\s+fs\s+from\s+['\"](?:node:)?fs['\"]",src,flags=re.M):
        raise ValueError('Unexpected existing fs import; adapt patch to current upstream')
    src = src.replace(old_import,old_import+"import fs from 'fs'\n",1)
    anchor = 'const appEnvironment = setupEnvironment(args as Record<string, unknown>)'
    crash_anchor = 'crashReporter.start({'
    if src.count(anchor) != 1 or src.count(crash_anchor) != 1:
        raise ValueError('MarkText startup source has changed; exact anchor not found once')
    if src.index(anchor) >= src.index(crash_anchor):
        raise ValueError('Crashpad starts before environment setup: unsafe to patch')
    src = src.replace(anchor,anchor+'\n\n'+INSERT,1)
    return src.replace('\n',newline)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    args=parser.parse_args()
    target=Path(args.root)/TARGET
    if not target.is_file():
        raise SystemExit(f'MarkText source not found: {target}')
    try:
        original=target.read_text(encoding='utf-8-sig')
        target.write_text(patch(original),encoding='utf-8',newline='')
    except (OSError,ValueError) as exc:
        raise SystemExit('FAILED CLOSED: '+str(exc))
    print('PASS: v1.1 now explicitly pins Electron userData, sessionData, logs and Crashpad to the actual portable folder')

if __name__=='__main__':
    main()
