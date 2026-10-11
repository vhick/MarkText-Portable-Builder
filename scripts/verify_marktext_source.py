#!/usr/bin/env python3
"""Source-level checks; not a substitute for the Windows runtime test."""
import argparse
from pathlib import Path

P=Path('packages/desktop/src/main/index.ts')

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--root',required=True)
    a.add_argument('--output',required=True)
    arg=a.parse_args()
    p=Path(arg.root)/P
    t=p.read_text(encoding='utf-8')
    checks = {
      'marktext portable marker': 'MARKTEXT_PORTABLE_CRASHPAD_V1' in t,
      'portable profile source': "const portableProfile = app.getPath('userData')" in t,
      'crash dump redirect': "app.setPath('crashDumps', portableCrashpad)" in t,
      'session data redirect': "app.setPath('sessionData', portableProfile)" in t,
      'logs redirect': "app.setPath('logs', portableLogs)" in t,
      'crash reporter is still enabled': 'crashReporter.start({' in t,
      'source patch runs after setupEnvironment': t.find('setupEnvironment(args as Record<string, unknown>)') < t.find('MARKTEXT_PORTABLE_CRASHPAD_V1'),
      'source patch runs before crashReporter': t.find('MARKTEXT_PORTABLE_CRASHPAD_V1') < t.find('crashReporter.start({'),
    }
    lines=['MarkText Portable Builder — source verification','This verifies patch structure, NOT actual Windows runtime behavior.','']
    lines += [f'{"PASS" if v else "FAIL"}: {k}' for k,v in checks.items()]
    out=Path(arg.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(out.read_text(encoding='utf-8'))
    if not all(checks.values()): raise SystemExit('Source verification FAILED')

if __name__=='__main__':main()
