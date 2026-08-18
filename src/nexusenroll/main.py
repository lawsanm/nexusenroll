"""
===============================================================================
NexusEnroll -- runnable proof of concept
===============================================================================

Satisfies the brief's requirement for "a simple main function or test classes
that simulate student, faculty and administration functions/user stories".

Running order:

    ACT 1  Student module      -- catalogue search, validation, enrolment,
                                  schedule, progress tracking
    ACT 2  Faculty module      -- roster, batch grading with error isolation,
                                  course change request
    ACT 3  Administrator module-- approvals, force-add override, reports
    ACT 4  The three pattern PROOFS -- each one shows a pattern working rather
                                  than merely existing:
                                    (a) Command rollback leaves state untouched
                                    (b) State refuses an illegal transition
                                    (c) Observer fires with no enrolment code
                                        involved, and isolates a failure

Run with:   python -m nexusenroll.main       (from the src/ directory)
       or:  python src/nexusenroll/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `python src/nexusenroll/main.py` to work as well as `-m`.
if __package__ in (None, ""):  # pragma: no cover - script-mode convenience
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from nexusenroll.composition_root import build_system
    from nexusenroll.domain.enums import ChangeType, EventType, ReportType, Semester
    from nexusenroll.domain.events import DomainEvent
    from nexusenroll.domain.exceptions import IllegalTransition
    from nexusenroll.domain.records import Grade
    from nexusenroll.patterns.observer_notifications import FailingChannel, WaitlistObserver
else:
    from .composition_root import build_system
    from .domain.enums import ChangeType, EventType, ReportType, Semester
    from .domain.events import DomainEvent
    from .domain.exceptions import IllegalTransition
    from .domain.records import Grade
    from .patterns.observer_notifications import FailingChannel, WaitlistObserver


# ---------------------------------------------------------------------------
# Console helpers -- presentation only, no business logic here.
# ---------------------------------------------------------------------------
def banner(text: str) -> None:
    print(f"\n{'=' * 78}\n{text}\n{'=' * 78}")


def step(text: str) -> None:
    print(f"\n--- {text}")


def out(text: str = "") -> None:
    print(f"        {text}")


# ===========================================================================
# ACT 1 -- STUDENT MODULE
# ===========================================================================
def act_student(sys_) -> None:
    banner("ACT 1  STUDENT MODULE")
    student = sys_.student

    # -- Course Catalogue Browse (BUILDER 7) --------------------------------
    step("1.1  Catalogue search -- the section 3.1 use case")
    out('"Browse all Computer Science courses for the upcoming semester')
    out(' that a specific professor teaches."')
    out()
    results = student.browse_department_by_instructor(
        "Computer Science", "Nimal Silva", Semester.FALL_2026
    )
    out(f"{'Section':<10} {'Course':<8} {'Title':<34} {'Instructor':<18} {'Seats':<8} Schedule")
    out("-" * 110)
    for view in results:
        out(view.as_line())
    out()
    out("The query was assembled by CourseSearchQueryBuilder via the Director's")
    out("department_taught_by() recipe -- no seven-parameter search() call.")

    step("1.2  Builder validates on build() -- an invalid query cannot exist")
    try:
        from nexusenroll.patterns.builder_search import CourseSearchQueryBuilder  # noqa: PLC0415
    except ImportError:  # pragma: no cover
        from .patterns.builder_search import CourseSearchQueryBuilder
    try:
        CourseSearchQueryBuilder().min_occupancy(1.7).build()
    except ValueError as exc:
        out(f"REFUSED at construction: {exc}")

    # -- Registration and Enrolment (FACADE 6 -> STRATEGY 1 -> COMMAND 2) ---
    step("1.3  Successful enrolment -- Facade orchestrates the whole flow")
    section = sys_.repos.sections.find("CS301-A")
    out(f"CS301-A before: {section.enrolled_count}/{section.total_capacity} seats taken")
    outcome = student.enrol("S-01", "CS301-A")
    out(f"S-01 (Kavith, has completed CS-201) -> {outcome}")
    out(f"CS301-A after:  {section.enrolled_count}/{section.total_capacity} seats taken")

    step("1.4  Validation refusals -- Strategy reports EVERY failed rule")
    out("S-02 (Dilini) has not completed CS-201:")
    out(f"  {student.enrol('S-02', 'CS301-A')}")

    student.enrol("S-05", "CS101-A")
    out("")
    out("S-05 is enrolled in CS101-A (Mon 09:00-11:00); MAT105-A is Mon 10:00-12:00:")
    out(f"  {student.enrol('S-05', 'MAT105-A')}")

    step("1.5  Full section -> waitlisted, not rejected")
    out("BUS210-A is at 3/3. S-04 fails ONLY the capacity rule, so she is")
    out("eligible and gets queued rather than refused:")
    result = student.enrol("S-04", "BUS210-A")
    out(f"  {result}  (queue position {result.waitlist_position})")

    # -- Personal Schedule Management ---------------------------------------
    step("1.6  Personal schedule -- the calendar-like view")
    student.enrol("S-01", "CS350-A")
    for day, entries in student.schedule("S-01").items():
        out(f"{day:<10} {entries[0]}")
        for extra in entries[1:]:
            out(f"{'':<10} {extra}")

    # -- Academic Progress Tracking -----------------------------------------
    step("1.7  Academic progress")
    out("Completed courses with grades:")
    for code, letter in student.completed_courses("S-01"):
        out(f"  {code:<10} {letter}")
    remaining, percent, credits = student.remaining_requirements("S-01")
    out(f"Still required for BSc Computer Science: {', '.join(remaining)}")
    out(f"Degree progress: {percent}%  ({credits} credits outstanding)")


# ===========================================================================
# ACT 2 -- FACULTY MODULE
# ===========================================================================
def act_faculty(sys_) -> None:
    banner("ACT 2  FACULTY MODULE")
    faculty = sys_.faculty

    # -- Class Roster Viewing ------------------------------------------------
    step("2.1  Class roster -- real-time, with contact information")
    for entry in faculty.roster("F-01", "CS301-A"):
        out(f"{entry.student_id:<6} {entry.name:<22} {entry.email:<24} "
            f"{entry.phone:<14} {entry.status}")

    # -- Grade Submission (STATE 3) -----------------------------------------
    step("2.2  Batch grade entry with ERROR ISOLATION")
    submission = faculty.open_submission("F-01", "CS301-A", Semester.FALL_2026)
    out(f"New submission {submission.submission_id} state = {submission.state_name()}")

    batch = [
        Grade("S-01", "CS-301", "A-", Semester.FALL_2026),   # valid
        Grade("S-02", "CS-301", "Z+", Semester.FALL_2026),   # invalid letter
        Grade("S-99", "CS-301", "B", Semester.FALL_2026),    # not enrolled
    ]
    rejected = faculty.enter_batch(submission, batch)
    out(f"Accepted {len(submission.entries)} entries; rejected {len(rejected)}:")
    for grade, reason in rejected:
        out(f"  REJECTED {grade.student_id} '{grade.letter_grade}' -- {reason}")
    out("The valid entry for S-01 was NOT discarded. One bad grade in a roster")
    out("of 200 would reject one entry, not 200.")

    step("2.3  Draft -> PendingApproval, the state the requirement names")
    submission.rejected_entries = []      # professor gave up on the two bad rows
    state = faculty.submit_for_approval(submission)
    out(f"{submission.submission_id} state = {state}")
    sys_.demo_submission = submission     # handed to Act 3 and Act 4

    # -- Course Information Management (STATE 3, second application) --------
    step("2.4  Course change request -- requires administrator approval")
    request = faculty.request_change(
        "F-03", "BUS210-A", ChangeType.CAPACITY, capacity=5
    )
    section = sys_.repos.sections.find("BUS210-A")
    out(f"{request.request_id}: raise BUS210-A capacity 3 -> 5")
    out(f"Request state = {request.state_name()}")
    out(f"LIVE section capacity is still {section.total_capacity} -- the catalogue is")
    out("unaffected until an administrator approves. That is enforced by the")
    out("state machine, not by convention.")


# ===========================================================================
# ACT 3 -- ADMINISTRATOR MODULE
# ===========================================================================
def act_admin(sys_) -> None:
    banner("ACT 3  ADMINISTRATOR MODULE")
    admin_module = sys_.admin
    registrar = sys_.repos.users.find("A-01")   # has OVERRIDE_ENROLMENT
    clerk = sys_.repos.users.find("A-02")       # does not

    # -- Approvals (STATE 3) -------------------------------------------------
    step("3.1  Approve the pending grade submission")
    state = admin_module.approve_grades(registrar, sys_.demo_submission.submission_id)
    out(f"{sys_.demo_submission.submission_id} state = {state}")
    record = sys_.repos.records.find("S-01")
    out(f"S-01 academic record now holds {len(record.grades)} grades, GPA {record.calculate_gpa()}")
    out("Updating the records is the ENTRY ACTION of SubmittedState.")

    step("3.2  Approve the course change request -- the live section changes now")
    pending = admin_module.pending_change_requests()
    out(f"{len(pending)} request(s) awaiting approval")
    section = sys_.repos.sections.find("BUS210-A")
    out(f"BUS210-A capacity before approval: {section.total_capacity}")
    outcome = admin_module.approve_change(registrar, pending[0].request_id)
    out(f"Applied: {outcome}")
    out(f"BUS210-A capacity after approval:  {section.total_capacity}")
    out("Note the waitlist notification above: raising the capacity released a")
    out("seat, which the existing WaitlistObserver picked up with no extra code.")

    # -- Student & Faculty Management ---------------------------------------
    step("3.3  Account management")
    out(f"{len(admin_module.accounts.students())} students, "
        f"{len(admin_module.accounts.faculty())} faculty on file")
    admin_module.accounts.edit_account("S-03", phone="077-9999999")
    out(f"S-03 phone updated to {sys_.repos.users.find('S-03').phone}")
    admin_module.accounts.deactivate("S-03")
    out(f"S-03 active = {sys_.repos.users.find('S-03').is_active}")

    # -- Manual override (STRATEGY 1) ---------------------------------------
    step("3.4  Force-add into a full class -- the override composes a rule list")
    bus330 = sys_.repos.sections.find("BUS330-A")
    for _ in range(bus330.available_seats()):
        bus330.reserve_seat()                 # fill it completely for the demo
    out(f"BUS330-A is now {bus330.enrolled_count}/{bus330.total_capacity} -- full")
    out("")
    out(f"Standard student path:  {sys_.student.enrol('S-04', 'BUS330-A')}")
    out(f"Clerk (no rights):      {admin_module.force_add(clerk, 'S-04', 'BUS330-A')}")
    out(f"Registrar override:     {admin_module.force_add(registrar, 'S-04', 'BUS330-A')}")
    out(f"BUS330-A now {bus330.enrolled_count}/{bus330.total_capacity} -- over capacity by design")
    out("")
    out("The override validator is the SAME rule classes with CapacityRule left")
    out("out of the list. There is no 'if admin' branch inside any rule.")
    out("")
    out("Two guards had to agree: the rule list decides, and CourseSection's own")
    out("invariant is waived through force_reserve_seat(). Dropping the rule")
    out("alone would have failed at step 2 and rolled the force-add back.")

    # -- Reporting & Analytics (FACTORY METHOD 5 + BUILDER 7) ---------------
    step("3.5  Reports -- created through the factory, never by name")
    out(f"Report kinds registered: {len(admin_module.available_reports())}")
    for report_type in [
        ReportType.ENROLMENT_STATISTICS,
        ReportType.FACULTY_WORKLOAD,
        ReportType.COURSE_POPULARITY,
    ]:
        report, data = admin_module.run_report(report_type)
        print(f"\n        {report.title()}")
        print(data.as_table())

    step("3.6  The section 3.3 use case -- Business courses over 90% capacity")
    report, data = admin_module.run_report(
        ReportType.CAPACITY_THRESHOLD, {"school": "Business", "threshold": 0.9}
    )
    print(f"\n        {report.title()}  (school=Business, threshold=90%)")
    print(data.as_table())
    out("")
    out("Factory Method created the report; Builder built its criteria via the")
    out("Director's over_capacity_in_school() recipe -- the same builder the")
    out("student catalogue search uses.")
    out("")
    out("Same data as a spreadsheet export:")
    for line in data.as_csv().splitlines():
        out(f"  {line}")


# ===========================================================================
# ACT 4 -- THE PATTERN PROOFS
# ===========================================================================
def act_proofs(sys_) -> None:
    banner("ACT 4  PATTERN PROOFS -- each shows a pattern WORKING, not existing")

    # -- (a) COMMAND rollback ------------------------------------------------
    step("4.1  COMMAND (2) -- a forced mid-transaction failure rolls back cleanly")
    section = sys_.repos.sections.find("CS201-A")
    schedule_before = len(sys_.facade.view_schedule("S-02"))
    enrolments_before = len(sys_.repos.enrolments.find_by_student("S-02"))
    out(f"BEFORE   enrolledCount={section.enrolled_count}  "
        f"enrolments(S-02)={enrolments_before}  schedule days={schedule_before}")
    out("")
    out("Forcing step 3 of AddCourseCommand.execute() to raise. Steps 1 and 2")
    out("(create the enrolment, reserve the seat) will already have completed.")
    outcome = sys_.student.enrol("S-02", "CS201-A", fail_on_step=3)
    out(f"Result: {outcome}")
    out("")
    section_after = sys_.repos.sections.find("CS201-A")
    out(f"AFTER    enrolledCount={section_after.enrolled_count}  "
        f"enrolments(S-02)={len(sys_.repos.enrolments.find_by_student('S-02'))}  "
        f"schedule days={len(sys_.facade.view_schedule('S-02'))}")
    unchanged = (
        section_after.enrolled_count == section.enrolled_count
        and len(sys_.repos.enrolments.find_by_student("S-02")) == enrolments_before
    )
    out(f"NO PARTIAL STATE SURVIVED: {unchanged}")
    out("undo() ran in reverse order 3 -> 2 -> 1 on every completed step.")

    out("")
    out("The same command stack gives the administrator an audit log for free:")
    for line in sys_.tx.audit_log()[-4:]:
        out(f"  {line}")

    # -- (b) STATE illegal transition ---------------------------------------
    step("4.2  STATE (3) -- an illegal transition fails loudly")
    submission = sys_.demo_submission
    out(f"{submission.submission_id} is in {submission.state_name()} (terminal).")
    try:
        submission.add_entry(Grade("S-05", "CS-301", "A", Semester.FALL_2026))
        out("BUG: the call was allowed!")
    except IllegalTransition as exc:
        out(f"IllegalTransition raised: {exc}")

    out("")
    fresh = sys_.faculty.open_submission("F-01", "CS301-A", Semester.FALL_2026)
    fresh.add_entry(Grade("S-01", "CS-301", "B", Semester.FALL_2026))
    fresh.submit_for_approval()
    out(f"A second submission is now in {fresh.state_name()} -- the 'Pending' state.")
    try:
        fresh.add_entry(Grade("S-05", "CS-301", "A", Semester.FALL_2026))
        out("BUG: the call was allowed!")
    except IllegalTransition as exc:
        out(f"IllegalTransition raised: {exc}")
    out("The entry set is locked while an administrator decides. Nothing in")
    out("GradeSubmission checks a status flag -- the state object refused.")

    # -- (c) OBSERVER decoupling --------------------------------------------
    step("4.3  OBSERVER (4) -- a drop notifies, with no enrolment code involved")
    waitlist = sys_.repos.waitlists.for_section("BUS210-A")
    waitlist.add("S-04")
    out(f"BUS210-A waitlist: {waitlist.queue}")
    out("S-03 now drops BUS-210. Watch what fires:")
    out("")
    sys_.student.enrol("S-03", "BUS210-A")
    outcome = sys_.facade.drop("S-03", "BUS210-A")
    out("")
    out(f"Drop result: {outcome}")
    out("EnrollmentFacade.drop() published two events and returned. It holds no")
    out("reference to WaitlistObserver, AdvisorObserver or EmailChannel, and")
    out("never learns whether any notification was delivered.")

    step("4.4  OBSERVER (4) -- one broken subscriber cannot fail an enrolment")
    broken = WaitlistObserver(FailingChannel(), sys_.repos.waitlists, sys_.repos.users)
    sys_.publisher.attach(EventType.SEAT_RELEASED, broken)
    # Two names queued: the healthy observer pops the first, the broken one
    # pops the second and blows up trying to email them.
    sys_.repos.waitlists.for_section("CS350-A").add("S-05")
    sys_.repos.waitlists.for_section("CS350-A").add("S-02")
    out("Attached an observer whose channel always raises, then dropped a course:")
    out("")
    outcome = sys_.facade.drop("S-01", "CS350-A")
    out("")
    out(f"Drop still succeeded: {bool(outcome)}  ({outcome})")
    out(f"Publisher error log holds {len(sys_.publisher.error_log)} isolated failure(s).")
    out("A dead mail server cannot fail a transaction that already committed.")

    step("4.5  OBSERVER (4) -- adding a subscriber costs zero enrolment changes")
    out(f"AuditObserver (standing in for the future financial aid system) saw")
    out(f"all {len(sys_.audit.seen)} enrol/drop events without a single line of")
    out("enrolment code knowing it exists:")
    for event in sys_.audit.seen:
        out(f"  {event}")

    step("4.6  System-wide error alerting")
    sys_.publisher.publish(
        DomainEvent(
            EventType.SYSTEM_ERROR,
            {"source": "ReportingService", "detail": "read replica timed out"},
        )
    )
    out("Administrators alerted through the same publisher -- one mechanism,")
    out("three unrelated notification requirements.")


# ===========================================================================
def main() -> None:
    banner("NexusEnroll -- proof of concept\n"
           "Microservices + 3-Tier  |  7 design patterns  |  Fall 2026 semester")
    print("\nBuilding the object graph from the composition root...")
    system = build_system()
    print(f"        {len(system.repos.users.all())} people, "
          f"{len(system.repos.courses.all())} courses, "
          f"{len(system.repos.sections.all())} sections seeded")
    print(f"        Exactly one NotificationPublisher, injected everywhere "
          f"(no Singleton, no getInstance)")
    print(f"        Validation rules in play: {', '.join(system.validator.rule_names())}")

    act_student(system)
    act_faculty(system)
    act_admin(system)
    act_proofs(system)

    banner("DONE -- every requirement above traces to a pattern on diagram 03")
    print("""
    1 Strategy        EnrollmentValidator + 4 rules      Acts 1.4, 3.4
    2 Command         Add/DropCourseCommand + TxManager  Acts 1.3, 4.1
    3 State           GradeSubmission, CourseChangeReq   Acts 2.2-2.4, 3.1-3.2, 4.2
    4 Observer        NotificationPublisher + observers  Acts 4.3-4.6
    5 Factory Method  ReportFactory + 4 reports          Acts 3.5, 3.6
    6 Facade          EnrollmentFacade                   Acts 1.3, 1.5, 4.1, 4.3
    7 Builder         CourseSearchQueryBuilder+Director  Acts 1.1, 1.2, 3.6

    Singleton: considered, rejected, replaced by the composition root.
    """)


if __name__ == "__main__":
    main()
