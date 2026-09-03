"""
Shared helper for batch-scoping subjects.
"""


def get_target_batches(subject, batches):
    """
    Return the set of batch indices that a subject applies to.

    Uses batch_id, batch, or schedule_id fields.
    If none are specified, returns all batches (shared subject).
    """
    subject_batch_id = (
        subject.get("batch_id")
        or subject.get("batch")
        or subject.get("schedule_id")
    )

    target = set()

    for b, batch in enumerate(batches):
        if subject_batch_id is not None:
            batch_id = (
                batch.get("id")
                if isinstance(batch, dict)
                else batch
            )
            if str(batch_id) != str(subject_batch_id):
                continue
        target.add(b)

    return target
