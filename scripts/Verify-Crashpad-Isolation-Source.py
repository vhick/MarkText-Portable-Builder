#!/usr/bin/env python3
"""Verify BOTH explicit MarkText crash reporter calls are disabled."""
from __future__ import annotations
import argparse
from pathlib import Path
import re

INDEX = 'packages/desktop/src/main/index.ts'
HANDLER = 'packages/desktop/src/main/exceptionHandler.ts'

# A code-line anchor avoids matching explanatory comments mentioning the call.
REAL_CALL = re.compile(r'(?m)^[ \t]*crashReporter\s*\.\s*start\s*\(')
REPORTER_IMPORT = re.compile(r"(?m)^\s*import\s*\{[^}\n]*\bcrashReporter\b[^}\n]*\}\s*from\s*['\"]electron")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    root = Path(args.root)
    index = (root / INDEX).read_text(encoding='utf-8-sig')
    handler = (root / HANDLER).read_text(encoding='utf-8-sig')
    checks = {
        'existing v1.1 portable patch remains': 'MARKTEXT_PORTABLE_CRASHPAD_V11' in index,
        'index.ts isolation patch present once': index.count('MARKTEXT_CRASHPAD_ISOLATION_V12') == 1,
        'exceptionHandler.ts early-start patch present once': handler.count('MARKTEXT_EXCEPTION_CRASHPAD_ISOLATION_V123') == 1,
        'index.ts explicit crashReporter.start removed': REAL_CALL.search(index) is None,
        'exceptionHandler.ts explicit crashReporter.start removed': REAL_CALL.search(handler) is None,
        'index.ts crashReporter import removed': REPORTER_IMPORT.search(index) is None,
        'exceptionHandler.ts crashReporter import removed': REPORTER_IMPORT.search(handler) is None,
        'portable path diagnostic retained': "'portable-paths.txt'" in index,
        'portable crashDumps override retained': "app.setPath('crashDumps', portableCrashpad)" in index,
        'JS main exception reporting retained': "process.on('uncaughtException'" in index,
        'exceptionHandler JS error reporting retained': "process.on('uncaughtException'" in handler,
        'renderer error listener retained': "ipcMain.on('mt::handle-renderer-error'" in handler,
        'early exception handler still installed': 'setupExceptionHandler()' in index,
    }
    other=[]
    for p in (root/'packages/desktop/src/main').rglob('*'):
        if not p.is_file() or p.suffix.lower() not in {'.js', '.ts', '.mjs', '.cjs', '.tsx'}:
            continue
        code=p.read_text(encoding='utf-8-sig', errors='replace')
        for m in REAL_CALL.finditer(code):
            other.append(f'{p.relative_to(root)}:{code.count(chr(10), 0, m.start())+1}')
    checks['no remaining explicit start calls under main source'] = not other
    report = 'MARKTEXT CRASHPAD ISOLATION v1.2.3 — SOURCE CHECK\n\n' + '\n'.join(
        f"{'PASS' if value else 'FAIL'}: {name}" for name, value in checks.items()
    )
    if other:
        report += '\nRemaining calls: ' + '; '.join(other)
    report += '\n\nThis is a SOURCE check, not proof of zero AppData writes. Test the EXE on Windows.\n'
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding='utf-8')
    print(report)
    if not all(checks.values()):
        raise SystemExit('MarkText isolation verification FAILED')


if __name__ == '__main__':
    main()
