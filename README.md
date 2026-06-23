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
- Alert history with offline, latency, port, and HTTP failure events
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

## Build and packaging notes

- The project targets Python 3.13.3.
- PySide6 supports Windows and Linux builds.
- A future packaging pass can add PyInstaller or Nuitka without changing the core architecture.

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

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

