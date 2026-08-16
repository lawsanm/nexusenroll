"""
===============================================================================
PATTERN 5 -- FACTORY METHOD  «Creational»     Diagram 03, zone 5
===============================================================================

ROLE OF THE PATTERN IN THIS SYSTEM
        "The system must generate various reports: Enrolment statistics by
         department and semester.  Faculty workload reports.  Course popularity
         trends."

    Plus the section 3.3 use case (Business school courses over 90% capacity),
    which is a fourth.  The word "various" signals a set that will grow.

GoF ROLES
    Creator         -- ReportFactory       (create_report() is the factory method)
    Product         -- Report              (the interface)
    ConcreteProduct -- EnrolmentStatisticsReport, FacultyWorkloadReport,
                       CoursePopularityReport, CapacityThresholdReport

WHAT THE PATTERN BUYS US HERE
    The administrator module asks for a report BY KIND and receives a `Report`
    without knowing which concrete class implements it.  A new report type is a
    new class plus one register() call, and no calling code changes.
    available_types() additionally lets a UI populate its report menu
    dynamically instead of hard-coding one.

WHY NOT ABSTRACT FACTORY
    We have ONE product family, not several varying by platform or region.
    Factory Method is the right granularity; Abstract Factory here would be
    speculative generality (YAGNI).  See 01-design-patterns.md section 6.

WITHOUT IT
    A switch/if chain on a report-type string at every call site, duplicated
    wherever reports are requested, each needing an edit for every new report.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..domain.enums import ReportType


# ---------------------------------------------------------------------------
# The data a report produces -- "present report data in a clean, organised
# format (e.g. a table or spreadsheet)".
# ---------------------------------------------------------------------------
@dataclass
class ReportData:
    columns: list[str]
    rows: list[list[object]] = field(default_factory=list)

    def as_table(self) -> str:
        """Fixed-width table for the console demo."""
        if not self.rows:
            return "        (no rows)"
        widths = [
            max(len(str(self.columns[i])), max(len(str(r[i])) for r in self.rows))
            for i in range(len(self.columns))
        ]
        head = "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(self.columns))
        rule = "  ".join("-" * w for w in widths)
        body = [
            "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
            for row in self.rows
        ]
        return "\n".join(
            ["        " + head, "        " + rule] + ["        " + b for b in body]
        )

    def as_csv(self) -> str:
        """The "spreadsheet" half of the same requirement."""
        lines = [",".join(self.columns)]
        lines += [",".join(str(c) for c in row) for row in self.rows]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Product interface
# ---------------------------------------------------------------------------
class Report(ABC):
    """PRODUCT.  Three methods -- generate, title, export.  The administrator
    module is written against THIS and never against a concrete report."""

    @abstractmethod
    def generate(self, criteria=None) -> ReportData: ...

    @abstractmethod
    def title(self) -> str: ...

    def export(self, fmt: str = "table") -> str:
        """Shared default -- the one piece of behaviour genuinely common to all
        four reports.  (Note this is NOT a Template Method: there is no fixed
        multi-step skeleton, which is exactly why Template Method was rejected
        for report generation.)"""
        data = self.generate()
        return data.as_csv() if fmt == "csv" else data.as_table()


# ---------------------------------------------------------------------------
# Concrete products -- each owns its own aggregation shape
# ---------------------------------------------------------------------------
class EnrolmentStatisticsReport(Report):
    """"Enrolment statistics by department and semester"."""

    def __init__(self, section_repo, course_repo, enrol_repo) -> None:
        self._sections = section_repo
        self._courses = course_repo
        self._enrolments = enrol_repo

    def title(self) -> str:
        return "Enrolment Statistics by Department and Semester"

    def generate(self, criteria=None) -> ReportData:
        buckets: dict[tuple[str, str], list[int]] = {}
        for section in self._sections.all():
            course = self._courses.find(section.course_code)
            if course is None:
                continue
            key = (course.department, section.semester.label)
            bucket = buckets.setdefault(key, [0, 0, 0])
            bucket[0] += 1                        # sections
            bucket[1] += section.enrolled_count   # enrolled
            bucket[2] += section.total_capacity   # capacity

        rows = [
            [dept, sem, b[0], b[1], b[2], f"{(b[1] / b[2] * 100 if b[2] else 0):.0f}%"]
            for (dept, sem), b in sorted(buckets.items())
        ]
        return ReportData(
            ["Department", "Semester", "Sections", "Enrolled", "Capacity", "Fill"], rows
        )


class FacultyWorkloadReport(Report):
    """"Faculty workload reports" -- sections and credits taught per instructor."""

    def __init__(self, section_repo, course_repo, user_repo) -> None:
        self._sections = section_repo
        self._courses = course_repo
        self._users = user_repo

    def title(self) -> str:
        return "Faculty Workload"

    def generate(self, criteria=None) -> ReportData:
        workload: dict[str, list[int]] = {}
        for section in self._sections.all():
            course = self._courses.find(section.course_code)
            bucket = workload.setdefault(section.instructor_id, [0, 0, 0])
            bucket[0] += 1
            bucket[1] += course.credits if course else 0
            bucket[2] += section.enrolled_count

        rows = []
        for instructor_id, (sections, credits, students) in sorted(workload.items()):
            person = self._users.find(instructor_id)
            name = person.get_full_name() if person else instructor_id
            rows.append([name, sections, credits, students])
        return ReportData(["Instructor", "Sections", "Credits", "Students"], rows)


class CoursePopularityReport(Report):
    """"Course popularity trends" -- enrolment trend across semesters."""

    def __init__(self, section_repo, course_repo) -> None:
        self._sections = section_repo
        self._courses = course_repo

    def title(self) -> str:
        return "Course Popularity Trends"

    def generate(self, criteria=None) -> ReportData:
        totals: dict[str, list[int]] = {}
        for section in self._sections.all():
            bucket = totals.setdefault(section.course_code, [0, 0])
            bucket[0] += section.enrolled_count
            bucket[1] += section.total_capacity

        rows = []
        for code, (enrolled, capacity) in totals.items():
            course = self._courses.find(code)
            rate = enrolled / capacity if capacity else 0
            rows.append(
                [code, course.title if course else "?", enrolled, f"{rate * 100:.0f}%"]
            )
        rows.sort(key=lambda r: -int(r[2]))  # most popular first
        return ReportData(["Course", "Title", "Enrolled", "Fill rate"], rows)


class CapacityThresholdReport(Report):
    """THE SECTION 3.3 USE CASE: "a report on all courses in the Business
    school that are currently at over 90% capacity".

    Note how it obtains its criteria: from the BUILDER (pattern 7), via the
    CatalogQueryDirector's over_capacity_in_school() recipe.  Two patterns
    collaborating -- Factory Method creates the report, Builder builds the
    query it runs.
    """

    def __init__(self, section_repo, course_repo, director) -> None:
        self._sections = section_repo
        self._courses = course_repo
        self._director = director

    def title(self) -> str:
        return "Courses Over Capacity Threshold"

    def generate(self, criteria=None) -> ReportData:
        school = (criteria or {}).get("school", "Business")
        threshold = (criteria or {}).get("threshold", 0.9)

        query = self._director.over_capacity_in_school(school, threshold)
        rows = []
        for section in self._sections.all():
            course = self._courses.find(section.course_code)
            if course is None:
                continue
            if query.matches(section, course, None):
                rows.append(
                    [
                        section.section_id,
                        course.course_code,
                        course.title,
                        f"{section.enrolled_count}/{section.total_capacity}",
                        f"{section.occupancy_rate() * 100:.0f}%",
                    ]
                )
        rows.sort(key=lambda r: r[4], reverse=True)
        return ReportData(
            ["Section", "Course", "Title", "Seats", "Occupancy"], rows
        )


# ---------------------------------------------------------------------------
# Creator
# ---------------------------------------------------------------------------
class ReportFactory:
    """CREATOR.  `create_report()` is the factory method.

    A registry of ReportType -> zero-argument constructor keeps the factory
    itself closed to modification: registering a new kind is a call, not an
    edit to a switch statement inside this class.
    """

    def __init__(self) -> None:
        self._registry: dict[ReportType, callable] = {}

    def register(self, report_type: ReportType, constructor) -> None:
        self._registry[report_type] = constructor

    def create_report(self, report_type: ReportType) -> Report:
        """THE FACTORY METHOD.  Callers get a `Report`; which concrete class
        they got is not their business."""
        constructor = self._registry.get(report_type)
        if constructor is None:
            raise ValueError(f"No report registered for {report_type}")
        return constructor()

    def available_types(self) -> list[ReportType]:
        """Lets a UI build its report menu dynamically."""
        return list(self._registry)
