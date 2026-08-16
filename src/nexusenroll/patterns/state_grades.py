"""
===============================================================================
PATTERN 3 -- STATE  «Behavioural»             Diagram 03 zone 3, diagram 06 p1
===============================================================================

ROLE OF THE PATTERN IN THIS SYSTEM
    Two separate requirements land on the same object, and both are lifecycle
    concerns:

        "The system must have a process for grade approval (e.g. a 'Pending'
         state before a final 'Submitted' state)."

        "If an error occurs during the process (e.g. an invalid grade is
         submitted), the system must handle it gracefully and allow the
         professor to correct it WITHOUT LOSING OTHER SUBMITTED GRADES."

GoF ROLES
    Context       -- GradeSubmission (in domain/records.py)
    State         -- GradeState  (this file)
    ConcreteState -- DraftState, PendingApprovalState,
                     PartiallyRejectedState, SubmittedState

WHY THE PATTERN EARNS ITS PLACE
    Behaviour differs COMPLETELY by state: add_entry() is legal in Draft and
    illegal in PendingApproval; correct_entry() is legal only in
    PartiallyRejected; Submitted is terminal.  Encoding that as classes puts
    each legality rule next to the state it describes.

    The base class raises IllegalTransition by default, so an unhandled
    operation FAILS LOUDLY rather than corrupting a batch of 200 grades.  That
    is Fail Fast, and it is the second screencast demo.

    PartiallyRejectedState is the direct answer to the error-isolation
    requirement: on entry it retains every accepted entry and returns only the
    rejected ones.

WITHOUT IT
    A `status` enum plus an if/elif ladder in every mutating method of
    GradeSubmission.  Each new state multiplies branches across several
    methods, and nothing structurally stops a caller editing a submitted batch.

DESIGN-LEVEL DRY
    The same pattern shape is applied a second time to CourseChangeRequest --
    see state_course_change.py.  One design idea, two workflows.
"""

from __future__ import annotations

from abc import ABC

from ..domain.enums import EventType
from ..domain.events import DomainEvent
from ..domain.exceptions import IllegalTransition
from ..domain.records import Grade, GradeSubmission


# ---------------------------------------------------------------------------
# State interface
# ---------------------------------------------------------------------------
class GradeState(ABC):
    """STATE.

    Every method has a DEFAULT implementation that raises IllegalTransition.
    A ConcreteState overrides only the operations that are legal in it, so
    "what is illegal here" is expressed by silence rather than by boilerplate.
    """

    def name(self) -> str:
        return type(self).__name__

    def _refuse(self, operation: str) -> None:
        raise IllegalTransition(
            f"{operation}() is not legal while the submission is in "
            f"{self.name()}"
        )

    # -- default: everything is refused -------------------------------------
    def add_entry(self, ctx: GradeSubmission, grade: Grade) -> None:
        self._refuse("addEntry")

    def submit_for_approval(self, ctx: GradeSubmission) -> None:
        self._refuse("submitForApproval")

    def approve(self, ctx: GradeSubmission, admin_id: str) -> None:
        self._refuse("approve")

    def reject(self, ctx: GradeSubmission, reason: str) -> None:
        self._refuse("reject")

    def correct_entry(self, ctx: GradeSubmission, grade: Grade) -> None:
        self._refuse("correctEntry")


# ---------------------------------------------------------------------------
# Concrete states -- each one answers only for itself
# ---------------------------------------------------------------------------
class DraftState(GradeState):
    """The faculty member is still keying in the batch.

    Legal: add_entry, correct_entry (self-transitions), submit_for_approval.
    """

    def add_entry(self, ctx: GradeSubmission, grade: Grade) -> None:
        ctx.entries.append(grade)

    def correct_entry(self, ctx: GradeSubmission, grade: Grade) -> None:
        _replace_entry(ctx, grade)

    def submit_for_approval(self, ctx: GradeSubmission) -> None:
        if not ctx.entries:
            raise IllegalTransition("Cannot submit an empty grade batch")
        ctx.set_state(PendingApprovalState())  # Draft -> Pending


class PendingApprovalState(GradeState):
    """The "Pending" state named verbatim in the requirement.

    Legal: approve, reject.  ILLEGAL: add_entry -- the entry set is locked
    while an administrator is deciding, and attempting it raises
    IllegalTransition.  That refusal is screencast demo #2.
    """

    def approve(self, ctx: GradeSubmission, admin_id: str) -> None:
        """Guarded transition (diagram 06 p1): whether we land in Submitted or
        PartiallyRejected depends on whether every entry validated."""
        invalid = [(g, "invalid letter grade") for g in ctx.entries if not g.is_valid_letter()]
        if invalid:
            ctx.rejected_entries = invalid
            ctx.entries = [g for g in ctx.entries if g.is_valid_letter()]
            ctx.set_state(PartiallyRejectedState())
            return
        ctx.set_state(SubmittedState())

    def reject(self, ctx: GradeSubmission, reason: str) -> None:
        """Administrator declines the batch; it goes back for correction with
        the accepted entries intact."""
        ctx.rejected_entries = [(g, reason) for g in ctx.entries]
        ctx.set_state(PartiallyRejectedState())


