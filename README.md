# MarkText True-Portable GitHub Builder — Master v1.3

This repo holds **two independent GitHub Actions workflows** for a Windows MarkText portable build, both using the same tested source-level portability changes.

## Which workflow?

| Workflow | Builds | How settings remain safe |
|---|---|---|
| `build-portable.yml` | Standalone Windows ZIP | MarkText data is stored in `marktext-user-data` **beside** `marktext.exe` |
| `build-paf-portable.yml` | PAF-compatible app binary ZIP | The PortableApps launcher passes `--user-data-dir "%PAL:DataDir%\marktext-user-data"` to redirect settings to the **top-level Data folder** |

The GitHub builder repo contains **no executable and no user settings**. GitHub compiles a fresh EXE from the clean fork when you run a workflow.

## Changes applied during each GitHub build

The following patch sequence is identical across both builds:

1. `patch_marktext_portable.py` — v1.1 Electron `userData`, `sessionData`, logs and crash paths, plus `portable-paths.txt` diagnostics.
2. `verify_marktext_source.py` — verifies v1.1 **while the upstream `crashReporter.start` call still exists**.
3. `Disable-Crashpad-For-Test.py` — removes **both** upstream explicit `crashReporter.start()` calls, including the earlier one in `exceptionHandler.ts`.
4. `Verify-Crashpad-Isolation-Source.py` — confirms that both reporter calls are disabled and JavaScript error logging remains.
5. `Verify-MarkText-PAF-Source.py` — checks no reporter calls remain and portable paths/CLI support are present. Used for both build types.

**Historical script names are kept for compatibility with the successfully tested PAF workflow.** These are now the production patch steps, not separate experimental workflows.

## Build commands (no tools required on your laptop)

On GitHub: **Actions → Build MarkText True Portable → Run workflow** for the standalone ZIP, or **Actions → Build MarkText PAF-Compatible Windows x64 → Run workflow** for the PortableApps binary.

Leave the source repository field blank to use `YOUR-GITHUB-USERNAME/marktext`. Set source ref to `develop`, as previously tested. Source checkout must be the clean fork; never commit source patches into it.

Both workflows use pnpm/Node on GitHub's Windows runner, run the upstream `pnpm run build:win:x64`, and upload the assembled ZIP through GitHub artifacts.

## Installation

**Standalone:** Download the `MarkText-True-Portable-Windows-x64-...` artifact, extract the embedded ZIP **completely**, and keep the adjacent `marktext-user-data` folder. Run `marktext.exe` or the packaged launcher. For testing, use `VERIFY-MARKTEXT-PORTABLE.cmd`.

**PAF:** Download `MarkText-PAF-Binary-Windows-x64-...`. Copy the entire contents of `App-Binary` from the embedded ZIP to `MarkTextPortable/App/MarkText/` inside your **separate** MarkText PortableApps skeleton. Launch **only** through `MarkTextPortable.exe`, because that launcher must provide `--user-data-dir`. Keep `MarkTextPortable/Data/marktext-user-data` outside the replaceable `App` folder. Do not add the adjacent marker folder inside `App/MarkText`.

## Important limitations

* The tested Windows runtime showed no regenerated `%APPDATA%\marktext` directory after both reporter calls were disabled; future versions and other OS-managed traces are not guaranteed absent.
* **Native Crashpad crash-report collection is disabled**, while MarkText's JavaScript error handlers remain.
* This build does **not** install or update software automatically on your PC; it builds a downloadable artifact.
* Future upstream source changes can cause the fail-closed patch checks to stop. Download the failed GitHub Actions job log and inspect the new upstream source before adapting anything.
* Keep your personal MarkText profile and documents out of the GitHub builder repository.

For one-time setup and rebuilding the repositories from scratch, read `START-HERE-BEGINNER-GUIDE.txt` from the outer ZIP.
