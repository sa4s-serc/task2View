"""Phase 6. Need–evidence reconciliation. Compares each question with the claims."""

from task2view.phase6.critic import refine_extracted_view
from task2view.phase6.reconcile import reconcile_evidence

__all__ = ["reconcile_evidence", "refine_extracted_view"]
