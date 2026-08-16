"""
===============================================================================
PATTERN 6 -- FACADE  «Structural»             Diagram 03, zone 6
===============================================================================

ROLE OF THE PATTERN IN THIS SYSTEM
        "The same back-end services must be usable by both the web application
         and a future mobile application."

    Enrolling a student touches at least six collaborators.  Exposing them to
    the Service API layer would push orchestration into the presentation tier
    -- the exact coupling the 3-Tier layering exists to prevent, and it would
    break the shared-back-end requirement, because the web and mobile
    controllers would each grow their own copy of the orchestration.

    With the facade, enrol() is ONE call with ONE result.  The sequence diagram
    shows the client sending exactly one message and receiving one reply.

GoF ROLE
    Facade -- EnrollmentFacade, over: EnrollmentValidator (Strategy),
              TransactionManager + Commands (Command), the repositories, and
              NotificationPublisher (Observer).

THE DEPENDENCY INVERSION SHOWCASE
    Every collaborator arrives through the constructor as an abstraction.
    There is no `new`, no getInstance(), and no import of a concrete
    repository anywhere in this class body.  Every dependency is visible in the
    constructor signature -- which is precisely the property Singleton would
    have destroyed.

HOW THE PATTERNS COLLABORATE HERE (diagram 03, cross-reference panel)
    enrol() asks the VALIDATOR (Strategy) to run every rule
        -> wraps the state changes in an AddCourseCommand (Command)
        -> hands it to the TransactionManager (Command)
        -> AFTER COMMIT, publishes a domain event (Observer)
    Each observer then reacts independently.

WITHOUT IT
    Each API controller orchestrating validation, command construction,
    transaction control and event publication -- duplicated between web and
    mobile, and drifting apart over time.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..domain.enrollment import EnrollmentRequest
from ..domain.enums import EventType
from ..domain.events import DomainEvent
from ..repositories.interfaces import IEnrollmentRepository, IWaitlistRepository
from .command_enrollment import (
    AddCourseCommand,
    DropCourseCommand,
    EnrolmentReceiver,
    TransactionManager,
)
from .observer_notifications import NotificationPublisher
from .strategy_validation import EnrollmentValidator


@dataclass
class EnrolmentOutcome:
    """The single reply the client receives.  Deliberately simple: a boolean, a
    message, and the failed rules when there are any."""

    success: bool
    message: str
    failed_rules: list[str] = field(default_factory=list)
    waitlist_position: int | None = None

    def __bool__(self) -> bool:
        return self.success

    def __str__(self) -> str:  # pragma: no cover - display only
        return ("OK: " if self.success else "REFUSED: ") + self.message


class EnrollmentFacade:
    """FACADE.

    Note the constructor: validator, transaction manager, publisher, receiver
    and two repositories -- all injected, all abstractions.  Swapping the
    in-memory repositories for SQL ones, or the real publisher for a silent
    test double, requires no change inside this class.
    """

    def __init__(
        self,
        validator: EnrollmentValidator,
        tx_manager: TransactionManager,
        publisher: NotificationPublisher,
        receiver: EnrolmentReceiver,
        enrol_repo: IEnrollmentRepository,
        waitlist_repo: IWaitlistRepository,
        semester,
    ) -> None:
        self._validator = validator
        self._tx = tx_manager
        self._publisher = publisher
        self._receiver = receiver
        self._enrolments = enrol_repo
        self._waitlists = waitlist_repo
        self._semester = semester

    # -----------------------------------------------------------------------
    # The one operation the web SPA and the future mobile app both call.
    # -----------------------------------------------------------------------
    def enrol(
        self,
        student_id: str,
        section_id: str,
        is_override: bool = False,
        fail_on_step: int | None = None,
    ) -> EnrolmentOutcome:
        """Message 1 on sequence diagram page 1; the whole of diagram 04 page 1.

        `fail_on_step` exists solely so the screencast can force a mid-
        transaction failure and show the rollback.  Production callers omit it.
        """
        request = EnrollmentRequest(student_id, section_id, is_override)

        # --- STRATEGY: run every rule, aggregate every failure --------------
        result = self._validator.validate_all(request)
        if not result.is_valid():
            failed = self._validator.failed_rules(request)

            # The waitlist branch (diagram 04, note "Waitlist branch"):
            # distinguishing "full" from "ineligible" matters.  A student who
            # fails ONLY the capacity check is otherwise eligible, so queue
            # them; anyone else must be refused.
            if failed == ["CapacityRule"]:
                position = self._waitlists.for_section(section_id).add(student_id)
                return EnrolmentOutcome(
                    False,
                    f"Section full - waitlisted at position {position}",
                    failed,
                    waitlist_position=position,
                )
            return EnrolmentOutcome(False, str(result), failed)

        # --- COMMAND: wrap the three state changes, run atomically ----------
        command = AddCourseCommand(
            request, self._receiver, self._semester, fail_on_step=fail_on_step
        )
        tx_result = self._tx.run_atomic([command])
        if not tx_result:
            # Rollback already happened inside run_atomic().  Nothing partial
            # survives, so we can safely report a clean failure.
            self._publisher.publish(
                DomainEvent(
                    EventType.SYSTEM_ERROR,
                    {"source": "enrol", "detail": tx_result.message},
                )
            )
            return EnrolmentOutcome(False, f"Transaction failed, {tx_result.message}")

        # --- OBSERVER: fire-and-forget, strictly AFTER the commit ----------
        # The enrolment is already valid and committed at this point.  If every
        # observer failed, this call would still return success -- which is the
        # concrete meaning of "decoupled from the core enrolment logic".
        section = self._receiver.sections.find(section_id)
        self._publisher.publish(
            DomainEvent(
                EventType.STUDENT_ENROLLED,
                {
                    "student_id": student_id,
                    "section_id": section_id,
                    "course_code": section.course_code if section else "",
                },
            )
        )
        return EnrolmentOutcome(True, f"Enrolled in {section_id}")

    def drop(self, student_id: str, section_id: str) -> EnrolmentOutcome:
        """Sequence diagram page 2 -- the Observer showcase.

        A drop publishes TWO events: SeatReleased (which the WaitlistObserver
        consumes to alert the next queued student) and StudentDropped (which the
        AdvisorObserver consumes, guarded on degree-criticality).
        """
        section = self._receiver.sections.find(section_id)
        course_code = section.course_code if section else ""

        command = DropCourseCommand(student_id, section_id, self._receiver, self._semester)
        tx_result = self._tx.run_atomic([command])
        if not tx_result:
            return EnrolmentOutcome(False, f"Drop failed, {tx_result.message}")

        # Everything below this line is asynchronous and fully decoupled --
        # the red boundary on sequence diagram page 2.
        payload = {
            "student_id": student_id,
            "section_id": section_id,
            "course_code": course_code,
        }
        self._publisher.publish(DomainEvent(EventType.SEAT_RELEASED, payload))
        self._publisher.publish(DomainEvent(EventType.STUDENT_DROPPED, payload))

        return EnrolmentOutcome(True, f"Dropped {section_id}")

    def force_add(
        self, admin_validator: EnrollmentValidator, student_id: str, section_id: str
    ) -> EnrolmentOutcome:
        """Administrator override -- "force-add a student into a full class".

        The override is implemented by handing in a DIFFERENT RULE LIST (one
        composed without CapacityRule), not by adding an `if admin` branch
        inside a rule.  That is Strategy plus composition doing the work.
        """
        original = self._validator
        try:
            self._validator = admin_validator
            return self.enrol(student_id, section_id, is_override=True)
        finally:
            self._validator = original

    # -----------------------------------------------------------------------
    # Read-only queries the facade also fronts
    # -----------------------------------------------------------------------
    def view_schedule(self, student_id: str, semester=None) -> dict[str, list[str]]:
        """Personal Schedule Management: the calendar-like view."""
        schedule = self._receiver.schedules.find(student_id, semester or self._semester)
        return schedule.as_calendar_view() if schedule else {}

    def past_schedules(self, student_id: str):
        """"View past semester schedules"."""
        return self._receiver.schedules.find_all_for(student_id)
