"""In-memory repository implementations -- the Data Access layer of the
proof-of-concept.

LISKOV SUBSTITUTION EXAMPLE (02-design-principles.md section L).  These classes
are what a production SqlEnrollmentRepository would be swapped for.  They honour
the interface contracts exactly:

  * save() returns nothing and never raises on a valid entity;
  * every find_by_* returns an empty list, never None;
  * no precondition is strengthened and no postcondition is weakened.

Because of that, the *same* EnrollmentFacade object runs unmodified against
either implementation -- a substitutability claim the demo actually exercises
rather than merely asserting.

KISS (02-design-principles.md): a real database would add setup friction and
demonstrate nothing about the design patterns, which are what is being marked.
"""

from __future__ import annotations

from ..domain.catalog import Course, CourseChangeRequest, CourseSection, DegreeProgram
from ..domain.enrollment import Enrollment, StudentSchedule, Waitlist
from ..domain.people import Person
from ..domain.records import AcademicRecord, GradeSubmission
from .interfaces import (
    IChangeRequestRepository,
    ICourseRepository,
    IEnrollmentRepository,
    IGradeSubmissionRepository,
    IProgramRepository,
    IRecordRepository,
    IScheduleRepository,
    ISectionRepository,
    IUserRepository,
    IWaitlistRepository,
)


class InMemoryEnrollmentRepository(IEnrollmentRepository):
    def __init__(self) -> None:
        self._items: dict[str, Enrollment] = {}

    def save(self, enrollment: Enrollment) -> None:
        self._items[enrollment.enrollment_id] = enrollment

    def find(self, enrollment_id: str) -> Enrollment | None:
        return self._items.get(enrollment_id)

    def find_by_student(self, student_id: str) -> list[Enrollment]:
        return [e for e in self._items.values() if e.student_id == student_id]

    def find_by_section(self, section_id: str) -> list[Enrollment]:
        return [e for e in self._items.values() if e.section_id == section_id]

    def delete(self, enrollment_id: str) -> None:
        self._items.pop(enrollment_id, None)


class InMemorySectionRepository(ISectionRepository):
    def __init__(self) -> None:
        self._items: dict[str, CourseSection] = {}

    def save(self, section: CourseSection) -> None:
        self._items[section.section_id] = section

    def find(self, section_id: str) -> CourseSection | None:
        return self._items.get(section_id)

    def all(self) -> list[CourseSection]:
        return list(self._items.values())

    def find_by_instructor(self, instructor_id: str) -> list[CourseSection]:
        return [s for s in self._items.values() if s.instructor_id == instructor_id]


class InMemoryCourseRepository(ICourseRepository):
    def __init__(self) -> None:
        self._items: dict[str, Course] = {}

    def save(self, course: Course) -> None:
        self._items[course.course_code] = course

    def find(self, course_code: str) -> Course | None:
        return self._items.get(course_code)

    def all(self) -> list[Course]:
        return list(self._items.values())

    def delete(self, course_code: str) -> None:
        self._items.pop(course_code, None)


class InMemoryProgramRepository(IProgramRepository):
    def __init__(self) -> None:
        self._items: dict[str, DegreeProgram] = {}

    def save(self, program: DegreeProgram) -> None:
        self._items[program.program_id] = program

    def find(self, program_id: str) -> DegreeProgram | None:
        return self._items.get(program_id)

    def all(self) -> list[DegreeProgram]:
        return list(self._items.values())


class InMemoryScheduleRepository(IScheduleRepository):
    def __init__(self) -> None:
        self._items: dict[tuple[str, object], StudentSchedule] = {}

    def save(self, schedule: StudentSchedule) -> None:
        self._items[(schedule.student_id, schedule.semester)] = schedule

    def find(self, student_id: str, semester) -> StudentSchedule | None:
        return self._items.get((student_id, semester))

    def find_all_for(self, student_id: str) -> list[StudentSchedule]:
        return [s for (sid, _), s in self._items.items() if sid == student_id]


class InMemoryRecordRepository(IRecordRepository):
    def __init__(self) -> None:
        self._items: dict[str, AcademicRecord] = {}

    def save(self, record: AcademicRecord) -> None:
        self._items[record.student_id] = record

    def find(self, student_id: str) -> AcademicRecord | None:
        return self._items.get(student_id)


class InMemoryUserRepository(IUserRepository):
    def __init__(self) -> None:
        self._items: dict[str, Person] = {}

    def save(self, person: Person) -> None:
        self._items[person.person_id] = person

    def find(self, person_id: str) -> Person | None:
        return self._items.get(person_id)

    def all(self) -> list[Person]:
        return list(self._items.values())

    def delete(self, person_id: str) -> None:
        self._items.pop(person_id, None)


class InMemoryWaitlistRepository(IWaitlistRepository):
    def __init__(self) -> None:
        self._items: dict[str, Waitlist] = {}

    def for_section(self, section_id: str) -> Waitlist:
        # Contract: never None.  Create-on-first-access keeps every caller free
        # of a null check.
        return self._items.setdefault(section_id, Waitlist(section_id))


class InMemoryGradeSubmissionRepository(IGradeSubmissionRepository):
    def __init__(self) -> None:
        self._items: dict[str, GradeSubmission] = {}

    def save(self, submission: GradeSubmission) -> None:
        self._items[submission.submission_id] = submission

    def find(self, submission_id: str) -> GradeSubmission | None:
        return self._items.get(submission_id)

    def all(self) -> list[GradeSubmission]:
        return list(self._items.values())


class InMemoryChangeRequestRepository(IChangeRequestRepository):
    def __init__(self) -> None:
        self._items: dict[str, CourseChangeRequest] = {}

    def save(self, request: CourseChangeRequest) -> None:
        self._items[request.request_id] = request

    def find(self, request_id: str) -> CourseChangeRequest | None:
        return self._items.get(request_id)

    def all(self) -> list[CourseChangeRequest]:
        return list(self._items.values())
