"""Course Catalogue context -- Course, Prerequisite, CourseSection, TimeSlot,
DegreeProgram and CourseChangeRequest.

Diagram 02, COURSE CATALOGUE CONTEXT band.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time

from .enums import ChangeType, DayOfWeek, Semester
from .exceptions import CapacityExceeded, IllegalState


@dataclass(frozen=True)
class Prerequisite:
    """A course that must be completed, at or above a minimum grade."""

    required_course_code: str
    minimum_grade: str = "D"

    def is_satisfied_by(self, record) -> bool:
        """`record` is an AcademicRecord; kept duck-typed to avoid a cycle."""
        return record.has_completed(self.required_course_code, self.minimum_grade)


@dataclass
class Course:
    course_code: str
    title: str
    description: str
    credits: int
    department: str
    school: str = ""
    prerequisites: list[Prerequisite] = field(default_factory=list)

    def get_prerequisites(self) -> list[Prerequisite]:
        return list(self.prerequisites)

    def add_prerequisite(self, prereq: Prerequisite) -> None:
        """Only reached via an approved CourseChangeRequest (diagram 06 p3)."""
        if prereq not in self.prerequisites:
            self.prerequisites.append(prereq)

    def update_description(self, description: str) -> None:
        self.description = description


@dataclass(frozen=True)
class TimeSlot:
    """Composition over inheritance: a section *holds* TimeSlots rather than
    subclassing a "TwiceWeeklySection".  A Mon+Wed course is simply two
    TimeSlot objects -- a data change, not a class change.
    """

    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    location: str = "TBA"

    def overlaps(self, other: TimeSlot) -> bool:
        if self.day_of_week is not other.day_of_week:
            return False
        return self.start_time < other.end_time and other.start_time < self.end_time

    def __str__(self) -> str:  # pragma: no cover - display only
        return (
            f"{self.day_of_week.short} "
            f"{self.start_time:%H:%M}-{self.end_time:%H:%M} @ {self.location}"
        )


@dataclass
class CourseSection:
    """A course offering in one semester.

    ENCAPSULATION EXAMPLE (02-design-principles.md).  `_enrolled_count` is
    private and the invariant 0 <= enrolled <= capacity is enforced here.  No
    caller -- not the facade, not a command, not a repository -- can put a
    section into an impossible state.
    """

    section_id: str
    course_code: str
    semester: Semester
    instructor_id: str
    total_capacity: int
    time_slots: list[TimeSlot] = field(default_factory=list)
    _enrolled_count: int = 0

    @property
    def enrolled_count(self) -> int:
        """Read-only to the outside world -- there is deliberately no setter."""
        return self._enrolled_count

    def available_seats(self) -> int:
        return self.total_capacity - self._enrolled_count

    def has_available_seat(self) -> bool:
        return self.available_seats() > 0

    def occupancy_rate(self) -> float:
        if self.total_capacity == 0:
            return 0.0
        return self._enrolled_count / self.total_capacity

    def reserve_seat(self) -> None:
        """Tell, Don't Ask: callers say "reserve a seat", they do not read the
        counter, increment it and write it back."""
        if not self.has_available_seat():
            raise CapacityExceeded(
                f"Section {self.section_id} is full "
                f"({self._enrolled_count}/{self.total_capacity})"
            )
        self._enrolled_count += 1

    def force_reserve_seat(self) -> None:
        """Take a seat the section does not have.

        The requirement "manually override enrolment rules (e.g. force-add a
        student into a full class)" cannot be met by relaxing a validation rule
        alone: CapacityRule guards the *decision*, while reserve_seat() guards
        the *invariant*, and an over-capacity section violates the invariant by
        definition.  So the bypass gets its own name rather than a boolean
        parameter on reserve_seat() -- a caller cannot exceed capacity by
        accident, and every place that can is greppable.

        Still encapsulated: the counter remains private, `enrolled_count` has no
        setter, and 0 <= enrolled is untouched.  Only the upper bound is waived.
        """
        self._enrolled_count += 1

    def release_seat(self) -> None:
        if self._enrolled_count == 0:
            raise IllegalState(f"Section {self.section_id} has no seats to release")
        self._enrolled_count -= 1

    def change_capacity(self, new_capacity: int) -> None:
        """Only reached via an approved CourseChangeRequest (diagram 06 p3)."""
        if new_capacity < self._enrolled_count:
            raise IllegalState(
                f"Cannot shrink capacity to {new_capacity}: "
                f"{self._enrolled_count} students are already enrolled"
            )
        self.total_capacity = new_capacity

    def schedule_text(self) -> str:
        return "; ".join(str(s) for s in self.time_slots) or "unscheduled"


@dataclass
class DegreeProgram:
    program_id: str
    name: str
    required_credits: int
    required_course_codes: list[str] = field(default_factory=list)

    def get_required_courses(self) -> list[str]:
        return list(self.required_course_codes)

    def remaining_for(self, record) -> list[str]:
        """Academic Progress Tracking: "courses still required for the degree"."""
        completed = {g.course_code for g in record.grades if g.is_passing()}
        return [c for c in self.required_course_codes if c not in completed]


@dataclass
class CourseChangeRequest:
    """Faculty-raised request requiring administrator approval.

    SRP: this is a separate entity rather than approval fields bolted onto
    CourseSection.  A section describes an offering; this tracks a workflow.
    Its lifecycle is modelled by the State pattern -- see
    patterns/state_course_change.py and diagram 06 page 3.
    """

    request_id: str
    section_id: str
    requested_by: str
    change_type: ChangeType
    payload: dict = field(default_factory=dict)
    decided_by: str | None = None
    reason: str | None = None
    # `state` is injected by the State pattern module to avoid an import cycle.
    state: object | None = field(default=None, repr=False)

    # -- Context methods: every one delegates to the current state object. ----
    def submit(self) -> None:
        self.state.submit(self)

    def approve(self, admin_id: str) -> None:
        self.state.approve(self, admin_id)

    def reject(self, reason: str) -> None:
        self.state.reject(self, reason)

    def withdraw(self) -> None:
        self.state.withdraw(self)

    def set_state(self, state) -> None:
        self.state = state

    def state_name(self) -> str:
        return self.state.name()
