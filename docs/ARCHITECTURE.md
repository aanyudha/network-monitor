# Architecture

## Principles

The project follows a Heisenberg-style layering:

- Workflow: monitoring loop, discovery flow, reporting flow
- Module: dashboard, devices, monitoring, alerts, reports
- Engine: heartbeat, port check, HTTP check, discovery, alert, reporting, SNMP stub

## Key rules

- UI pages do not talk directly to engines.
- Actions and services orchestrate write behavior.
- Repositories own persistence.
- Engines stay reusable and UI-agnostic.
- Background workers isolate monitoring activity from the main Qt thread.

## Application flow

1. `app.main` bootstraps repositories, services, engines, and pages.
2. Pages call actions such as device create, update, delete, and discovery import.
3. `MonitoringService` executes heartbeat, port, and HTTP checks on enabled devices.
4. Results are persisted and summarized for dashboard and reporting readers.
5. The UI refreshes through worker signals and lightweight read services.

## Extension points

- Event bus publishes device and alert changes.
- SNMP engine is intentionally abstracted for later expansion.
- Reporting engine can grow into PDF or scheduled exports without changing UI pages.

