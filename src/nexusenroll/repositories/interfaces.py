"""Repository interfaces -- DEPENDENCY INVERSION PRINCIPLE in one file.

These abstractions are *declared in the business logic layer* (this package
lives above the data access layer, not below it).  The data access layer
implements them.  High-level enrolment policy therefore never depends on a
low-level persistence detail; both depend on an abstraction that the policy
owns.  See diagram 03 zone 6 and 02-design-principles.md section D.

They are also the INTERFACE SEGREGATION example: each interface carries only
the handful of operations its clients actually call.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.catalog import Course, CourseChangeRequest, CourseSection, DegreeProgram
from ..domain.enrollment import Enrollment, StudentSchedule, Waitlist
from ..domain.people import Person
from ..domain.records import AcademicRecord, GradeSubmission


class IEnrollmentRepository(ABC):
    @abstractmethod
    def save(self, enrollment: Enrollment) -> None: ...

    @abstractmethod
    def find(self, enrollment_id: str) -> Enrollment | None: ...

    @abstractmethod
    def find_by_student(self, student_id: str) -> list[Enrollment]:
        """LSP contract: returns an empty list -- never None -- when nothing
        matches.  Every implementation must honour this, otherwise callers
        would have to know which implementation they were given."""

    @abstractmethod
    def find_by_section(self, section_id: str) -> list[Enrollment]: ...

    @abstractmethod
    def delete(self, enrollment_id: str) -> None: ...


class ISectionRepository(ABC):
    @abstractmethod
    def save(self, section: CourseSection) -> None: ...

    @abstractmethod
    def find(self, section_id: str) -> CourseSection | None: ...

    @abstractmethod
    def all(self) -> list[CourseSection]: ...

    @abstractmethod
    def find_by_instructor(self, instructor_id: str) -> list[CourseSection]: ...


class ICourseRepository(ABC):
    @abstractmethod
    def save(self, course: Course) -> None: ...

    @abstractmethod
    def find(self, course_code: str) -> Course | None: ...

    @abstractmethod
    def all(self) -> list[Course]: ...

    @abstractmethod
    def delete(self, course_code: str) -> None: ...


class IProgramRepository(ABC):
    @abstractmethod
    def save(self, program: DegreeProgram) -> None: ...

    @abstractmethod
    def find(self, program_id: str) -> DegreeProgram | None: ...

    @abstractmethod
    def all(self) -> list[DegreeProgram]: ...


class IScheduleRepository(ABC):
    @abstractmethod
    def save(self, schedule: StudentSchedule) -> None: ...

    @abstractmethod
    def find(self, student_id: str, semester) -> StudentSchedule | None: ...

    @abstractmethod
    def find_all_for(self, student_id: str) -> list[StudentSchedule]:
        """Backs "view past semester schedules"."""


class IRecordRepository(ABC):
    @abstractmethod
    def save(self, record: AcademicRecord) -> None: ...

    @abstractmethod
    def find(self, student_id: str) -> AcademicRecord | None: ...


class IUserRepository(ABC):
    @abstractmethod
    def save(self, person: Person) -> None: ...

    @abstractmethod
    def find(self, person_id: str) -> Person | None: ...

    @abstractmethod
    def all(self) -> list[Person]: ...

    @abstractmethod
    def delete(self, person_id: str) -> None: ...


class IWaitlistRepository(ABC):
    @abstractmethod
    def for_section(self, section_id: str) -> Waitlist:
        """Never returns None -- creates an empty Waitlist on first access."""


class IGradeSubmissionRepository(ABC):
    @abstractmethod
    def save(self, submission: GradeSubmission) -> None: ...

    @abstractmethod
    def find(self, submission_id: str) -> GradeSubmission | None: ...

    @abstractmethod
    def all(self) -> list[GradeSubmission]: ...


class IChangeRequestRepository(ABC):
    @abstractmethod
    def save(self, request: CourseChangeRequest) -> None: ...

    @abstractmethod
    def find(self, request_id: str) -> CourseChangeRequest | None: ...

    @abstractmethod
    def all(self) -> list[CourseChangeRequest]: ...
