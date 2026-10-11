#!/usr/bin/env python3
"""Static source verification for MarkText portable v1.1."""
import argparse
from pathlib import Path

TARGET=Path('packages/desktop/src/main/index.ts')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    text=(Path(a.root)/TARGET).read_text(encoding='utf-8')
    needle={
        'new v1.1 marker': 'MARKTEXT_PORTABLE_CRASHPAD_V11',
        'uses EXE directory for portable marker': "path.dirname(process.execPath), 'marktext-user-data'",
        'respects explicit --user-data-dir': "args['--user-data-dir']",
        'sets Electron userData': "app.setPath('userData', portableProfile)",
        'sets Electron sessionData': "app.setPath('sessionData', portableProfile)",
        'sets Electron crashDumps': "app.setPath('crashDumps', portableCrashpad)",
        'sets Electron logs': "app.setPath('logs', portableLogs)",
        'writes actual Electron runtime path report': "'portable-paths.txt'",
        'keeps crash reporter enabled': 'crashReporter.start({',
    }
    checks={key:val in text for key,val in needle.items()}
    checks['redirect happens after setupEnvironment']=(text.find('setupEnvironment(args as Record<string, unknown>)') < text.find('MARKTEXT_PORTABLE_CRASHPAD_V11'))
    checks['redirect happens before crashReporter.start']=(text.find('MARKTEXT_PORTABLE_CRASHPAD_V11') < text.find('crashReporter.start({'))
    report='MarkText portable v1.1 — source-only verification\n' + '\n'.join(('PASS' if v else 'FAIL')+': '+k for k,v in checks.items())+'\n'
    dest=Path(a.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(report,encoding='utf-8')
    print(report)
    if not all(checks.values()):
        raise SystemExit('Source verification FAILED')

if __name__=='__main__':
    main()
