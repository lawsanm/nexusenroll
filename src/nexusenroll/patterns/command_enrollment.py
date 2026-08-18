"""
===============================================================================
PATTERN 2 -- COMMAND  «Behavioural»           Diagram 03, zone 2
===============================================================================

ROLE OF THE PATTERN IN THIS SYSTEM
    It satisfies an explicit, hard requirement from the brief:

        "All enrolment operations (adding/dropping a course) must be treated as
         transactions.  This means either the entire operation succeeds (e.g.
         the student is enrolled, the class capacity is updated, and the
         schedule is modified) or the entire operation fails, leaving no
         partial state changes."

GoF ROLES
    Command         -- EnrollmentCommand  (execute / undo / describe)
    ConcreteCommand -- AddCourseCommand, DropCourseCommand
    Receiver        -- EnrolmentReceiver  (owns the repositories being mutated)
    Invoker         -- TransactionManager (runs commands onto a stack)

HOW IT DELIVERS ATOMICITY
    AddCourseCommand.execute() performs exactly the three state changes the
    requirement enumerates, IN ORDER, recording each one as it succeeds.
    undo() reverses them.  TransactionManager.run_atomic() pushes each executed
    command onto a stack and, on any exception, pops the stack calling undo()
    -- so no partial state change survives.

WHY NOT JUST A DATABASE TRANSACTION?
    Both, at different levels.  A DB transaction protects persistence; the
    Command stack protects IN-MEMORY DOMAIN STATE -- a CourseSection whose
    enrolled_count was already incremented, a StudentSchedule already mutated.
    In this proof-of-concept there is no database at all, so the Command
    rollback *is* the transaction, which is what makes it demonstrable live.

BONUS CAPABILITY
    describe() gives the administrator module a replayable audit log for free.

WITHOUT IT
    Rollback logic hand-written inline in a try/except, duplicated between add
    and drop, and silently incomplete the first time a fourth state change is
    added.
"""

from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..domain.enrollment import Enrollment, EnrollmentRequest, StudentSchedule
from ..domain.enums import EnrollmentStatus
from ..repositories.interfaces import (
    IEnrollmentRepository,
    IScheduleRepository,
    ISectionRepository,
)

_enrolment_ids = itertools.count(1)


class EnrolmentReceiver:
    """RECEIVER.  Owns the three pieces of state named in the requirement, so a
    command never touches a repository directly.

    Keeping the receiver separate means the commands stay tiny and readable --
    they express *what* changes, in what order, and how to reverse it.
    """

    def __init__(
        self,
        enrol_repo: IEnrollmentRepository,
        section_repo: ISectionRepository,
        schedule_repo: IScheduleRepository,
    ) -> None:
        self.enrolments = enrol_repo
        self.sections = section_repo
        self.schedules = schedule_repo

    def schedule_for(self, student_id: str, semester) -> StudentSchedule:
        schedule = self.schedules.find(student_id, semester)
        if schedule is None:
            schedule = StudentSchedule(student_id, semester)
            self.schedules.save(schedule)
        return schedule


# ---------------------------------------------------------------------------
# Command interface
# ---------------------------------------------------------------------------
class EnrollmentCommand(ABC):
    """COMMAND.  Three methods, no more -- another Interface Segregation
    example.  Anything that can be executed, reversed and described qualifies.
    """

    @abstractmethod
    def execute(self) -> None:
        """Perform the state changes, recording enough to reverse them."""

    @abstractmethod
    def undo(self) -> None:
        """Reverse whatever execute() actually completed -- and only that."""

    @abstractmethod
    def describe(self) -> str:
        """Human-readable line for the audit log."""


