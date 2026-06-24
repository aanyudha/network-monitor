from __future__ import annotations

from collections.abc import Callable

from app.core.models import TrafficObservation


class TrafficVisibilityRepository:
    def __init__(self, connection_factory: Callable) -> None:
        self._connection_factory = connection_factory

    def insert_many(self, observations: list[TrafficObservation]) -> int:
        with self._connection_factory() as connection:
            connection.executemany(
                """
                INSERT INTO traffic_observations (
                    device_id, source_ip, destination_ip, domain, public_ip, protocol, port,
                    source_type, observed_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        observation.device_id,
                        observation.source_ip,
                        observation.destination_ip,
                        observation.domain,
                        observation.public_ip,
                        observation.protocol,
                        observation.port,
                        observation.source_type,
                        observation.observed_at,
                        observation.created_at,
                    )
                    for observation in observations
                ],
            )
            connection.commit()
        return len(observations)

    def recent_for_device(self, device_id: int, limit: int = 25) -> list[TrafficObservation]:
        with self._connection_factory() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM traffic_observations
                WHERE device_id = ?
                ORDER BY observed_at DESC, id DESC
                LIMIT ?
                """,
                (device_id, limit),
            ).fetchall()
        return [self._row_to_observation(row) for row in rows]

    @staticmethod
    def _row_to_observation(row) -> TrafficObservation:
        return TrafficObservation(
            id=row["id"],
            device_id=row["device_id"],
            source_ip=row["source_ip"],
            destination_ip=row["destination_ip"],
            domain=row["domain"],
            public_ip=row["public_ip"],
            protocol=row["protocol"],
            port=row["port"],
            source_type=row["source_type"],
            observed_at=row["observed_at"],
            created_at=row["created_at"],
        )
