"""
===============================================================================
PATTERN 4 -- OBSERVER  «Behavioural»          Diagram 03, zone 4
===============================================================================

ROLE OF THE PATTERN IN THIS SYSTEM
    The brief does not merely ask for notifications -- it names the design
    property it wants:

        "A student drops a course.  The notification system must automatically
         alert any waitlisted students that a spot has opened up.  This process
         should be automated and DECOUPLED from the core enrolment logic."

    Observer is what makes the word "decoupled" true rather than aspirational.
    The Enrolment Service publishes one event and returns.  It holds no
    reference to any subscriber and never learns whether delivery succeeded.

GoF ROLES
    Subject          -- NotificationPublisher
    Observer         -- EventObserver  (interface)
    ConcreteObserver -- WaitlistObserver, AdvisorObserver, AdminAlertObserver

REQUIREMENT -> OBSERVER -> TRIGGERING EVENT
    "notified when a waitlisted course becomes available"  WaitlistObserver   <- SeatReleased
    "advisors notified when an advisee drops a critical course"
                                                           AdvisorObserver    <- StudentDropped
    "administrators notified of any system-wide errors"    AdminAlertObserver <- SystemError

    A drop therefore publishes BOTH SeatReleased and StudentDropped: one drives
    the waitlist alert, the other the advisor alert.  (Diagram 05 page 2.)

THE ARCHITECTURAL PAYOFF
    This is also how the future financial aid system integrates: it subscribes
    to StudentEnrolled and gets what it needs with ZERO lines changed in the
    Enrolment Service.  Observer at class level and event-driven messaging at
    architecture level are the same idea at two scales.

FAULT ISOLATION
    publish() catches and logs per observer.  A dead mail server cannot fail an
    enrolment that has already committed.

WITHOUT IT
    EnrollmentFacade calling email_service.send(...) three times inline: adding
    a recipient means editing enrolment code, a mail timeout fails the
    enrolment, and "decoupled" is simply not satisfied.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.enums import EventType
from ..domain.events import DomainEvent
from ..repositories.interfaces import (
    ICourseRepository,
    IProgramRepository,
    IUserRepository,
    IWaitlistRepository,
)


# ---------------------------------------------------------------------------
# Delivery channel -- a second, small abstraction so observers do not hard-code
# "email".  Adding SMS later is a new class and zero observer changes.
# ---------------------------------------------------------------------------
class NotificationChannel(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, body: str) -> None: ...


class EmailChannel(NotificationChannel):
    """Stand-in for an SMTP adapter.  Prints so the screencast can show the
    notification actually firing."""

    def __init__(self, sink: list[str] | None = None) -> None:
        self.sent: list[str] = sink if sink is not None else []

    def send(self, to: str, subject: str, body: str) -> None:
        line = f"EMAIL -> {to} | {subject} | {body}"
        self.sent.append(line)
        print(f"        [notification] {line}")


class FailingChannel(NotificationChannel):
    """Used in the demo to prove FAULT ISOLATION: one observer blowing up does
    not stop the others and cannot fail the committed enrolment."""

    def send(self, to: str, subject: str, body: str) -> None:
        raise ConnectionError("SMTP server unreachable")


# ---------------------------------------------------------------------------
# Observer interface
# ---------------------------------------------------------------------------
class EventObserver(ABC):
    @abstractmethod
    def on_event(self, event: DomainEvent) -> None: ...

    @abstractmethod
    def interested_in(self) -> set[EventType]: ...


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------
class NotificationPublisher:
    """SUBJECT.

    Note what this class does NOT contain: any enrolment logic, any knowledge
    of what a course or a student is, and any reference to a concrete observer
    class.  It only maps event types to subscribers and dispatches.

    Exactly one instance of this exists at runtime.  That guarantee comes from
    the COMPOSITION ROOT in composition_root.py -- not from a Singleton.  See
    01-design-patterns.md section 6 for why we rejected the pattern.
    """

    def __init__(self) -> None:
        self._observers: dict[EventType, list[EventObserver]] = {}
        self.error_log: list[str] = []

    def attach(self, event_type: EventType, observer: EventObserver) -> None:
        self._observers.setdefault(event_type, []).append(observer)

    def detach(self, event_type: EventType, observer: EventObserver) -> None:
        if observer in self._observers.get(event_type, []):
            self._observers[event_type].remove(observer)

    def subscriber_count(self, event_type: EventType) -> int:
        return len(self._observers.get(event_type, []))

    def publish(self, event: DomainEvent) -> None:
        """Fire-and-forget.  Returns None -- the caller learns nothing about
        delivery, which is the whole point of "decoupled".

        FAULT ISOLATION: each observer is called inside its own try/except, so
        one failure is logged and the remaining observers still run.
        """
        for observer in list(self._observers.get(event.event_type, [])):
            try:
                observer.on_event(event)
            except Exception as exc:  # noqa: BLE001 - deliberately swallowed
                message = f"{type(observer).__name__} failed on {event}: {exc}"
                self.error_log.append(message)
                print(f"        [isolated failure] {message}")


# ---------------------------------------------------------------------------
# Concrete observers -- one per notification requirement
# ---------------------------------------------------------------------------
class WaitlistObserver(EventObserver):
    """"Students should be notified when a course they are waitlisted for
    becomes available."  Triggered by SeatReleased."""

    def __init__(
        self,
        channel: NotificationChannel,
        waitlist_repo: IWaitlistRepository,
        user_repo: IUserRepository,
    ) -> None:
        self._channel = channel
        self._waitlists = waitlist_repo
        self._users = user_repo

    def interested_in(self) -> set[EventType]:
        return {EventType.SEAT_RELEASED}

    def on_event(self, event: DomainEvent) -> None:
        section_id = event.get("section_id")
        course_code = event.get("course_code", section_id)
        waitlist = self._waitlists.for_section(section_id)
        next_student_id = waitlist.pop_next()
        if next_student_id is None:
            return
        student = self._users.find(next_student_id)
        if student is None:
            return
        self._channel.send(
            student.email,
            f"A spot has opened up in {course_code}",
            f"{student.get_full_name()}, a seat is now free in {section_id}. "
            "You have 24 hours to claim it.",
        )


