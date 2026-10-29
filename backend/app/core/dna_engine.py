import logging
from typing import Dict, List, Optional
from app.models.schemas import DnaRecord, MetricVector, DnaHistoryResponse
from app.storage.state_store import state_store, StateStore

logger = logging.getLogger("software_dna.dna_engine")


class EvolutionaryDNAEngine:
    """
    Maintains the multi-generational software DNA matrix M(c, t) for all classes.
    """

    def __init__(self, store: Optional[StateStore] = None):
        self.store = store or state_store

    def record_class_dna(
        self,
        class_name: str,
        package_name: str,
        file_path: str,
        commit_sha: str,
        version_label: str,
        metrics: MetricVector,
        timestamp: str,
    ) -> DnaRecord:
        record = DnaRecord(
            class_name=class_name,
            package_name=package_name,
            file_path=file_path,
            commit_sha=commit_sha,
            version_label=version_label,
            metrics=metrics,
            timestamp=timestamp,
        )
        self.store.record_dna(record)
        return record

    def get_trajectory(self, class_name: str) -> Optional[DnaHistoryResponse]:
        records = self.store.get_dna_history(class_name)
        if not records:
            return None
        return DnaHistoryResponse(
            class_name=class_name,
            records=records,
            latest_metrics=records[-1].metrics,
        )

    def get_all_trajectories(self) -> Dict[str, List[DnaRecord]]:
        return self.store.dna_history
