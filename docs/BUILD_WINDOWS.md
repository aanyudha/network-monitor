# Build Windows EXE

## Prerequisites

- Windows with Python 3.13.x
- PowerShell
- A local virtual environment

If you want a custom icon, place it at `assets/icon.ico` before building. The committed spec file will use it automatically when present.

## Create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## Install dependencies

```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Run tests

```powershell
python -m pytest
python scripts/smoke_check.py
```

You can also run the lightweight packaging entrypoint check with:

```powershell
python -m app.main --smoke
```

## Build with PyInstaller

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_exe.ps1
```

Batch wrapper:

```bat
scripts\build_windows_exe.bat
```

The PyInstaller spec file lives at `packaging/heisenberg-network-monitor.spec`.

## Output location

The generated executable is placed at:

`dist/HeisenbergNetworkMonitor/HeisenbergNetworkMonitor.exe`

## First-run note

The packaged application does not bundle a runtime SQLite database, logs, exports, cache, or local configuration. On first launch it creates local runtime folders and the database automatically.

## Troubleshooting

- If `pyinstaller` is not found, reinstall `requirements-dev.txt`.
- If Qt fails with a missing platform plugin error such as `xcb` or `windows`, rebuild from a clean virtual environment and verify PySide6 is installed in that same environment.
- If the EXE launches but cannot persist data, confirm the user can write to the local runtime directory created on first run.

## CI note

- CI should run `python -m pytest` on both Windows and Linux.
- EXE artifact upload should stay disabled until release packaging is intentionally enabled.
- Optional future GitHub Actions artifact step:

```yaml
# - name: Upload Windows EXE
#   uses: actions/upload-artifact@v4
#   with:
#     name: heisenberg-network-monitor-windows
#     path: dist/HeisenbergNetworkMonitor/
```