# ---------------------------------------------------------------------------
# Concrete commands
# ---------------------------------------------------------------------------
class AddCourseCommand(EnrollmentCommand):
    """The three numbered steps below are exactly the three state changes the
    transaction requirement names.  `_completed_steps` is what makes undo()
    correct when execute() fails PART WAY THROUGH -- we reverse only the steps
    that actually happened.
    """

    def __init__(
        self,
        request: EnrollmentRequest,
        receiver: EnrolmentReceiver,
        semester,
        fail_on_step: int | None = None,
    ) -> None:
        self._request = request
        self._receiver = receiver
        self._semester = semester
        self._enrolment: Enrollment | None = None
        self._section = None
        self._schedule: StudentSchedule | None = None
        self._completed_steps: list[int] = []
        # Test seam used by the screencast demo to force a failure at step 3
        # and prove the rollback. Production code never sets this.
        self._fail_on_step = fail_on_step

    def describe(self) -> str:
        # An over-capacity force-add is exactly the entry an administrator
        # wants to find later, so the audit line says so.
        suffix = ", ADMIN OVERRIDE" if self._request.is_override() else ""
        return (
            f"AddCourse(student={self._request.student_id}, "
            f"section={self._request.section_id}{suffix})"
        )

    def _maybe_fail(self, step: int) -> None:
        from ..domain.exceptions import TransactionFailed

        if self._fail_on_step == step:
            raise TransactionFailed(
                f"Injected failure at step {step} of {self.describe()}"
            )

    def execute(self) -> None:
        self._section = self._receiver.sections.find(self._request.section_id)
        self._schedule = self._receiver.schedule_for(
            self._request.student_id, self._semester
        )

        # -- step 1: "the student is enrolled" ------------------------------
        self._maybe_fail(1)
        self._enrolment = Enrollment(
            enrollment_id=f"ENR-{next(_enrolment_ids):04d}",
            student_id=self._request.student_id,
            section_id=self._request.section_id,
            status=EnrollmentStatus.ENROLLED,
        )
        self._receiver.enrolments.save(self._enrolment)
        self._completed_steps.append(1)

        # -- step 2: "the class capacity is updated" ------------------------
        # An administrator override skipped CapacityRule at validation time,
        # but the section still enforces its own invariant -- so the override
        # has to be honoured HERE too, or the transaction fails at step 2 and
        # rolls back a force-add that was deliberately authorised.
        self._maybe_fail(2)
        if self._request.is_override():
            self._section.force_reserve_seat()
        else:
            self._section.reserve_seat()
        self._completed_steps.append(2)

        # -- step 3: "the schedule is modified" -----------------------------
        self._maybe_fail(3)
        self._schedule.add_section(self._section)
        self._receiver.schedules.save(self._schedule)
        self._completed_steps.append(3)

    def undo(self) -> None:
        """Reverse in the opposite order: 3 -> 2 -> 1."""
        if 3 in self._completed_steps:
            self._schedule.remove_section(self._section)
            self._receiver.schedules.save(self._schedule)
        if 2 in self._completed_steps:
            self._section.release_seat()
        if 1 in self._completed_steps and self._enrolment is not None:
            self._receiver.enrolments.delete(self._enrolment.enrollment_id)
        self._completed_steps.clear()

    @property
    def enrolment(self) -> Enrollment | None:
        return self._enrolment


