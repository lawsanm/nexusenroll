"""
===============================================================================
PATTERN 1 -- STRATEGY  «Behavioural»          Diagram 03, zone 1
===============================================================================

ROLE OF THE PATTERN IN THIS SYSTEM
    The brief requires that "the system must validate all enrolment requests"
    against three rules: prerequisites, capacity, and time conflicts.  Each rule
    takes the same input, inspects some state, and returns pass/fail with a
    reason -- the textbook signature of a family of interchangeable algorithms.

GoF ROLES
    Strategy          -- ValidationRule            (the interface)
    ConcreteStrategy  -- PrerequisiteRule, CapacityRule, TimeConflictRule
    Context           -- EnrollmentValidator       (holds a list of strategies)

WHAT THE PATTERN BUYS US HERE
    1. Open/Closed.  A credit-limit rule is a new class plus one add_rule()
       call; EnrollmentValidator is never edited.  See `CreditLimitRule` at the
       bottom of this file -- it was added exactly that way.
    2. Independent testability.  TimeConflictRule can be exercised against two
       overlapping TimeSlots with no student, no database and no enrolment.
    3. Aggregate error reporting.  Because the Context ITERATES rather than
       short-circuiting, the student is told every reason the enrolment failed,
       not just the first.  This is precisely why Decorator was rejected: a
       decorator chain short-circuits.
    4. The administrator override composes a DIFFERENT RULE LIST (one without
       CapacityRule) rather than adding a special case inside a rule.

WITHOUT IT
    One validate() method with three nested `if` blocks; each new rule deepens
    the nesting, every change risks the others, and only one problem can be
    reported at a time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..domain.enrollment import EnrollmentRequest, ValidationResult
from ..repositories.interfaces import (
    ICourseRepository,
    IRecordRepository,
    IScheduleRepository,
    ISectionRepository,
)


@dataclass
class EnrolmentContext:
    """Everything a rule may need, passed in rather than looked up globally.

    Keeping this a parameter (not an attribute reached via a singleton) is what
    lets any rule be unit-tested with a hand-built context.
    """

    semester: object


# ---------------------------------------------------------------------------
# Strategy interface
# ---------------------------------------------------------------------------
class ValidationRule(ABC):
    """STRATEGY.  Deliberately a ONE-METHOD interface (plus a name), which is
    the Interface Segregation example in 02-design-principles.md: no rule is
    forced to implement undo() or on_event() stubs it does not need.

    LSP contract, honoured by every concrete rule: an invalid *request* is
    reported by RETURNING a failed ValidationResult, never by raising.  If one
    subtype raised while the others returned, the Context's uniform loop would
    break for that subtype -- exactly the Liskov violation to avoid.
    """

    @abstractmethod
    def validate(
        self, req: EnrollmentRequest, ctx: EnrolmentContext
    ) -> ValidationResult: ...

    @abstractmethod
    def rule_name(self) -> str: ...


# ---------------------------------------------------------------------------
# Concrete strategies -- one per requirement
# ---------------------------------------------------------------------------
class PrerequisiteRule(ValidationRule):
    """"Check if the student has completed the necessary prerequisites."

    Note the collaborators are REPOSITORY INTERFACES, injected via the
    constructor -- the rule depends on abstractions only.
    """

    def __init__(
        self,
        record_repo: IRecordRepository,
        section_repo: ISectionRepository,
        course_repo: ICourseRepository,
    ) -> None:
        self._records = record_repo
        self._sections = section_repo
        self._courses = course_repo

    def rule_name(self) -> str:
        return "PrerequisiteRule"

    def validate(self, req, ctx) -> ValidationResult:
        section = self._sections.find(req.section_id)
        if section is None:
            return ValidationResult.failure(f"Unknown section {req.section_id}")

        course = self._courses.find(section.course_code)
        if course is None:
            return ValidationResult.failure(f"Unknown course {section.course_code}")

        record = self._records.find(req.student_id)
        result = ValidationResult.ok()
        for prereq in course.get_prerequisites():
            if record is None or not prereq.is_satisfied_by(record):
                result.add_error(
                    f"Prerequisite not met: {course.course_code} requires "
                    f"{prereq.required_course_code} at grade "
                    f"{prereq.minimum_grade} or better"
                )
        return result


class CapacityRule(ValidationRule):
    """"Check if there is available capacity in the course."

    THE OVERRIDE NUANCE: this rule is not given a special "if admin" branch.
    Instead the administrator path composes a validator WITHOUT this rule (see
    services/admin_service.py).  The guard below is a belt-and-braces second
    line of defence for the case where the rule is present anyway.
    """

    def __init__(self, section_repo: ISectionRepository) -> None:
        self._sections = section_repo

    def rule_name(self) -> str:
        return "CapacityRule"

    def validate(self, req, ctx) -> ValidationResult:
        if req.is_override():
            return ValidationResult.ok()

        section = self._sections.find(req.section_id)
        if section is None:
            return ValidationResult.failure(f"Unknown section {req.section_id}")

        if not section.has_available_seat():
            return ValidationResult.failure(
                f"Section {section.section_id} is full "
                f"({section.enrolled_count}/{section.total_capacity} seats taken)"
            )
        return ValidationResult.ok()


class TimeConflictRule(ValidationRule):
    """"Check for time conflicts with the student's existing schedule."""

    def __init__(
        self, schedule_repo: IScheduleRepository, section_repo: ISectionRepository
    ) -> None:
        self._schedules = schedule_repo
        self._sections = section_repo

    def rule_name(self) -> str:
        return "TimeConflictRule"

    def validate(self, req, ctx) -> ValidationResult:
        section = self._sections.find(req.section_id)
        if section is None:
            return ValidationResult.failure(f"Unknown section {req.section_id}")

        schedule = self._schedules.find(req.student_id, ctx.semester)
        if schedule is None:
            return ValidationResult.ok()  # nothing enrolled yet, nothing to clash

        clash = schedule.has_conflict_with(section.time_slots)
        if clash is not None:
            return ValidationResult.failure(
                f"Time conflict: {section.section_id} overlaps an enrolled "
                f"class at {clash}"
            )
        return ValidationResult.ok()


