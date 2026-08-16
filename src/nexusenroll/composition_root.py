"""
===============================================================================
THE COMPOSITION ROOT -- what replaced the rejected Singleton
===============================================================================

This is the ONLY place in the entire system where objects are wired together.
Every class above this file receives its collaborators through its constructor
and constructs none of them.

WHY THIS FILE EXISTS AT ALL
    An earlier draft used `NotificationService.getInstance()` to guarantee that
    exactly one observer registry existed.  The concern was legitimate: if a
    second registry were ever created, subscriptions registered at start-up
    would be invisible to the instance dispatching events, and notifications
    would vanish SILENTLY -- no exception, no log, no waitlisted student ever
    told a seat had opened.

    But Singleton conflicts with three of the five SOLID principles:
      SRP -- the class acquires a second job, managing its own lifecycle;
      DIP -- every getInstance() call site binds to a CONCRETE class through a
             dependency invisible in the constructor signature;
      OCP -- substituting a test double means editing the accessor.

    The decisive argument was specific to our design: we had already committed
    to constructor injection everywhere, so the single-instance guarantee was
    coming from THE WIRING, NOT THE PATTERN.  We would have paid Singleton's
    full SOLID cost for a global access point we had promised never to use.

    So: `NotificationPublisher()` is constructed exactly once, below, and that
    same reference is injected into every collaborator.  Identical uniqueness
    guarantee, no global access point, no hidden dependency, every dependency
    visible in a constructor signature.  This is the SINGLE-INSTANCE LIFESTYLE,
    not the Singleton pattern.

    (A module is already effectively a singleton in Python, which makes a
    hand-written getInstance() un-idiomatic here as well.)

Full reasoning: DESIGN/01-design-patterns.md section 6, and the
rejected-patterns panel on diagram 03.
"""

from __future__ import annotations

from dataclasses import dataclass

from .domain.enums import EventType, ReportType
from .patterns.builder_search import CatalogQueryDirector, CourseSearchQueryBuilder
from .patterns.command_enrollment import EnrolmentReceiver, TransactionManager
from .patterns.facade_enrollment import EnrollmentFacade
from .patterns.factory_reports import (
    CapacityThresholdReport,
    CoursePopularityReport,
    EnrolmentStatisticsReport,
    FacultyWorkloadReport,
    ReportFactory,
)
from .patterns.observer_notifications import (
    AdminAlertObserver,
    AdvisorObserver,
    AuditObserver,
    EmailChannel,
    NotificationPublisher,
    WaitlistObserver,
)
from .patterns.state_course_change import CourseChangeService
from .patterns.state_grades import BatchGradeProcessor
from .patterns.strategy_validation import (
    CapacityRule,
    CreditLimitRule,
    EnrolmentContext,
    EnrollmentValidator,
    PrerequisiteRule,
    TimeConflictRule,
)
from .repositories.in_memory import (
    InMemoryChangeRequestRepository,
    InMemoryCourseRepository,
    InMemoryEnrollmentRepository,
    InMemoryGradeSubmissionRepository,
    InMemoryProgramRepository,
    InMemoryRecordRepository,
    InMemoryScheduleRepository,
    InMemorySectionRepository,
    InMemoryUserRepository,
    InMemoryWaitlistRepository,
)
from .seed import SEMESTER, seed
from .services.admin_service import (
    AccountManager,
    AdministratorModule,
    CourseCatalogAdmin,
)
from .services.faculty_service import FacultyModule
from .services.student_service import CourseCatalogService, StudentModule


@dataclass
class Repositories:
    """The data access layer, bundled.

    Every field is typed as the CONCRETE in-memory class here and only here.
    Everything above receives them through I*Repository parameters, so
    swapping in SQL implementations would change this file and nothing else --
    Liskov substitution with a single edit point.
    """

    users: InMemoryUserRepository
    courses: InMemoryCourseRepository
    sections: InMemorySectionRepository
    programs: InMemoryProgramRepository
    enrolments: InMemoryEnrollmentRepository
    schedules: InMemoryScheduleRepository
    records: InMemoryRecordRepository
    waitlists: InMemoryWaitlistRepository
    submissions: InMemoryGradeSubmissionRepository
    changes: InMemoryChangeRequestRepository


@dataclass
class System:
    """Everything main.py needs, assembled and ready to use."""

    repos: Repositories
    publisher: NotificationPublisher
    email: EmailChannel
    audit: AuditObserver
    tx: TransactionManager
    validator: EnrollmentValidator
    facade: EnrollmentFacade
    director: CatalogQueryDirector
    report_factory: ReportFactory
    student: StudentModule
    faculty: FacultyModule
    admin: AdministratorModule
    semester: object


