"""
===============================================================================
PATTERN 7 -- BUILDER  «Creational»            Diagram 03, zone 7
===============================================================================

ROLE OF THE PATTERN IN THIS SYSTEM
        "Students can search for courses by department, course number, keyword,
         and instructor."

    Four independent OPTIONAL filters is 16 possible combinations, and the
    administrator reports add three more criteria (semester, school, minimum
    occupancy).  The two obvious alternatives are both poor:

      * telescoping constructors -- one overload per combination;
      * one wide constructor with nullable parameters -- call sites degrade to
        search(None, None, "algorithms", None, None, True, None), where a
        transposed argument is a silent bug rather than an error.

GoF ROLES
    Builder         -- SearchQueryBuilder        (the interface)
    ConcreteBuilder -- CourseSearchQueryBuilder
    Product         -- CourseSearchQuery         (immutable)
    Director        -- CatalogQueryDirector      (holds the reusable recipes)

WHAT THE PATTERN BUYS US HERE
    1. Readable, self-documenting call sites -- each step names its criterion.
    2. An IMMUTABLE product.  CourseSearchQuery is frozen, so once built it can
       be logged, cached and passed across a service boundary to the Reporting
       Service with no risk of downstream mutation and no defensive copying.
    3. VALIDATION AT THE MOMENT OF CONSTRUCTION.  build() enforces the
       invariants -- at least one criterion, occupancy within 0.0-1.0, semester
       not in the past -- so AN INVALID QUERY OBJECT CAN NEVER EXIST.  That is
       Fail Fast applied to a value object.
    4. The Director removes duplication: student catalogue search and the
       administrator ">90% capacity" report share one builder (DRY), even
       though the two features live in different modules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..domain.catalog import CourseSection
from ..domain.enums import Semester


# ---------------------------------------------------------------------------
# Product -- immutable by construction
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CourseSearchQuery:
    """PRODUCT.  `frozen=True` is the whole point: there are no setters, so the
    object cannot drift after validation."""

    department: str | None = None
    course_number: str | None = None
    keyword: str | None = None
    instructor_id: str | None = None
    instructor_name: str | None = None
    semester: Semester | None = None
    school: str | None = None
    min_occupancy: float | None = None
    available_seats_only: bool = False

    @staticmethod
    def builder() -> CourseSearchQueryBuilder:
        """Convenience entry point used by the client-side example in
        01-design-patterns.md."""
        return CourseSearchQueryBuilder()

    def matches(self, section: CourseSection, course, instructor) -> bool:
        """The query knows how to test itself against a section.

        Each criterion is skipped when it was never set, which is what makes
        any SUBSET of the criteria a valid query.
        """
        if self.department and course.department.lower() != self.department.lower():
            return False
        if self.course_number and self.course_number.lower() not in course.course_code.lower():
            return False
        if self.keyword:
            haystack = f"{course.title} {course.description}".lower()
            if self.keyword.lower() not in haystack:
                return False
        if self.instructor_id and section.instructor_id != self.instructor_id:
            return False
        if self.instructor_name:
            name = instructor.get_full_name().lower() if instructor else ""
            if self.instructor_name.lower() not in name:
                return False
        if self.semester and section.semester is not self.semester:
            return False
        if self.school and (course.school or "").lower() != self.school.lower():
            return False
        if self.min_occupancy is not None and section.occupancy_rate() < self.min_occupancy:
            return False
        if self.available_seats_only and not section.has_available_seat():
            return False
        return True

    def describe(self) -> str:
        parts = [
            f"{field}={value!r}"
            for field, value in self.__dict__.items()
            if value not in (None, False)
        ]
        return "CourseSearchQuery(" + ", ".join(parts) + ")"


# ---------------------------------------------------------------------------
# Builder interface
# ---------------------------------------------------------------------------
class SearchQueryBuilder(ABC):
    """BUILDER.  Every step returns the builder itself, which is what makes the
    fluent chaining in the Director's recipes possible."""

    @abstractmethod
    def reset(self) -> SearchQueryBuilder: ...

    @abstractmethod
    def department(self, value: str) -> SearchQueryBuilder: ...

    @abstractmethod
    def course_number(self, value: str) -> SearchQueryBuilder: ...

    @abstractmethod
    def keyword(self, value: str) -> SearchQueryBuilder: ...

    @abstractmethod
    def instructor(self, value: str) -> SearchQueryBuilder: ...

    @abstractmethod
    def build(self) -> CourseSearchQuery: ...


