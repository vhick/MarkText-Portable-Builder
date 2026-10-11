# MarkText True-Portable Builder (Windows x64)

This GitHub repository builds a private/unofficial Windows ZIP from your **clean `marktext` fork, `develop` branch**.

## Scope

Your user-confirmed residue is `%APPDATA%\marktext\Crashpad`. The patch in `packages/desktop/src/main/index.ts` runs **after** the upstream portable-path setup and **before** `crashReporter.start()`.

When packaged MarkText runs on Windows, the patch redirects `crashDumps`, `sessionData` and `logs` to its already-selected `userData` directory. Make a `marktext-user-data` folder beside `marktext.exe` and those paths should stay under it.

## Build

**Actions → Build MarkText True Portable → Run workflow**

- Leave source repository blank to use `<your-account>/marktext`.
- Source ref should be `develop` (the upstream project's current development branch).
- Download `MarkText-True-Portable-Windows-x64-<commit>` from Artifacts.
- Extract the embedded `MarkText-True-Portable-Windows-x64-<commit>.zip`.
- Keep `marktext-user-data` beside `marktext.exe`.

The build uses upstream `pnpm run build:win:x64`, then repackages only the upstream Windows ZIP. It does not upload the installer.

## Future failures

The patch is deliberately fail-closed if its startup anchors change. Upload the GitHub Actions **job log archive** when troubleshooting.

## Caveats

- No complete Windows build/runtime test has yet been performed by this package author.
- This package targets the current source structure, which can change.
- The change addresses the confirmed Crashpad escape; it is not a guarantee that Windows jump-list entries, file associations, credential stores, recent-file state, and system-managed traces are absent.
- Do not modify your Universal Fork Sync until a real build has been tested.
