"""
===============================================================================
PATTERN 3 (SECOND APPLICATION) -- STATE       Diagram 06, page 3
===============================================================================

ROLE OF THE PATTERN IN THIS SYSTEM
        "Instructors can submit requests to update course descriptions, add
         prerequisites, or change course capacity (these requests must be
         approved by an administrator)."

    CourseChangeRequest has the same Draft -> Pending -> terminal shape as
    GradeSubmission, so the SAME PATTERN is applied a second time with a
    different ConcreteState family.  That is DRY operating at the DESIGN level
    rather than the code level: one design idea serving two workflows.

GoF ROLES
    Context       -- CourseChangeRequest (in domain/catalog.py)
    State         -- RequestState  (this file)
    ConcreteState -- DraftRequestState, PendingAdminApprovalState,
                     ApprovedState, RejectedState, WithdrawnState

THE KEY DESIGN POINT
    The live CourseSection is mutated ONLY on entry to ApprovedState.  While a
    request sits in PendingAdminApproval the published catalogue is unaffected,
    so students never see a capacity or prerequisite that has not been
    authorised.  That is the whole point of "must be approved by an
    administrator", and it is enforced structurally rather than by convention.
"""

from __future__ import annotations

from abc import ABC

from ..domain.catalog import CourseChangeRequest, Prerequisite
from ..domain.enums import ChangeType, EventType
from ..domain.events import DomainEvent
from ..domain.exceptions import IllegalTransition


class RequestState(ABC):
    """Same shape as GradeState: defaults refuse, ConcreteStates permit."""

    def name(self) -> str:
        return type(self).__name__

    def _refuse(self, operation: str) -> None:
        raise IllegalTransition(
            f"{operation}() is not legal while the request is in {self.name()}"
        )

    def submit(self, ctx: CourseChangeRequest) -> None:
        self._refuse("submit")

    def approve(self, ctx: CourseChangeRequest, admin_id: str) -> None:
        self._refuse("approve")

    def reject(self, ctx: CourseChangeRequest, reason: str) -> None:
        self._refuse("reject")

    def withdraw(self, ctx: CourseChangeRequest) -> None:
        self._refuse("withdraw")


class DraftRequestState(RequestState):
    """Faculty is still editing.  Legal: submit, withdraw."""

    def submit(self, ctx: CourseChangeRequest) -> None:
        ctx.set_state(PendingAdminApprovalState())

    def withdraw(self, ctx: CourseChangeRequest) -> None:
        ctx.set_state(WithdrawnState())


class PendingAdminApprovalState(RequestState):
    """Awaiting an administrator decision.  The live section is NOT touched
    while we sit here.  Legal: approve, reject, withdraw."""

    def approve(self, ctx: CourseChangeRequest, admin_id: str) -> None:
        ctx.decided_by = admin_id
        ctx.set_state(ApprovedState())

    def reject(self, ctx: CourseChangeRequest, reason: str) -> None:
        ctx.reason = reason
        ctx.set_state(RejectedState())

    def withdraw(self, ctx: CourseChangeRequest) -> None:
        ctx.set_state(WithdrawnState())


class ApprovedState(RequestState):
    """Terminal.  The change is applied to the live CourseSection by
    `CourseChangeService.apply_if_approved()` on entry to this state."""


class RejectedState(RequestState):
    """Terminal.  The live section is unchanged; the reason is stored."""


class WithdrawnState(RequestState):
    """Terminal.  Faculty pulled the request before a decision."""


def new_change_request(
    request_id: str,
    section_id: str,
    requested_by: str,
    change_type: ChangeType,
    payload: dict,
) -> CourseChangeRequest:
    """Initial pseudostate of diagram 06 page 3."""
    request = CourseChangeRequest(
        request_id, section_id, requested_by, change_type, payload
    )
    request.set_state(DraftRequestState())
    return request


class CourseChangeService:
    """Applies an approved request to the live catalogue.

    Kept OUT of the state classes deliberately: a state's job is to decide
    which transitions are legal, not to know about repositories.  Single
    Responsibility at the class level.
    """

    def __init__(self, section_repo, course_repo, publisher=None) -> None:
        self._sections = section_repo
        self._courses = course_repo
        self._publisher = publisher

    def apply_if_approved(self, request: CourseChangeRequest) -> str:
        if not isinstance(request.state, ApprovedState):
            return f"not applied - request is in {request.state_name()}"

        section = self._sections.find(request.section_id)
        if section is None:
            return "not applied - unknown section"
        course = self._courses.find(section.course_code)

        if request.change_type is ChangeType.CAPACITY:
            old = section.total_capacity
            new = int(request.payload["capacity"])
            section.change_capacity(new)
            self._sections.save(section)
            outcome = f"capacity {old} -> {new}"
            # A capacity INCREASE releases seats, so the existing
            # WaitlistObserver picks it up with no extra code -- two
            # independently designed features composing because both are
            # event-driven.
            if new > old and self._publisher is not None:
                self._publisher.publish(
                    DomainEvent(
                        EventType.SEAT_RELEASED,
                        {
                            "section_id": section.section_id,
                            "course_code": section.course_code,
                        },
                    )
                )
        elif request.change_type is ChangeType.DESCRIPTION:
            course.update_description(request.payload["description"])
            self._courses.save(course)
            outcome = "description updated"
        elif request.change_type is ChangeType.ADD_PREREQUISITE:
            course.add_prerequisite(
                Prerequisite(
                    request.payload["course_code"],
                    request.payload.get("minimum_grade", "D"),
                )
            )
            self._courses.save(course)
            outcome = f"prerequisite {request.payload['course_code']} added"
        else:  # pragma: no cover - ChangeType is exhaustive above
            outcome = "unknown change type"

        if self._publisher is not None:
            self._publisher.publish(
                DomainEvent(
                    EventType.COURSE_CHANGED,
                    {"section_id": section.section_id, "outcome": outcome},
                )
            )
        return outcome