class PartiallyRejectedState(GradeState):
    """THE ERROR-ISOLATION ANSWER.

    Entry action: accepted entries are RETAINED on ctx.entries; only the
    rejected ones sit in ctx.rejected_entries awaiting correction.  A professor
    correcting one bad grade in a roster of 200 does not lose the other 199.

    Legal: correct_entry, submit_for_approval.
    """

    def correct_entry(self, ctx: GradeSubmission, grade: Grade) -> None:
        ctx.rejected_entries = [
            (g, why)
            for (g, why) in ctx.rejected_entries
            if not (g.student_id == grade.student_id and g.course_code == grade.course_code)
        ]
        _replace_entry(ctx, grade)

    def submit_for_approval(self, ctx: GradeSubmission) -> None:
        if ctx.rejected_entries:
            raise IllegalTransition(
                f"{len(ctx.rejected_entries)} entries still need correction"
            )
        ctx.set_state(PendingApprovalState())


class SubmittedState(GradeState):
    """TERMINAL.  Every inherited default applies, so every transition is
    refused -- nothing can edit an already-submitted batch.  The class body is
    empty on purpose: that emptiness IS the behaviour."""


# ---------------------------------------------------------------------------
# Helper shared by the states that may edit entries (DRY)
# ---------------------------------------------------------------------------
def _replace_entry(ctx: GradeSubmission, grade: Grade) -> None:
    for i, existing in enumerate(ctx.entries):
        if (
            existing.student_id == grade.student_id
            and existing.course_code == grade.course_code
        ):
            ctx.entries[i] = grade
            return
    ctx.entries.append(grade)


# ---------------------------------------------------------------------------
# Factory helper -- keeps the domain package free of a pattern import
# ---------------------------------------------------------------------------
def new_grade_submission(
    submission_id: str, section_id: str, faculty_id: str, semester
) -> GradeSubmission:
    """Every GradeSubmission starts in DraftState (the initial pseudostate on
    diagram 06 page 1)."""
    submission = GradeSubmission(submission_id, section_id, faculty_id, semester)
    submission.set_state(DraftState())
    return submission


# ---------------------------------------------------------------------------
# Batch processing -- per-entry validation, not per-batch
# ---------------------------------------------------------------------------
class BatchGradeProcessor:
    """Diagram 04 page 2, lane 3.

    ERROR ISOLATION: validation runs per ENTRY.  One bad letter grade in a
    roster of 200 rejects one entry, not 200.  This class is separate from
    GradeSubmission by SRP -- the submission owns its lifecycle, the processor
    owns batch validation.
    """

    def __init__(self, enrol_repo, publisher=None) -> None:
        self._enrolments = enrol_repo
        self._publisher = publisher

    def validate_batch(
        self, submission: GradeSubmission, grades: list[Grade]
    ) -> tuple[list[Grade], list[tuple[Grade, str]]]:
        """Returns (accepted, rejected_with_reason) -- never raises for a merely
        invalid entry, which keeps the caller's loop uniform."""
        enrolled_ids = {
            e.student_id
            for e in self._enrolments.find_by_section(submission.section_id)
        }
        accepted: list[Grade] = []
        rejected: list[tuple[Grade, str]] = []
        already_graded: set[str] = set()

        for grade in grades:
            if not grade.is_valid_letter():
                rejected.append((grade, f"'{grade.letter_grade}' is not a valid letter grade"))
            elif grade.student_id not in enrolled_ids:
                rejected.append((grade, "student is not enrolled in this section"))
            elif grade.student_id in already_graded:
                rejected.append((grade, "duplicate entry for this student"))
            else:
                already_graded.add(grade.student_id)
                accepted.append(grade)
        return accepted, rejected

    def apply_to_records(self, submission: GradeSubmission, record_repo) -> int:
        """Entry action of SubmittedState: "update student academic records"."""
        applied = 0
        for grade in submission.entries:
            record = record_repo.find(grade.student_id)
            if record is not None:
                record.add_grade(grade)
                record_repo.save(record)
                applied += 1
        if self._publisher is not None:
            # Observer (pattern 4) again: records updated -> tell whoever cares.
            self._publisher.publish(
                DomainEvent(
                    EventType.GRADES_SUBMITTED,
                    {
                        "section_id": submission.section_id,
                        "faculty_id": submission.faculty_id,
                        "count": applied,
                    },
                )
            )
        return applied