def build_system() -> System:
    """Construct the entire object graph, bottom-up, exactly once."""

    # -- Data access layer ---------------------------------------------------
    repos = Repositories(
        users=InMemoryUserRepository(),
        courses=InMemoryCourseRepository(),
        sections=InMemorySectionRepository(),
        programs=InMemoryProgramRepository(),
        enrolments=InMemoryEnrollmentRepository(),
        schedules=InMemoryScheduleRepository(),
        records=InMemoryRecordRepository(),
        waitlists=InMemoryWaitlistRepository(),
        submissions=InMemoryGradeSubmissionRepository(),
        changes=InMemoryChangeRequestRepository(),
    )
    seed(repos)

    # -- OBSERVER (4): exactly ONE publisher, by construction ---------------
    publisher = NotificationPublisher()
    email = EmailChannel()

    publisher.attach(
        EventType.SEAT_RELEASED, WaitlistObserver(email, repos.waitlists, repos.users)
    )
    publisher.attach(
        EventType.STUDENT_DROPPED,
        AdvisorObserver(email, repos.users, repos.programs, repos.courses),
    )
    publisher.attach(EventType.SYSTEM_ERROR, AdminAlertObserver(email, repos.users))

    # A late-added subscriber standing in for the future financial aid system.
    # Note that attaching it required no change to any enrolment class -- the
    # Open/Closed Principle, at runtime.
    audit = AuditObserver({EventType.STUDENT_ENROLLED, EventType.STUDENT_DROPPED})
    publisher.attach(EventType.STUDENT_ENROLLED, audit)
    publisher.attach(EventType.STUDENT_DROPPED, audit)

    # -- STRATEGY (1): the standard student rule list ------------------------
    ctx = EnrolmentContext(semester=SEMESTER)
    prerequisite_rule = PrerequisiteRule(repos.records, repos.sections, repos.courses)
    capacity_rule = CapacityRule(repos.sections)
    time_conflict_rule = TimeConflictRule(repos.schedules, repos.sections)
    credit_limit_rule = CreditLimitRule(
        repos.schedules, repos.sections, repos.courses, max_credits=18
    )

    validator = EnrollmentValidator(
        [prerequisite_rule, capacity_rule, time_conflict_rule], ctx
    )
    # OPEN/CLOSED, demonstrated: a fourth rule joins with one call and zero
    # edits to EnrollmentValidator or to the three rules already present.
    validator.add_rule(credit_limit_rule)

    # The ADMINISTRATOR OVERRIDE list -- same classes, CapacityRule omitted.
    # No `if admin` branch exists anywhere in the rule implementations.
    override_rules = [prerequisite_rule, time_conflict_rule]

    # -- COMMAND (2) ---------------------------------------------------------
    receiver = EnrolmentReceiver(repos.enrolments, repos.sections, repos.schedules)
    tx = TransactionManager()

    # -- FACADE (6): every collaborator injected as an abstraction -----------
    facade = EnrollmentFacade(
        validator=validator,
        tx_manager=tx,
        publisher=publisher,
        receiver=receiver,
        enrol_repo=repos.enrolments,
        waitlist_repo=repos.waitlists,
        semester=SEMESTER,
    )

    # -- BUILDER (7) ---------------------------------------------------------
    director = CatalogQueryDirector(CourseSearchQueryBuilder())

    # -- FACTORY METHOD (5): register the four report kinds ------------------
    # Each entry is a zero-argument constructor closing over the repositories,
    # so ReportFactory itself needs no knowledge of what a report requires.
    report_factory = ReportFactory()
    report_factory.register(
        ReportType.ENROLMENT_STATISTICS,
        lambda: EnrolmentStatisticsReport(repos.sections, repos.courses, repos.enrolments),
    )
    report_factory.register(
        ReportType.FACULTY_WORKLOAD,
        lambda: FacultyWorkloadReport(repos.sections, repos.courses, repos.users),
    )
    report_factory.register(
        ReportType.COURSE_POPULARITY,
        lambda: CoursePopularityReport(repos.sections, repos.courses),
    )
    report_factory.register(
        ReportType.CAPACITY_THRESHOLD,
        lambda: CapacityThresholdReport(repos.sections, repos.courses, director),
    )

    # -- STATE (3) collaborators ---------------------------------------------
    processor = BatchGradeProcessor(repos.enrolments, publisher)
    change_service = CourseChangeService(repos.sections, repos.courses, publisher)

    # -- The three modules the brief requires --------------------------------
    catalog_service = CourseCatalogService(
        repos.sections, repos.courses, repos.users, repos.enrolments
    )
    student = StudentModule(
        facade, catalog_service, director, repos.records, repos.programs, repos.courses
    )
    faculty = FacultyModule(
        repos.sections, repos.enrolments, repos.users, repos.records,
        repos.submissions, repos.changes, processor,
    )
    admin = AdministratorModule(
        catalog_admin=CourseCatalogAdmin(repos.courses, repos.sections, repos.programs),
        accounts=AccountManager(repos.users),
        report_factory=report_factory,
        facade=facade,
        change_service=change_service,
        change_repo=repos.changes,
        submission_repo=repos.submissions,
        record_repo=repos.records,
        processor=processor,
        override_rules=override_rules,
        ctx=ctx,
    )

    return System(
        repos=repos, publisher=publisher, email=email, audit=audit, tx=tx,
        validator=validator, facade=facade, director=director,
        report_factory=report_factory, student=student, faculty=faculty,
        admin=admin, semester=SEMESTER,
    )