class AdvisorObserver(EventObserver):
    """"Advisors should be notified when one of their advisees drops a critical
    course."  Triggered by StudentDropped, guarded on degree-criticality."""

    def __init__(
        self,
        channel: NotificationChannel,
        user_repo: IUserRepository,
        program_repo: IProgramRepository,
        course_repo: ICourseRepository,
    ) -> None:
        self._channel = channel
        self._users = user_repo
        self._programs = program_repo
        self._courses = course_repo

    def interested_in(self) -> set[EventType]:
        return {EventType.STUDENT_DROPPED}

    def _is_degree_critical(self, student, course_code: str) -> bool:
        program = self._programs.find(getattr(student, "program_id", ""))
        return bool(program) and course_code in program.get_required_courses()

    def on_event(self, event: DomainEvent) -> None:
        student = self._users.find(event.get("student_id"))
        if student is None:
            return
        course_code = event.get("course_code", "")
        if not self._is_degree_critical(student, course_code):
            return  # the guard: only *critical* drops reach an advisor
        advisor = self._users.find(getattr(student, "advisor_id", None) or "")
        if advisor is None:
            return
        self._channel.send(
            advisor.email,
            "Advisee dropped a critical course",
            f"{student.get_full_name()} has dropped {course_code}, which is "
            "required for their degree programme.",
        )


class AdminAlertObserver(EventObserver):
    """"Administrators should be notified of any system-wide errors."
    Triggered by SystemError."""

    def __init__(self, channel: NotificationChannel, user_repo: IUserRepository) -> None:
        self._channel = channel
        self._users = user_repo

    def interested_in(self) -> set[EventType]:
        return {EventType.SYSTEM_ERROR}

    def on_event(self, event: DomainEvent) -> None:
        from ..domain.people import Administrator

        for person in self._users.all():
            if isinstance(person, Administrator) and person.is_active:
                self._channel.send(
                    person.email,
                    f"System error: {event.get('source', 'unknown')}",
                    str(event.get("detail", "")),
                )


class AuditObserver(EventObserver):
    """Proof that a NEW subscriber costs zero enrolment-code changes.

    This observer -- a stand-in for the future financial aid system named in the
    brief -- was added after the enrolment logic was complete.  It subscribes in
    composition_root.py and nothing else in the system knows it exists.  Open/Closed at
    runtime.
    """

    def __init__(self, watching: set[EventType]) -> None:
        self._watching = watching
        self.seen: list[DomainEvent] = []

    def interested_in(self) -> set[EventType]:
        return set(self._watching)

    def on_event(self, event: DomainEvent) -> None:
        self.seen.append(event)
