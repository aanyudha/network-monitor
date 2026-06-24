# Architecture

## Principles

The project follows a Heisenberg-style layering:

- Workflow: monitoring loop, discovery flow, reporting flow
- Module: dashboard, devices, monitoring, alerts, reports
- Engine: heartbeat, port check, HTTP check, discovery, discovery classification, traffic visibility, alert, reporting, SNMP stub

## Key rules

- UI pages do not talk directly to engines.
- Actions and services orchestrate write behavior.
- Repositories own persistence.
- Engines stay reusable and UI-agnostic.
- Background workers isolate monitoring activity from the main Qt thread.
- Discovery review and traffic import flows follow Action -> Service -> Engine/Repository boundaries.

## Application flow

1. `app.main` bootstraps repositories, services, engines, and pages.
2. Pages call actions such as device create, update, discovery review import, and traffic log import.
3. `MonitoringService` executes heartbeat, port, HTTP, and discovery workflows through engines.
4. `DiscoveryClassificationEngine` turns best-effort fingerprints into device type, confidence, and notes without letting the UI touch probing logic directly.
5. `TrafficVisibilityService` imports supported log sources, maps source IPs to known devices, and stores observations for device-detail views.
6. Results are persisted and summarized for dashboard and reporting readers.
7. The UI refreshes through worker signals and lightweight read services.

## Extension points

- Event bus publishes device and alert changes.
- SNMP engine is intentionally abstracted for later expansion.
- Reporting engine can grow into PDF or scheduled exports without changing UI pages.
- Traffic visibility is prepared for DNS, firewall, proxy, NetFlow, router export, and future flow-source adapters.
