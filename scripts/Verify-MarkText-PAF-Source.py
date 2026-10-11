#!/usr/bin/env python3
"""Fail-closed check for the *already tested* MarkText portable + Crashpad patches.

The PAF-specific profile is supplied via MarkText's officially documented
--user-data-dir flag, rather than through another source-level path rewrite.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re

ROOT = Path('packages/desktop/src/main')
CALL = re.compile(r'(?m)^[ \t]*crashReporter\s*\.\s*start\s*\(')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    root = Path(args.root)
    index_path = root / ROOT / 'index.ts'
    handler_path = root / ROOT / 'exceptionHandler.ts'
    if not index_path.is_file() or not handler_path.is_file():
        raise SystemExit('FAIL: MarkText startup files were moved. Inspect upstream.')
    index = index_path.read_text(encoding='utf-8-sig')
    handler = handler_path.read_text(encoding='utf-8-sig')
    main_dir = root / ROOT
    remaining = []
    for p in main_dir.rglob('*'):
        if p.suffix.lower() in ('.ts', '.js', '.tsx', '.mjs', '.cjs') and p.is_file():
            txt = p.read_text(encoding='utf-8-sig', errors='replace')
            if CALL.search(txt):
                remaining.append(str(p.relative_to(root)))
    checks = {
        'v1.1 portable storage patch present': 'MARKTEXT_PORTABLE_CRASHPAD_V11' in index,
        'uses MarkText CLI --user-data-dir': "args['--user-data-dir']" in index,
        'CLI argument handed to setupEnvironment': 'setupEnvironment(args as Record<string, unknown>)' in index,
        'CLI-selected profile has priority': 'explicitProfile || (fs.existsSync(adjacentProfile) ? adjacentProfile : null)' in index,
        'Electron userData redirected': "app.setPath('userData', portableProfile)" in index,
        'Electron sessionData redirected': "app.setPath('sessionData', portableProfile)" in index,
        'Electron logs redirected': "app.setPath('logs', portableLogs)" in index,
        'Electron Crashpad path redirected': "app.setPath('crashDumps', portableCrashpad)" in index,
        'runtime path report retained': "'portable-paths.txt'" in index,
        'index.ts reporter disabled': 'MARKTEXT_CRASHPAD_ISOLATION_V12' in index,
        'exceptionHandler.ts reporter disabled': 'MARKTEXT_EXCEPTION_CRASHPAD_ISOLATION_V123' in handler,
        'JS exception handling retained': "process.on('uncaughtException'" in handler,
        'no explicit crashReporter.start calls under main': not remaining,
    }
    report = 'MARKTEXT PAF-COMPATIBLE SOURCE CHECK\n' + '\n'.join(
        ('PASS' if ok else 'FAIL') + ': ' + label for label, ok in checks.items()
    ) + '\n'
    if remaining:
        report += '\nUnexpected reporter calls: ' + ', '.join(remaining) + '\n'
    report += ('\nRequired PortableApps launcher argument:\n'
               '  --user-data-dir "%PAL:DataDir%\\marktext-user-data"\n'
               'The PAF builder DOES NOT create App\\MarkText\\marktext-user-data.\n'
               'Runtime verification on Windows is still required.\n')
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(report, encoding='utf-8')
    print(report)
    if not all(checks.values()):
        raise SystemExit('FAIL CLOSED: source no longer matches validated MarkText portable code')


if __name__ == '__main__':
    main()
