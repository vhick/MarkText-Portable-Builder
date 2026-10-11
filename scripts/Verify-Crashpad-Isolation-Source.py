#!/usr/bin/env python3
"""Check v1.2 Crashpad-isolation experimental source state."""
import argparse
import re
from pathlib import Path

MARKER = 'MARKTEXT_CRASHPAD_ISOLATION_V12'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--output',required=True)
    args = p.parse_args()
    source=Path(args.root)
    target=source/'packages/desktop/src/main/index.ts'
    text=target.read_text(encoding='utf-8')
    checks={
        'v1.1 portable-path patch still present': 'MARKTEXT_PORTABLE_CRASHPAD_V11' in text,
        'v1.2 isolation marker present once': text.count(MARKER)==1,
        'explicit crash reporter call absent in entry point': re.search(r'(?m)^[ \t]*crashReporter\s*\.\s*start\s*\(',text) is None,
        'crashReporter import removed': re.search(r'import\s*\{[^}]*\bcrashReporter\b[^}]*\}\s*from\s*[\'\"]electron',text) is None,
        'Electron path report still enabled': "'portable-paths.txt'" in text,
        'Electron crash directory override still enabled': "app.setPath('crashDumps', portableCrashpad)" in text,
        'JS uncaught exception logging still enabled': "process.on('uncaughtException'" in text,
        'disabled-crash-reporter marker precedes window creation': text.find(MARKER)<text.find('appController.init()'),
    }
    # Fail closed if another explicit crashReporter.start has appeared elsewhere
    # in the main-process source. Ignore node_modules/generated code.
    other=[]
    main_dir=source/'packages/desktop/src/main'
    for f in main_dir.rglob('*'):
        if f == target or not f.is_file() or f.suffix.lower() not in {'.ts','.tsx','.js','.mjs','.cjs'}:
            continue
        try: content=f.read_text(encoding='utf-8')
        except (OSError,UnicodeError): continue
        if re.search(r'(?m)^[ \t]*crashReporter\s*\.\s*start\s*\(',content):
            other.append(str(f.relative_to(source)))
    checks['no other obvious explicit crash reporter start in main source']=not other
    lines=['MARKTEXT CRASHPAD ISOLATION v1.2 — SOURCE-ONLY CHECK','']
    lines += [('PASS' if ok else 'FAIL')+': '+k for k,ok in checks.items()]
    if other:
        lines.append('Other starts: '+', '.join(other))
    lines += ['', 'THIS IS AN EXPERIMENTAL BUILD, NOT PROOF OF ZERO APPDATA WRITES.',
              'Windows runtime comparison is required.', '']
    report='\n'.join(lines)
    output=Path(args.output); output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(report,encoding='utf-8')
    print(report)
    if not all(checks.values()): raise SystemExit('Isolation source verification FAILED')


if __name__=='__main__':main()