class CreditLimitRule(ValidationRule):
    """DEMONSTRATION OF THE OPEN/CLOSED PRINCIPLE.

    This rule did not exist when EnrollmentValidator was written.  Adding it
    required a new class and one add_rule() call -- zero edits to the validator,
    to the facade, to the other three rules, or to any caller.  That is the
    concrete Open/Closed example claimed in 02-design-principles.md.
    """

    def __init__(
        self,
        schedule_repo: IScheduleRepository,
        section_repo: ISectionRepository,
        course_repo: ICourseRepository,
        max_credits: int = 18,
    ) -> None:
        self._schedules = schedule_repo
        self._sections = section_repo
        self._courses = course_repo
        self._max_credits = max_credits

    def rule_name(self) -> str:
        return "CreditLimitRule"

    def _credits_of(self, course_code: str) -> int:
        course = self._courses.find(course_code)
        return course.credits if course else 0

    def validate(self, req, ctx) -> ValidationResult:
        section = self._sections.find(req.section_id)
        schedule = self._schedules.find(req.student_id, ctx.semester)
        if section is None or schedule is None:
            return ValidationResult.ok()

        current = schedule.total_credits(self._credits_of)
        proposed = current + self._credits_of(section.course_code)
        if proposed > self._max_credits:
            return ValidationResult.failure(
                f"Credit limit exceeded: {proposed} credits requested, "
                f"maximum is {self._max_credits}"
            )
        return ValidationResult.ok()


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------
class EnrollmentValidator:
    """CONTEXT of the Strategy pattern.

    It knows only the ValidationRule abstraction -- there is no import of, and
    no isinstance check against, any concrete rule anywhere in this class.
    That is the "Programming to an Interface" example in the principles doc.

    COMPOSITION OVER INHERITANCE: standard enrolment, administrator override
    and (future) graduate enrolment are three different RULE LISTS passed into
    this one class, not three subclasses of a BaseValidator.
    """

    def __init__(self, rules: list[ValidationRule], ctx: EnrolmentContext) -> None:
        self._rules = list(rules)
        self._ctx = ctx

    def add_rule(self, rule: ValidationRule) -> None:
        """The entire cost of adding a new business rule at runtime."""
        self._rules.append(rule)

    def rule_names(self) -> list[str]:
        return [r.rule_name() for r in self._rules]

    def validate_all(self, req: EnrollmentRequest) -> ValidationResult:
        """DRY: the one and only place validation rules are iterated and merged.

        Note there is no early `return` inside the loop.  Iterating to the end
        is what lets the student see EVERY problem at once.
        """
        result = ValidationResult.ok()
        for rule in self._rules:
            result.merge(rule.validate(req, self._ctx))
        return result

    def failed_rules(self, req: EnrollmentRequest) -> list[str]:
        """Which rules failed -- used by the waitlist branch on diagram 04 to
        distinguish "full" (eligible, so queue them) from "ineligible"
        (reject them)."""
        return [
            rule.rule_name()
            for rule in self._rules
            if not rule.validate(req, self._ctx).is_valid()
        ]
