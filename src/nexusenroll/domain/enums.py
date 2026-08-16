"""Enumerations shared across the business logic tier.

These are the enumerations that appear on diagram 02 (domain model) and
diagram 06 (state diagrams).  Keeping them in one module means the rest of the
business logic never compares raw strings.
"""

from enum import Enum


class Role(Enum):
    """Role of a Person. Diagram 02 -- Person.getRole()."""

    STUDENT = "Student"
    FACULTY = "Faculty"
    ADMINISTRATOR = "Administrator"


class AcademicStanding(Enum):
    GOOD = "Good"
    PROBATION = "Probation"
    SUSPENDED = "Suspended"


class Semester(Enum):
    """Ordered so that "semester not in the past" is a simple comparison."""

    SPRING_2026 = (2026, 1, "Spring 2026")
    FALL_2026 = (2026, 2, "Fall 2026")
    SPRING_2027 = (2027, 1, "Spring 2027")

    def __init__(self, year: int, term: int, label: str) -> None:
        self.year = year
        self.term = term
        self.label = label

    @property
    def ordinal(self) -> int:
        return self.year * 10 + self.term

    def __str__(self) -> str:  # pragma: no cover - display only
        return self.label


class DayOfWeek(Enum):
    MON = "Monday"
    TUE = "Tuesday"
    WED = "Wednesday"
    THU = "Thursday"
    FRI = "Friday"

    @property
    def short(self) -> str:
        return self.name.title()


class EnrollmentStatus(Enum):
    """Diagram 02 «enumeration» EnrollmentStatus; lifecycle on diagram 06 page 2."""

    PENDING = "Pending"
    ENROLLED = "Enrolled"
    WAITLISTED = "Waitlisted"
    DROPPED = "Dropped"
    COMPLETED = "Completed"


class EventType(Enum):
    """Topics carried by the Message Broker on diagram 01.

    Observer (pattern 4) subscribes per topic: a drop publishes *both*
    SEAT_RELEASED (which drives the waitlist alert) and STUDENT_DROPPED (which
    drives the advisor alert).
    """

    STUDENT_ENROLLED = "StudentEnrolled"
    STUDENT_DROPPED = "StudentDropped"
    SEAT_RELEASED = "SeatReleased"
    GRADES_SUBMITTED = "GradesSubmitted"
    COURSE_CHANGED = "CourseChanged"
    SYSTEM_ERROR = "SystemError"


class ChangeType(Enum):
    """Diagram 06 page 3 -- what a CourseChangeRequest is asking to change."""

    DESCRIPTION = "Update description"
    ADD_PREREQUISITE = "Add prerequisite"
    CAPACITY = "Change capacity"


class ReportType(Enum):
    """Product kinds the Factory Method (pattern 5) can create."""

    ENROLMENT_STATISTICS = "Enrolment statistics by department and semester"
    FACULTY_WORKLOAD = "Faculty workload"
    COURSE_POPULARITY = "Course popularity trends"
    CAPACITY_THRESHOLD = "Courses over a capacity threshold"
