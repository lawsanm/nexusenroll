"""STUDENT MODULE -- course catalogue browse and academic progress.

Registration/enrolment and schedule viewing are fronted by EnrollmentFacade
(pattern 6); this module covers the two remaining student features.

Patterns visible here:
    Builder (7)  -- every search goes through CourseSearchQueryBuilder
    Facade  (6)  -- enrolment itself is delegated, not reimplemented
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain.records import ProgressTracker
from ..patterns.builder_search import CatalogQueryDirector, CourseSearchQuery


@dataclass
class SectionView:
    """"Display real-time information": everything the requirement lists for a
    catalogue entry, in one flat row ready for a UI."""

    section_id: str
    course_code: str
    title: str
    description: str
    instructor: str
    seats: str
    schedule: str
    prerequisites: str

    def as_line(self) -> str:  # pragma: no cover - display only
        return (
            f"{self.section_id:<10} {self.course_code:<8} {self.title:<34} "
            f"{self.instructor:<18} {self.seats:<8} {self.schedule}"
        )


class CourseCatalogService:
    """Course Catalogue Browse.

    Note the search API: it takes a CourseSearchQuery -- the immutable Product
    built by pattern 7 -- rather than seven optional parameters.  That is the
    whole reason Builder is here.
    """

    def __init__(self, section_repo, course_repo, user_repo, enrol_repo) -> None:
        self._sections = section_repo
        self._courses = course_repo
        self._users = user_repo
        self._enrolments = enrol_repo

    def search(self, query: CourseSearchQuery) -> list[SectionView]:
        """Delegates the per-section decision to `query.matches()`, so the
        filtering logic lives with the query object, not scattered here."""
        views: list[SectionView] = []
        for section in self._sections.all():
            course = self._courses.find(section.course_code)
            if course is None:
                continue
            instructor = self._users.find(section.instructor_id)
            if query.matches(section, course, instructor):
                views.append(self._to_view(section, course, instructor))
        return sorted(views, key=lambda v: (v.course_code, v.section_id))

    def _to_view(self, section, course, instructor) -> SectionView:
        prereqs = ", ".join(p.required_course_code for p in course.get_prerequisites())
        return SectionView(
            section_id=section.section_id,
            course_code=course.course_code,
            title=course.title,
            description=course.description,
            instructor=instructor.get_full_name() if instructor else "TBA",
            # "available seats vs. total capacity", read live off the section
            seats=f"{section.available_seats()}/{section.total_capacity}",
            schedule=section.schedule_text(),
            prerequisites=prereqs or "none",
        )


class StudentModule:
    """Everything a student can do, in one place.

    It COMPOSES the facade and the catalogue service rather than inheriting
    from either -- composition over inheritance at module level.
    """

    def __init__(
        self,
        facade,
        catalog: CourseCatalogService,
        director: CatalogQueryDirector,
        record_repo,
        program_repo,
        course_repo,
    ) -> None:
        self._facade = facade
        self._catalog = catalog
        self._director = director
        self._records = record_repo
        self._programs = program_repo
        self._courses = course_repo
        self._tracker = ProgressTracker()

    # -- Course Catalogue Browse -------------------------------------------
    def browse(self, query: CourseSearchQuery) -> list[SectionView]:
        return self._catalog.search(query)

    def browse_department_by_instructor(self, department, instructor_name, semester):
        """The section 3.1 use case: "browse all computer science courses for
        the upcoming semester that a specific professor teaches"."""
        query = self._director.department_taught_by(department, instructor_name, semester)
        return self._catalog.search(query)

    # -- Registration and Enrolment (delegated to the Facade) ---------------
    def enrol(self, student_id, section_id, fail_on_step=None):
        return self._facade.enrol(student_id, section_id, fail_on_step=fail_on_step)

    def drop(self, student_id, section_id):
        return self._facade.drop(student_id, section_id)

    # -- Personal Schedule Management ---------------------------------------
    def schedule(self, student_id, semester=None):
        return self._facade.view_schedule(student_id, semester)

    def past_schedules(self, student_id):
        return self._facade.past_schedules(student_id)

    # -- Academic Progress Tracking -----------------------------------------
    def completed_courses(self, student_id) -> list[tuple[str, str]]:
        """"List completed courses with grades received"."""
        record = self._records.find(student_id)
        if record is None:
            return []
        return [(g.course_code, g.letter_grade) for g in record.get_completed_courses()]

    def remaining_requirements(self, student_id) -> tuple[list[str], float, int]:
        """"Show courses still required for the degree program"."""
        record = self._records.find(student_id)
        if record is None:
            return [], 0.0, 0
        program = self._programs.find(record.program_id)
        if program is None:
            return [], 0.0, 0

        def credits_of(code: str) -> int:
            course = self._courses.find(code)
            return course.credits if course else 0

        return (
            self._tracker.remaining_courses(record, program),
            self._tracker.percent_complete(record, program),
            self._tracker.credits_outstanding(record, program, credits_of),
        )
