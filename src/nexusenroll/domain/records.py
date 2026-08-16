"""Academic Records context -- Grade, AcademicRecord, GradeSubmission,
Transcript and ProgressTracker.

Diagram 02, ACADEMIC RECORDS band.  GradeSubmission's lifecycle is modelled by
the State pattern -- diagram 06 page 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import Semester

#: Letter grade -> grade points.  A grade outside this map is invalid, which is
#: what the per-entry validation in BatchGradeProcessor checks.
GRADE_POINTS: dict[str, float] = {
    "A+": 4.0, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0,
    "F": 0.0,
}


@dataclass
class Grade:
    student_id: str
    course_code: str
    letter_grade: str
    semester: Semester

    @property
    def grade_points(self) -> float:
        return GRADE_POINTS.get(self.letter_grade.upper(), 0.0)

    def is_valid_letter(self) -> bool:
        return self.letter_grade.upper() in GRADE_POINTS

    def is_passing(self) -> bool:
        return self.is_valid_letter() and self.grade_points >= 1.0

    def meets(self, minimum_letter: str) -> bool:
        return self.grade_points >= GRADE_POINTS.get(minimum_letter.upper(), 0.0)


@dataclass
class AcademicRecord:
    student_id: str
    program_id: str
    grades: list[Grade] = field(default_factory=list)

    def add_grade(self, grade: Grade) -> None:
        self.grades.append(grade)

    def get_completed_courses(self) -> list[Grade]:
        return [g for g in self.grades if g.is_passing()]

    def has_completed(self, course_code: str, minimum_letter: str = "D") -> bool:
        """Used by PrerequisiteRule -- the Enrolment/Records loop closed."""
        return any(
            g.course_code == course_code and g.is_passing() and g.meets(minimum_letter)
            for g in self.grades
        )

    def earned_credits(self, credits_of) -> int:
        return sum(credits_of(g.course_code) for g in self.get_completed_courses())

    def calculate_gpa(self) -> float:
        if not self.grades:
            return 0.0
        return round(sum(g.grade_points for g in self.grades) / len(self.grades), 2)


@dataclass
class Transcript:
    """Read-only projection of an AcademicRecord, for display and export."""

    student_id: str
    entries: list[Grade]
    gpa: float

    @classmethod
    def of(cls, record: AcademicRecord) -> Transcript:
        return cls(record.student_id, list(record.grades), record.calculate_gpa())


@dataclass
class GradeSubmission:
    """Context of the State pattern (pattern 3).

    Every mutating operation delegates to `self.state`, so the rules about
    which transitions are legal live next to the state that describes them
    rather than in an if/elif ladder here.  See diagram 03 zone 3.
    """

    submission_id: str
    section_id: str
    faculty_id: str
    semester: Semester
    entries: list[Grade] = field(default_factory=list)
    rejected_entries: list[tuple[Grade, str]] = field(default_factory=list)
    # Injected by the State module (patterns/state_grades.py) at construction
    # time to keep the domain free of a dependency on the pattern package.
    state: object | None = field(default=None, repr=False)

    # -- Context methods -- each one is a pure delegation. --------------------
    def add_entry(self, grade: Grade) -> None:
        self.state.add_entry(self, grade)

    def submit_for_approval(self) -> None:
        self.state.submit_for_approval(self)

    def approve(self, admin_id: str) -> None:
        self.state.approve(self, admin_id)

    def reject(self, reason: str) -> None:
        self.state.reject(self, reason)

    def correct_entry(self, grade: Grade) -> None:
        self.state.correct_entry(self, grade)

    def set_state(self, state) -> None:
        self.state = state

    def state_name(self) -> str:
        return self.state.name()


class ProgressTracker:
    """Academic Progress Tracking.  A stateless collaborator -- it is given the
    record and the program rather than holding references to repositories.
    """

    def remaining_courses(self, record: AcademicRecord, program) -> list[str]:
        return program.remaining_for(record)

    def percent_complete(self, record: AcademicRecord, program) -> float:
        required = program.get_required_courses()
        if not required:
            return 100.0
        done = len(required) - len(program.remaining_for(record))
        return round(done / len(required) * 100, 1)

    def credits_outstanding(self, record: AcademicRecord, program, credits_of) -> int:
        return max(0, program.required_credits - record.earned_credits(credits_of))
