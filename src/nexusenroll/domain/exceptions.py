"""Domain exceptions.

Every one of these is a *Fail Fast* mechanism (see 02-design-principles.md):
an illegal operation raises loudly rather than silently corrupting state.
"""


class NexusEnrollError(Exception):
    """Base class so callers can catch everything this domain raises."""


class CapacityExceeded(NexusEnrollError):
    """Raised by CourseSection.reserveSeat() when the section is full.

    Encapsulation: the invariant 0 <= enrolled_count <= total_capacity is
    enforced *inside* CourseSection, not by its callers.
    """


class IllegalState(NexusEnrollError):
    """Raised by CourseSection.releaseSeat() when the count is already zero."""


class IllegalTransition(NexusEnrollError):
    """Raised by the State pattern (pattern 3) default implementations.

    Calling addEntry() on a submission in PendingApprovalState -- or anything
    at all on SubmittedState -- lands here.  This is the demo in the screencast.
    """


class TransactionFailed(NexusEnrollError):
    """Raised inside a Command's execute() to force a rollback in the demo."""
