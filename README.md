# Heisenberg Network Monitor

Open-source desktop network heartbeat and agentless monitoring tool for Windows and Linux.

## Overview

Heisenberg Network Monitor is a PySide6 desktop application for agentless device monitoring by IP. It focuses on heartbeat checks, latency, port health, HTTP availability, inventory tracking, alert history, discovery workflows, and exportable reports while keeping monitoring logic separate from the UI.

## Features

- Polished desktop dashboard with live summary cards and recent alerts
- Device inventory with SQLite-backed CRUD
- Agentless heartbeat and latency monitoring by IP
- TCP port checks for common and custom ports
- HTTP and HTTPS availability checks with optional keyword matching
- Subnet discovery for example ranges such as `192.168.1.0/24`
- Best-effort discovery classification with confidence scoring and review-before-save import flow
- Alert history with offline, latency, port, and HTTP failure events
- Traffic visibility imports from DNS and firewall CSV logs with per-device summaries
- CSV report export for downtime and availability
- Light and dark themes

## Screenshots

See [docs/SCREENSHOTS.md](docs/SCREENSHOTS.md) for placeholders and capture guidance.

## Installation

```bash
python -m venv .venv
. .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
```

## Run

```bash
python -m app.main
```

On first run, the application creates a local SQLite database and seeds sample devices using documentation-safe example addresses.

## Build Windows EXE

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m pytest
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_exe.ps1
```

The EXE is generated at `dist/HeisenbergNetworkMonitor/HeisenbergNetworkMonitor.exe`.
Generated `build/` and `dist/` folders are ignored by git.

More detail lives in [docs/BUILD_WINDOWS.md](docs/BUILD_WINDOWS.md).

## Heisenberg Framework summary

The project applies Heisenberg principles through:

- Workflow first architecture: monitoring cycles and discovery flows drive the design.
- Engine based architecture: heartbeat, HTTP, port, alert, discovery, and reporting logic live in reusable engines.
- Business driven design: modules reflect operator workflows such as devices, dashboard, alerts, monitoring, and reports.
- Thin UI and engine-hidden UX: Qt pages trigger actions and services without owning monitoring logic.
- Read/write separation: repositories persist state, while dashboard and reporting services aggregate read models for the UI.

More detail lives in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Agentless monitoring

No agent is required on monitored PCs or servers. The current release uses IP-based heartbeat, TCP connectivity, HTTP requests, and discovery scans. SNMP is prepared behind an abstraction for future interface and bandwidth monitoring.

Traffic visibility is also agentless, but it depends on imported DNS, firewall, proxy, or future flow-export logs. Agentless IP discovery alone cannot reveal per-PC browsing history or destination domains.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).