class DropCourseCommand(EnrollmentCommand):
    """Mirror image of AddCourseCommand.

    Note what is NOT here: no event is published inside execute().  Publishing
    happens in the Facade AFTER the transaction commits, because a notification
    must never be part of -- or able to fail -- the transaction.  See diagram 05
    page 2, where the red boundary sits between commit and dispatch.
    """

    def __init__(
        self,
        student_id: str,
        section_id: str,
        receiver: EnrolmentReceiver,
        semester,
    ) -> None:
        self._student_id = student_id
        self._section_id = section_id
        self._receiver = receiver
        self._semester = semester
        self._enrolment: Enrollment | None = None
        self._previous_status: EnrollmentStatus | None = None
        self._section = None
        self._schedule: StudentSchedule | None = None
        self._completed_steps: list[int] = []

    def describe(self) -> str:
        return f"DropCourse(student={self._student_id}, section={self._section_id})"

    def execute(self) -> None:
        matches = [
            e
            for e in self._receiver.enrolments.find_by_student(self._student_id)
            if e.section_id == self._section_id and e.is_active()
        ]
        if not matches:
            raise LookupError(
                f"{self._student_id} has no active enrolment in {self._section_id}"
            )

        self._enrolment = matches[0]
        self._section = self._receiver.sections.find(self._section_id)
        self._schedule = self._receiver.schedule_for(self._student_id, self._semester)

        # Snapshot taken BEFORE any mutation, so undo() can restore exactly.
        self._previous_status = self._enrolment.status

        self._enrolment.drop()                       # 1. enrolment.drop()
        self._receiver.enrolments.save(self._enrolment)
        self._completed_steps.append(1)

        self._section.release_seat()                 # 2. section.releaseSeat()
        self._completed_steps.append(2)

        self._schedule.remove_section(self._section)  # 3. schedule.removeSection()
        self._receiver.schedules.save(self._schedule)
        self._completed_steps.append(3)

    def undo(self) -> None:
        if 3 in self._completed_steps:
            self._schedule.add_section(self._section)
            self._receiver.schedules.save(self._schedule)
        if 2 in self._completed_steps:
            # Restoring the seat this command released, not competing for a new
            # one -- so it must always succeed.  reserve_seat() would refuse on
            # a section that a force-add had pushed over capacity, and an
            # exception raised during rollback strands the partial state that
            # rollback exists to remove.
            self._section.force_reserve_seat()
        if 1 in self._completed_steps and self._previous_status is not None:
            self._enrolment.status = self._previous_status
            self._receiver.enrolments.save(self._enrolment)
        self._completed_steps.clear()


# ---------------------------------------------------------------------------
# Invoker
# ---------------------------------------------------------------------------
@dataclass
class TxResult:
    """What run_atomic() reports back to the Facade."""

    success: bool
    message: str = ""
    commands: tuple[EnrollmentCommand, ...] = ()

    def __bool__(self) -> bool:
        return self.success


class TransactionManager:
    """INVOKER.

    SINGLE RESPONSIBILITY: this class guarantees atomicity and does nothing
    else.  It has no idea what an enrolment is -- it only knows that commands
    can be executed and undone.  That is why the same manager would serve a
    future "swap section" or "transfer programme" operation unchanged.
    """

    def __init__(self) -> None:
        self._audit_log: list[str] = []

    def run_atomic(self, commands: list[EnrollmentCommand]) -> TxResult:
        """Execute every command, or leave the system exactly as it was found.

        This method IS the "all-or-nothing" requirement, in nine lines.
        """
        executed: list[EnrollmentCommand] = []  # the stack
        try:
            for command in commands:
                # PUSH BEFORE EXECUTING.  A command that fails PART WAY through
                # has still changed some state, so it must be on the stack to be
                # undone.  Pushing only after success would strand exactly the
                # partial changes this method exists to prevent.  undo() is safe
                # to call either way because each command reverses only the
                # steps it recorded as completed.
                executed.append(command)
                command.execute()
        except Exception as exc:                  # noqa: BLE001 - any failure rolls back
            self._rollback_all(executed)
            return TxResult(False, f"rolled back: {exc}")

        self._audit_log.extend(c.describe() for c in executed)
        return TxResult(True, "committed", tuple(executed))

    def _rollback_all(self, executed: list[EnrollmentCommand]) -> None:
        """Pop the stack, calling undo() on each already-executed command in
        REVERSE order.  Reverse order matters: releasing a seat before removing
        the schedule entry would leave the two inconsistent midway."""
        while executed:
            executed.pop().undo()

    def audit_log(self) -> list[str]:
        """The free audit trail: a replayable history of who changed what."""
        return list(self._audit_log)
