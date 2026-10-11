#!/usr/bin/env python3
"""v1.2.3 experimental patch: disable BOTH MarkText explicit Crashpad starts.

Used on the temporary GitHub checkout AFTER the existing v1.1 path patch.
Does not disable JS uncaughtException logging or the dialog/error handlers.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

INDEX = Path('packages/desktop/src/main/index.ts')
HANDLER = Path('packages/desktop/src/main/exceptionHandler.ts')
INDEX_MARKER = 'MARKTEXT_CRASHPAD_ISOLATION_V12'
HANDLER_MARKER = 'MARKTEXT_EXCEPTION_CRASHPAD_ISOLATION_V123'
REPORTER_CALL = re.compile(
    r'(?ms)^[ \t]*crashReporter\s*\.\s*start\s*\(\s*\{(?P<body>.*?)\}\s*\)[ \t]*(?=\r?$|\n)'
)
ELECTRON_IMPORT = re.compile(
    r'(?m)^(?P<indent>[ \t]*)import\s*\{(?P<names>[^{}\r\n]+)\}\s*from\s*(?P<quote>[\'\"])electron(?P=quote)[ \t]*;?[ \t]*$'
)


def remove_electron_import(text: str, file_label: str) -> str:
    matches = list(ELECTRON_IMPORT.finditer(text))
    with_reporter = [m for m in matches if 'crashReporter' in [x.strip() for x in m.group('names').split(',')]]
    if len(with_reporter) != 1:
        raise ValueError(f'{file_label}: expected one Electron import of crashReporter, found {len(with_reporter)}')
    m = with_reporter[0]
    fields = [x.strip() for x in m.group('names').split(',')]
    fields.remove('crashReporter')
    if not fields:
        raise ValueError(f'{file_label}: unexpected Electron import with no remaining symbols')
    fixed = f"{m.group('indent')}import {{ {', '.join(fields)} }} from {m.group('quote')}electron{m.group('quote')}"
    return text[:m.start()] + fixed + text[m.end():]


def verify_body(body: str, file_label: str) -> None:
    # These two upstream calls use simple scalar options. Reject any unknown
    # option, but allow minor whitespace, product-name capitalization and comments.
    opts: dict[str, str] = {}
    for raw in body.splitlines():
        line = re.split(r'\s+//', raw, maxsplit=1)[0].strip().rstrip(',').strip()
        if not line:
            continue
        item = re.fullmatch(r'([A-Za-z_$][\w$]*)\s*:\s*(.+)', line)
        if not item:
            raise ValueError(f'{file_label}: unexpected crash reporter option syntax {line!r}')
        key, value = item.groups()
        if key in opts:
            raise ValueError(f'{file_label}: duplicate reporter option {key}')
        opts[key] = value.strip()
    # Check safety-significant values; both known calls disable uploads.
    if opts.get('uploadToServer') != 'false':
        raise ValueError(f'{file_label}: uploadToServer is not false; source inspection required')
    if opts.get('compress') != 'true':
        raise ValueError(f'{file_label}: unexpected compress option; source inspection required')
    if opts.get('productName') not in {"'marktext'", "'MarkText'", '"marktext"', '"MarkText"'}:
        raise ValueError(f'{file_label}: unknown productName; source inspection required')
    if 'companyName' not in opts or not re.fullmatch(r"[\'\"][^\'\"]*[\'\"]", opts['companyName']):
        raise ValueError(f'{file_label}: unexpected companyName; source inspection required')
    if file_label == 'exceptionHandler.ts':
        # GitHub's current develop source has a local-only submitURL.
        if opts.get('submitURL') not in {"'http://0.0.0.0/'", '"http://0.0.0.0/"'}:
            raise ValueError('exceptionHandler.ts: unexpected submitURL; source inspection required')
        expected = {'companyName', 'productName', 'submitURL', 'uploadToServer', 'compress'}
    else:
        expected = {'companyName', 'productName', 'uploadToServer', 'compress'}
    if set(opts) != expected:
        raise ValueError(f'{file_label}: unexpected option names: {sorted(opts)}')


def transform_source(original: str, file_label: str, marker: str) -> str:
    newline = '\r\n' if '\r\n' in original else '\n'
    text = original.replace('\r\n', '\n')
    if marker in text:
        raise ValueError(f'{file_label}: already patched; use a fresh checkout')
    matches = list(REPORTER_CALL.finditer(text))
    if len(matches) != 1:
        raise ValueError(f'{file_label}: expected exactly ONE real crashReporter.start call, found {len(matches)}')
    verify_body(matches[0].group('body'), file_label)
    replacement = (
        f'// {marker}\n'
        '// Experimental portable build: explicit native crash reporting DISABLED.\n'
        '// JavaScript error and exception handlers remain in place.'
    )
    text = text[:matches[0].start()] + replacement + text[matches[0].end():]
    text = remove_electron_import(text, file_label)
    if REPORTER_CALL.search(text):
        raise ValueError(f'{file_label}: an active crashReporter.start call remains')
    return text.replace('\n', newline)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    args = ap.parse_args()
    root = Path(args.root)
    index_path, handler_path = root / INDEX, root / HANDLER
    if not index_path.is_file() or not handler_path.is_file():
        raise SystemExit('FAIL CLOSED: MarkText source paths changed; expected index.ts and exceptionHandler.ts')
    try:
        original_index = index_path.read_bytes().decode('utf-8-sig')
        original_handler = handler_path.read_bytes().decode('utf-8-sig')
        if 'MARKTEXT_PORTABLE_CRASHPAD_V11' not in original_index:
            raise ValueError('v1.1 portable path patch must run first')
        if 'setupExceptionHandler()' not in original_index:
            raise ValueError('MarkText startup structure changed: no setupExceptionHandler() call')
        # Validate both in memory BEFORE writing either file.
        updated_index = transform_source(original_index, 'index.ts', INDEX_MARKER)
        updated_handler = transform_source(original_handler, 'exceptionHandler.ts', HANDLER_MARKER)
        if 'process.on(\'uncaughtException\'' not in updated_handler:
            raise ValueError('Unexpected change to JS error handlers')
        if 'ipcMain.on(\'mt::handle-renderer-error\'' not in updated_handler:
            raise ValueError('Unexpected change to renderer error handler')
        index_path.write_text(updated_index, encoding='utf-8', newline='')
        handler_path.write_text(updated_handler, encoding='utf-8', newline='')
    except (ValueError, OSError) as exc:
        raise SystemExit('FAIL CLOSED: ' + str(exc))
    print('PASS: disabled index.ts crashReporter.start')
    print('PASS: disabled exceptionHandler.ts early crashReporter.start')
    print('PASS: preserved normal JavaScript exception handlers')
    print('EXPERIMENTAL ONLY: Windows runtime still needs verification.')


if __name__ == '__main__':
    main()
