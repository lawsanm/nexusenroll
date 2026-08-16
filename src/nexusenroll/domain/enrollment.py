"""Enrolment context -- EnrollmentRequest, ValidationResult, Enrollment,
StudentSchedule and Waitlist.

Diagram 02, ENROLMENT CONTEXT band.  Lifecycle on diagram 06 page 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .catalog import CourseSection, TimeSlot
from .enums import EnrollmentStatus, Semester


@dataclass
class EnrollmentRequest:
    """What the Facade builds from an API call and hands to the validator."""

    student_id: str
    section_id: str
    is_admin_override: bool = False

    def is_override(self) -> bool:
        return self.is_admin_override


@dataclass
class ValidationResult:
    """Aggregates failures from *every* Strategy rule.

    This is why Strategy beat Decorator (01-design-patterns.md section 6): a
    decorator chain short-circuits at the first failure, but the requirement
    benefits from telling the student every problem at once.
    """

    errors: list[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        return not self.errors

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def merge(self, other: ValidationResult) -> None:
        self.errors.extend(other.errors)

    @classmethod
    def ok(cls) -> ValidationResult:
        return cls()

    @classmethod
    def failure(cls, message: str) -> ValidationResult:
        return cls([message])

    def __str__(self) -> str:  # pragma: no cover - display only
        return "OK" if self.is_valid() else "; ".join(self.errors)


@dataclass
class Enrollment:
    enrollment_id: str
    student_id: str
    section_id: str
    enrolled_on: datetime = field(default_factory=datetime.now)
    status: EnrollmentStatus = EnrollmentStatus.PENDING

    def confirm(self) -> None:
        self.status = EnrollmentStatus.ENROLLED

    def drop(self) -> None:
        self.status = EnrollmentStatus.DROPPED

    def waitlist(self) -> None:
        self.status = EnrollmentStatus.WAITLISTED

    def complete(self) -> None:
        self.status = EnrollmentStatus.COMPLETED

    def is_active(self) -> bool:
        return self.status is EnrollmentStatus.ENROLLED


@dataclass
class StudentSchedule:
    """One semester of sections for one student.

    Mutated *only* from inside a Command (pattern 2) so that every change to it
    is undoable -- it is one of the three pieces of state named in the
    transaction requirement.
    """

    student_id: str
    semester: Semester
    sections: list[CourseSection] = field(default_factory=list)

    def add_section(self, section: CourseSection) -> None:
        self.sections.append(section)

    def remove_section(self, section: CourseSection) -> None:
        if section in self.sections:
            self.sections.remove(section)

    def all_time_slots(self) -> list[TimeSlot]:
        return [slot for s in self.sections for slot in s.time_slots]

    def has_conflict_with(self, slots: list[TimeSlot]) -> TimeSlot | None:
        """Returns the first clashing slot already on the schedule, or None."""
        for mine in self.all_time_slots():
            for theirs in slots:
                if mine.overlaps(theirs):
                    return mine
        return None

    def total_credits(self, credits_of) -> int:
        return sum(credits_of(s.course_code) for s in self.sections)

    def as_calendar_view(self) -> dict[str, list[str]]:
        """"Dynamically build and display a calendar-like view of classes"."""
        calendar: dict[str, list[str]] = {}
        for section in self.sections:
            for slot in section.time_slots:
                day = calendar.setdefault(slot.day_of_week.short, [])
                day.append(
                    f"{slot.start_time:%H:%M}-{slot.end_time:%H:%M}  "
                    f"{section.course_code} ({section.section_id}) @ {slot.location}"
                )
        for entries in calendar.values():
            entries.sort()
        return calendar


@dataclass
class Waitlist:
    """FIFO queue per section.  Fed when the capacity rule is the *only*
    failure -- see the Waitlist branch on diagram 04 page 1.
    """

    section_id: str
    queue: list[str] = field(default_factory=list)

    def add(self, student_id: str) -> int:
        if student_id not in self.queue:
            self.queue.append(student_id)
        return self.position_of(student_id)

    def pop_next(self) -> str | None:
        return self.queue.pop(0) if self.queue else None

    def position_of(self, student_id: str) -> int:
        return self.queue.index(student_id) + 1 if student_id in self.queue else -1

    def is_empty(self) -> bool:
        return not self.queue
