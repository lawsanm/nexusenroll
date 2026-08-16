"""ADMINISTRATOR MODULE -- course/program management, accounts, overrides,
approvals and reporting.

Patterns visible here:
    Factory Method (5) -- every report is created through ReportFactory
    Builder (7)        -- the >90% capacity report's criteria
    Strategy (1)       -- the override composes a rule list WITHOUT CapacityRule
    State (3)          -- approving a CourseChangeRequest
"""

from __future__ import annotations

from ..domain.catalog import Course, CourseSection, DegreeProgram
from ..domain.enums import ReportType
from ..domain.people import Administrator, Faculty, Person, Student
from ..patterns.factory_reports import Report, ReportFactory
from ..patterns.strategy_validation import EnrolmentContext, EnrollmentValidator


class CourseCatalogAdmin:
    """"Create, edit, and delete courses" and "define and manage degree
    programs (required courses and credits)"."""

    def __init__(self, course_repo, section_repo, program_repo) -> None:
        self._courses = course_repo
        self._sections = section_repo
        self._programs = program_repo

    def create_course(self, course: Course) -> Course:
        self._courses.save(course)
        return course

    def edit_course(self, course_code: str, **changes) -> Course | None:
        course = self._courses.find(course_code)
        if course is None:
            return None
        for field, value in changes.items():
            if hasattr(course, field):
                setattr(course, field, value)
        self._courses.save(course)
        return course

    def delete_course(self, course_code: str) -> bool:
        """Refuses to orphan sections -- an integrity rule that belongs in the
        business tier, not in the database."""
        if any(s.course_code == course_code for s in self._sections.all()):
            return False
        self._courses.delete(course_code)
        return True

    def define_program(self, program: DegreeProgram) -> DegreeProgram:
        self._programs.save(program)
        return program

    def add_section(self, section: CourseSection) -> CourseSection:
        self._sections.save(section)
        return section


class AccountManager:
    """"Add, edit, and deactivate student and faculty accounts."

    Works against `Person`, so it handles all three subclasses without a single
    isinstance check -- polymorphism doing the work.
    """

    def __init__(self, user_repo) -> None:
        self._users = user_repo

    def add_account(self, person: Person) -> Person:
        self._users.save(person)
        return person

    def edit_account(self, person_id: str, **changes) -> Person | None:
        person = self._users.find(person_id)
        if person is None:
            return None
        for field, value in changes.items():
            if hasattr(person, field):
                setattr(person, field, value)
        self._users.save(person)
        return person

    def deactivate(self, person_id: str) -> bool:
        person = self._users.find(person_id)
        if person is None:
            return False
        person.deactivate()  # Tell, Don't Ask
        self._users.save(person)
        return True

    def students(self) -> list[Student]:
        return [p for p in self._users.all() if isinstance(p, Student)]

    def faculty(self) -> list[Faculty]:
        return [p for p in self._users.all() if isinstance(p, Faculty)]


class AdministratorModule:
    def __init__(
        self,
        catalog_admin: CourseCatalogAdmin,
        accounts: AccountManager,
        report_factory: ReportFactory,
        facade,
        change_service,
        change_repo,
        submission_repo,
        record_repo,
        processor,
        override_rules: list,
        ctx: EnrolmentContext,
    ) -> None:
        self._catalog = catalog_admin
        self._accounts = accounts
        self._reports = report_factory
        self._facade = facade
        self._change_service = change_service
        self._changes = change_repo
        self._submissions = submission_repo
        self._records = record_repo
        self._processor = processor
        # THE OVERRIDE RULE LIST: composed WITHOUT CapacityRule.  This is the
        # Strategy pattern paying off -- the override is a different list, not
        # an `if admin` branch buried inside CapacityRule.
        self._override_validator = EnrollmentValidator(override_rules, ctx)

    # -- Course & Program Management ----------------------------------------
    @property
    def catalog(self) -> CourseCatalogAdmin:
        return self._catalog

    # -- Student & Faculty Management ---------------------------------------
    @property
    def accounts(self) -> AccountManager:
        return self._accounts

    def force_add(self, admin: Administrator, student_id: str, section_id: str):
        """"Manually override enrolment rules (e.g. force-add a student into a
        full class)."

        Guarded on the administrator's own permission set, then delegated to
        the facade with the override rule list.
        """
        if not admin.can_override_enrolment():
            from ..patterns.facade_enrollment import EnrolmentOutcome

            return EnrolmentOutcome(False, f"{admin.get_full_name()} lacks override rights")
        return self._facade.force_add(self._override_validator, student_id, section_id)

    # -- Approvals (State pattern, second application) -----------------------
    def pending_change_requests(self):
        return [r for r in self._changes.all() if r.state_name() == "PendingAdminApprovalState"]

    def approve_change(self, admin: Administrator, request_id: str) -> str:
        """Approve, then apply.  The live section is mutated only now."""
        request = self._changes.find(request_id)
        if request is None:
            return "unknown request"
        request.approve(admin.admin_id)  # delegates to PendingAdminApprovalState
        self._changes.save(request)
        return self._change_service.apply_if_approved(request)

    def reject_change(self, request_id: str, reason: str) -> str:
        request = self._changes.find(request_id)
        if request is None:
            return "unknown request"
        request.reject(reason)
        self._changes.save(request)
        return request.state_name()

    def approve_grades(self, admin: Administrator, submission_id: str) -> str:
        """PendingApproval -> Submitted (or -> PartiallyRejected).

        On reaching SubmittedState we run the entry action: update the student
        academic records and publish GradesSubmitted.
        """
        submission = self._submissions.find(submission_id)
        if submission is None:
            return "unknown submission"
        submission.approve(admin.admin_id)
        self._submissions.save(submission)
        if submission.state_name() == "SubmittedState":
            self._processor.apply_to_records(submission, self._records)
        return submission.state_name()

    # -- Reporting & Analytics (Factory Method) ------------------------------
    def run_report(self, report_type: ReportType, criteria: dict | None = None):
        """Note the return type: a `Report`.  This module never names a
        concrete report class, so adding a fifth report requires no change
        here."""
        report: Report = self._reports.create_report(report_type)
        return report, report.generate(criteria)

    def available_reports(self) -> list[ReportType]:
        return self._reports.available_types()