# ---------------------------------------------------------------------------
# Concrete builder
# ---------------------------------------------------------------------------
class CourseSearchQueryBuilder(SearchQueryBuilder):
    """CONCRETE BUILDER.  Accumulates criteria, then validates once in build()."""

    def __init__(self) -> None:
        self._criteria: dict[str, object] = {}

    def reset(self) -> CourseSearchQueryBuilder:
        self._criteria = {}
        return self

    # -- the four criteria the requirement names ----------------------------
    def department(self, value: str) -> CourseSearchQueryBuilder:
        self._criteria["department"] = value
        return self

    def course_number(self, value: str) -> CourseSearchQueryBuilder:
        self._criteria["course_number"] = value
        return self

    def keyword(self, value: str) -> CourseSearchQueryBuilder:
        self._criteria["keyword"] = value
        return self

    def instructor(self, value: str) -> CourseSearchQueryBuilder:
        """By display name -- what a student actually types."""
        self._criteria["instructor_name"] = value
        return self

    # -- extra criteria the administrator reports need -----------------------
    def instructor_id(self, value: str) -> CourseSearchQueryBuilder:
        self._criteria["instructor_id"] = value
        return self

    def semester(self, value: Semester) -> CourseSearchQueryBuilder:
        self._criteria["semester"] = value
        return self

    def school(self, value: str) -> CourseSearchQueryBuilder:
        self._criteria["school"] = value
        return self

    def min_occupancy(self, value: float) -> CourseSearchQueryBuilder:
        self._criteria["min_occupancy"] = value
        return self

    def with_available_seats_only(self) -> CourseSearchQueryBuilder:
        self._criteria["available_seats_only"] = True
        return self

    def build(self) -> CourseSearchQuery:
        """FAIL FAST.  All three invariants are checked here, once, so no caller
        can ever hold an invalid CourseSearchQuery."""
        if not self._criteria:
            raise ValueError(
                "A search needs at least one criterion - an empty query would "
                "return the entire catalogue"
            )

        occupancy = self._criteria.get("min_occupancy")
        if occupancy is not None and not 0.0 <= float(occupancy) <= 1.0:
            raise ValueError(f"min_occupancy must be within 0.0-1.0, got {occupancy}")

        semester = self._criteria.get("semester")
        if semester is not None and semester.ordinal < Semester.SPRING_2026.ordinal:
            raise ValueError(f"Cannot search a past semester: {semester}")

        return CourseSearchQuery(**self._criteria)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Director
# ---------------------------------------------------------------------------
class CatalogQueryDirector:
    """DIRECTOR -- knows the recipes; delegates the steps to the builder.

    These are the standard queries the system issues repeatedly.  Because
    `over_capacity_in_school()` lives beside the student-facing recipes, the
    administrator's ">90% capacity" report and student catalogue search share
    one query-construction path (DRY) despite living in different modules.
    """

    def __init__(self, builder: SearchQueryBuilder) -> None:
        self._builder = builder

    def open_sections_for(self, department: str, semester: Semester) -> CourseSearchQuery:
        return (
            self._builder.reset()
            .department(department)
            .semester(semester)
            .with_available_seats_only()
            .build()
        )

    def taught_by(self, instructor_name: str, semester: Semester) -> CourseSearchQuery:
        """The section 3.1 use case: "browse all computer science courses for
        the upcoming semester that a specific professor teaches" -- combine
        with .department() at the call site."""
        return (
            self._builder.reset()
            .instructor(instructor_name)
            .semester(semester)
            .build()
        )

    def department_taught_by(
        self, department: str, instructor_name: str, semester: Semester
    ) -> CourseSearchQuery:
        return (
            self._builder.reset()
            .department(department)
            .instructor(instructor_name)
            .semester(semester)
            .build()
        )

    def over_capacity_in_school(self, school: str, threshold: float) -> CourseSearchQuery:
        """The section 3.3 administrator use case, verbatim: "a report on all
        courses in the Business school that are currently at over 90%
        capacity"."""
        return (
            self._builder.reset()
            .school(school)
            .min_occupancy(threshold)
            .build()
        )
