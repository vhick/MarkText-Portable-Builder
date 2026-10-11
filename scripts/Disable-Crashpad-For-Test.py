#!/usr/bin/env python3
"""MarkText v1.2 test ONLY: suppress explicit crashReporter.start call.

Run *after* the existing v1.1 portable-path patch. This is a controlled
experiment, not a claim that Chromium/Electron cannot initialize Crashpad.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

TARGET = Path('packages/desktop/src/main/index.ts')
MARKER = 'MARKTEXT_CRASHPAD_ISOLATION_V12'

# Match the reporter call and verify each expected property. Blank lines are
# allowed, but unexpected options trigger a fail-closed error.
CALL = re.compile(
    r"(?ms)^[ \t]*crashReporter\.start\(\{[ \t]*\n"
    r"(?P<body>.*?)"
    r"^[ \t]*\}\)[ \t]*(?=\n|$)"
)
EXPECTED_OPTIONS = [
    r"companyName\s*:\s*''\s*,?",
    r"productName\s*:\s*'marktext'\s*,?",
    r"uploadToServer\s*:\s*false\s*,?\s*(?://.*)?",
    r"compress\s*:\s*true\s*,?",
]

IMPORT = "import { app, dialog, crashReporter } from 'electron'"
NEW_IMPORT = "import { app, dialog } from 'electron'"


def transform(source: str) -> str:
    newline = '\r\n' if '\r\n' in source else '\n'
    text = source.replace('\r\n', '\n')
    if MARKER in text:
        raise ValueError('Already patched with v1.2; do not apply twice')
    if 'MARKTEXT_PORTABLE_CRASHPAD_V11' not in text:
        raise ValueError('Expected v1.1 portable-path patch first; refusing unprotected test build')
    if text.count(IMPORT) != 1:
        raise ValueError('Electron import changed upstream; expected the inspected import once')
    found = list(CALL.finditer(text))
    if len(found) != 1:
        raise ValueError(f'Expected one MarkText crashReporter.start block; found {len(found)}')
    properties = [line.strip() for line in found[0].group('body').splitlines() if line.strip()]
    if len(properties) != len(EXPECTED_OPTIONS) or any(
        re.fullmatch(option, line) is None for option, line in zip(EXPECTED_OPTIONS, properties)
    ):
        raise ValueError('Crash reporter arguments changed upstream; refusing isolation patch')
    # Intentionally remove only the startup call. Keep MarkText's error logger.
    replacement = (
        '// ' + MARKER + '\n'
        '// Controlled portability test: native crash-report collection is DISABLED.\n'
        '// JavaScript exception logs remain enabled.\n'
        "log.info('Portable test build: explicit native crashReporter.start disabled')"
    )
    text = CALL.sub(lambda _m: replacement, text, count=1)
    text = text.replace(IMPORT, NEW_IMPORT, 1)
    if re.search(r'crashReporter\s*\.\s*start\s*\(', text):
        raise ValueError('Another explicit crashReporter.start call is present in main/index.ts')
    if text.count(MARKER) != 1:
        raise ValueError('Experimental test marker missing or duplicated')
    return text.replace('\n', newline)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    args = p.parse_args()
    target = Path(args.root) / TARGET
    if not target.is_file():
        raise SystemExit('Missing inspected MarkText entry point: ' + str(target))
    try:
        original = target.read_text(encoding='utf-8-sig')
        modified = transform(original)
        target.write_text(modified, encoding='utf-8', newline='')
    except (OSError, ValueError) as exc:
        raise SystemExit('FAIL CLOSED: ' + str(exc))
    print('PASS: MarkText explicit crashReporter.start disabled only in temporary checkout')
    print('Native crash dump collection is reduced; this is an experimental test.')


if __name__ == '__main__':
    main()
