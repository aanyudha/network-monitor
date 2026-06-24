from __future__ import annotations

from collections import defaultdict

from app.core.models import DiscoveryClassification, DiscoveryFingerprint


PRINTER_VENDORS = {"hp", "brother", "canon", "epson", "lexmark", "xerox", "ricoh", "kyocera"}
ROUTER_VENDORS = {"cisco", "mikrotik", "tp-link", "netgear", "d-link", "asus", "fortinet", "ubiquiti"}
SWITCH_VENDORS = {"cisco", "aruba", "hpe", "juniper", "netgear", "d-link", "tplink", "tp-link"}
AP_VENDORS = {"aruba", "unifi", "ubiquiti", "tp-link", "mikrotik", "ruckus", "engenius"}
CCTV_VENDORS = {"hikvision", "dahua", "axis", "reolink", "uniview", "hanwha"}


class DiscoveryClassificationEngine:
    def classify(self, fingerprint: DiscoveryFingerprint) -> DiscoveryClassification:
        scores: dict[str, int] = defaultdict(int)
        evidence: dict[str, list[str]] = defaultdict(list)

        ports = set(fingerprint.open_ports)
        text = " ".join(
            part.lower()
            for part in [
                fingerprint.hostname,
                fingerprint.http_title,
                fingerprint.http_server,
                fingerprint.vendor_name,
            ]
            if part
        )
        vendor = fingerprint.vendor_name.lower()

        self._apply_printer_rules(scores, evidence, ports, text, vendor)
        self._apply_router_rules(scores, evidence, fingerprint.is_gateway, ports, text, vendor)
        self._apply_switch_rules(scores, evidence, ports, text, vendor)
        self._apply_ap_rules(scores, evidence, ports, text, vendor)
        self._apply_cctv_rules(scores, evidence, ports, text, vendor)
        self._apply_nvr_rules(scores, evidence, ports, text, vendor)
        self._apply_server_rules(scores, evidence, ports, text)
        self._apply_web_app_rules(scores, evidence, ports, fingerprint.http_status_code, fingerprint.http_title)
        self._apply_pc_rules(scores, evidence, ports, text)

        if not scores:
            if ports or fingerprint.http_title or fingerprint.vendor_name:
                notes = self._compose_generic_notes(ports, fingerprint.http_title, fingerprint.vendor_name)
                return DiscoveryClassification(device_type="Other", confidence=35, notes=notes)
            return DiscoveryClassification(
                device_type="Unknown",
                confidence=5,
                notes="Device responded to discovery but only heartbeat-level evidence was available.",
            )

        best_type = max(scores, key=lambda item: (scores[item], item))
        best_score = min(scores[best_type], 100)

        if best_score < 35:
            notes = self._compose_generic_notes(ports, fingerprint.http_title, fingerprint.vendor_name)
            return DiscoveryClassification(device_type="Other", confidence=max(best_score, 20), notes=notes)

        notes = "; ".join(evidence[best_type]) or self._compose_generic_notes(
            ports, fingerprint.http_title, fingerprint.vendor_name
        )
        return DiscoveryClassification(device_type=best_type, confidence=best_score, notes=notes)

    def _apply_printer_rules(self, scores, evidence, ports, text: str, vendor: str) -> None:
        printer_ports = {9100, 515, 631}
        if ports & printer_ports:
            scores["Printer"] += 45
            evidence["Printer"].append(f"Open printer ports: {', '.join(str(port) for port in sorted(ports & printer_ports))}.")
        if any(keyword in text for keyword in ("printer", "ipp", "jetdirect", "laserjet", "deskjet")):
            scores["Printer"] += 35
            evidence["Printer"].append("Hostname or HTTP title matched printer keywords.")
        if vendor and any(brand in vendor for brand in PRINTER_VENDORS):
            scores["Printer"] += 25
            evidence["Printer"].append(f"Vendor matched printer brand: {vendor}.")

    def _apply_router_rules(self, scores, evidence, is_gateway: bool, ports, text: str, vendor: str) -> None:
        if is_gateway:
            scores["Router"] += 60
            evidence["Router"].append("IP matches a detected default gateway.")
        infra_ports = ports & {80, 443, 22, 23, 161}
        if infra_ports:
            scores["Router"] += 10 + (len(infra_ports) * 4)
            evidence["Router"].append(f"Open infrastructure ports: {', '.join(str(port) for port in sorted(infra_ports))}.")
        if any(keyword in text for keyword in ("router", "gateway", "gw", "firewall", "edge")):
            scores["Router"] += 30
            evidence["Router"].append("Hostname or banner matched router keywords.")
        if vendor and any(brand in vendor for brand in ROUTER_VENDORS):
            scores["Router"] += 18
            evidence["Router"].append(f"Vendor matched router brand: {vendor}.")

    def _apply_switch_rules(self, scores, evidence, ports, text: str, vendor: str) -> None:
        if 161 in ports:
            scores["Switch"] += 22
            evidence["Switch"].append("SNMP port 161 is open.")
        if any(keyword in text for keyword in ("switch", "stack", "distribution", "access-switch")):
            scores["Switch"] += 32
            evidence["Switch"].append("Hostname or banner matched switch keywords.")
        if vendor and any(brand in vendor for brand in SWITCH_VENDORS):
            scores["Switch"] += 20
            evidence["Switch"].append(f"Vendor matched switch brand: {vendor}.")

    def _apply_ap_rules(self, scores, evidence, ports, text: str, vendor: str) -> None:
        if any(keyword in text for keyword in ("access point", "wireless", "wifi", "unifi", "aruba", "uap", "ap-")):
            scores["AP"] += 35
            evidence["AP"].append("Hostname or banner matched access-point keywords.")
        if vendor and any(brand in vendor for brand in AP_VENDORS):
            scores["AP"] += 24
            evidence["AP"].append(f"Vendor matched access-point brand: {vendor}.")
        if ports & {80, 443, 22}:
            scores["AP"] += 6
            evidence["AP"].append("Management ports are open.")

    def _apply_cctv_rules(self, scores, evidence, ports, text: str, vendor: str) -> None:
        video_ports = ports & {554, 8000, 8899}
        if 554 in ports:
            scores["CCTV"] += 25
            evidence["CCTV"].append("RTSP port 554 is open.")
        if video_ports & {8000, 8899}:
            scores["CCTV"] += 15
            evidence["CCTV"].append("ONVIF or camera management ports are open.")
        if any(keyword in text for keyword in ("camera", "cctv", "ipcam", "onvif", "hikvision", "dahua", "axis")):
            scores["CCTV"] += 35
            evidence["CCTV"].append("Hostname or banner matched camera keywords.")
        if vendor and any(brand in vendor for brand in CCTV_VENDORS):
            scores["CCTV"] += 24
            evidence["CCTV"].append(f"Vendor matched camera brand: {vendor}.")

    def _apply_nvr_rules(self, scores, evidence, ports, text: str, vendor: str) -> None:
        video_ports = ports & {554, 8000, 8899}
        if len(video_ports) >= 2:
            scores["NVR"] += 28
            evidence["NVR"].append("Multiple RTSP or ONVIF-related ports are open.")
        if any(keyword in text for keyword in ("nvr", "dvr", "video recorder", "surveillance", "xvr")):
            scores["NVR"] += 42
            evidence["NVR"].append("Hostname or banner matched NVR keywords.")
        if vendor and any(brand in vendor for brand in CCTV_VENDORS):
            scores["NVR"] += 12
            evidence["NVR"].append(f"Vendor matched surveillance brand: {vendor}.")

    def _apply_server_rules(self, scores, evidence, ports, text: str) -> None:
        server_ports = ports & {22, 3389, 3306, 5432, 1433, 8080, 8443}
        if server_ports:
            scores["Server"] += min(60, 12 + (len(server_ports) * 10))
            evidence["Server"].append(f"Open server ports: {', '.join(str(port) for port in sorted(server_ports))}.")
        if any(keyword in text for keyword in ("server", "sql", "db", "database", "app", "vm")):
            scores["Server"] += 18
            evidence["Server"].append("Hostname or banner matched server keywords.")

    def _apply_web_app_rules(self, scores, evidence, ports, http_status_code: int | None, http_title: str) -> None:
        web_ports = ports & {80, 443, 8080, 8443}
        if web_ports:
            scores["Web App"] += 20
            evidence["Web App"].append(f"HTTP or HTTPS ports are open: {', '.join(str(port) for port in sorted(web_ports))}.")
        if http_status_code is not None:
            scores["Web App"] += 18
            evidence["Web App"].append(f"HTTP responded with status {http_status_code}.")
        if http_title:
            scores["Web App"] += 15
            evidence["Web App"].append(f"HTTP title detected: {http_title}.")

    def _apply_pc_rules(self, scores, evidence, ports, text: str) -> None:
        workstation_ports = ports & {139, 445, 3389}
        if workstation_ports:
            scores["PC"] += 12 + (len(workstation_ports) * 10)
            evidence["PC"].append(
                f"Open workstation ports: {', '.join(str(port) for port in sorted(workstation_ports))}."
            )
        if any(keyword in text for keyword in ("desktop", "laptop", "workstation", "pc", "win-", "ws-")):
            scores["PC"] += 20
            evidence["PC"].append("Hostname matched workstation naming patterns.")

    @staticmethod
    def _compose_generic_notes(ports, http_title: str, vendor_name: str) -> str:
        parts = []
        if ports:
            parts.append(f"Open ports observed: {', '.join(str(port) for port in sorted(ports))}.")
        if http_title:
            parts.append(f"HTTP title: {http_title}.")
        if vendor_name:
            parts.append(f"Vendor hint: {vendor_name}.")
        return " ".join(parts) or "Insufficient fingerprint evidence was collected."
