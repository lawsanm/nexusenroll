"""FACULTY MODULE -- class rosters, grade submission, course change requests.

Patterns visible here:
    State (3) -- twice: the GradeSubmission lifecycle, and CourseChangeRequest
    Observer (4) -- GradesSubmitted is published once records are updated
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

from ..domain.enums import ChangeType
from ..domain.records import Grade
from ..patterns.state_course_change import new_change_request
from ..patterns.state_grades import BatchGradeProcessor, new_grade_submission

_submission_ids = itertools.count(1)
_request_ids = itertools.count(1)


@dataclass
class RosterEntry:
    """"Roster includes student names, IDs, and contact information"."""

    student_id: str
    name: str
    email: str
    phone: str
    status: str


class FacultyModule:
    def __init__(
        self,
        section_repo,
        enrol_repo,
        user_repo,
        record_repo,
        submission_repo,
        change_repo,
        processor: BatchGradeProcessor,
    ) -> None:
        self._sections = section_repo
        self._enrolments = enrol_repo
        self._users = user_repo
        self._records = record_repo
        self._submissions = submission_repo
        self._changes = change_repo
        self._processor = processor

    # -- Class Roster Viewing ------------------------------------------------
    def roster(self, faculty_id: str, section_id: str) -> list[RosterEntry]:
        """"View a real-time list of students enrolled in their courses."

        Real-time because it reads live off the enrolment repository -- there
        is no cached roster to go stale.
        """
        section = self._sections.find(section_id)
        if section is None or section.instructor_id != faculty_id:
            return []  # a lecturer sees only their own sections

        entries = []
        for enrolment in self._enrolments.find_by_section(section_id):
            student = self._users.find(enrolment.student_id)
            if student is None:
                continue
            entries.append(
                RosterEntry(
                    student_id=enrolment.student_id,
                    name=student.get_full_name(),
                    email=student.email,
                    phone=student.phone,
                    status=enrolment.status.value,
                )
            )
        return sorted(entries, key=lambda e: e.name)

    def my_sections(self, faculty_id: str):
        return self._sections.find_by_instructor(faculty_id)

    # -- Grade Submission (State pattern 3) ---------------------------------
    def open_submission(self, faculty_id: str, section_id: str, semester):
        """Creates a submission in DraftState -- the initial pseudostate."""
        submission = new_grade_submission(
            f"GS-{next(_submission_ids):03d}", section_id, faculty_id, semester
        )
        self._submissions.save(submission)
        return submission

    def enter_batch(self, submission, grades: list[Grade]) -> list[tuple[Grade, str]]:
        """"Batch grade submission processing" with ERROR ISOLATION.

        The processor validates PER ENTRY, so one bad letter grade in a roster
        of 200 rejects one entry, not 200.  Accepted entries are added to the
        submission immediately; rejected ones are handed back with a reason so
        the professor can correct just those.
        """
        accepted, rejected = self._processor.validate_batch(submission, grades)
        for grade in accepted:
            submission.add_entry(grade)  # delegates to DraftState
        submission.rejected_entries = rejected
        self._submissions.save(submission)
        return rejected

    def submit_for_approval(self, submission) -> str:
        """Draft -> PendingApproval.  The "Pending" state the brief names."""
        submission.submit_for_approval()
        self._submissions.save(submission)
        return submission.state_name()

    def correct(self, submission, grade: Grade) -> str:
        """Legal only in PartiallyRejectedState (or Draft).

        Calling it in PendingApprovalState raises IllegalTransition -- the
        accepted entries stay untouched throughout, which is the requirement
        "allow the professor to correct it without losing other submitted
        grades".
        """
        submission.correct_entry(grade)
        self._submissions.save(submission)
        return submission.state_name()

    # -- Course Information Management (State pattern 3, second application) -
    def request_change(
        self, faculty_id: str, section_id: str, change_type: ChangeType, **payload
    ):
        """"Instructors can submit requests to update course descriptions, add
        prerequisites, or change course capacity (these requests must be
        approved by an administrator)."

        The request is created in Draft and submitted, landing in
        PendingAdminApproval.  The live CourseSection is NOT touched here -- it
        is only mutated on entry to ApprovedState, by the administrator module.
        """
        request = new_change_request(
            f"CR-{next(_request_ids):03d}", section_id, faculty_id, change_type, payload
        )
        request.submit()
        self._changes.save(request)
        return request

    def my_requests(self, faculty_id: str):
        return [r for r in self._changes.all() if r.requested_by == faculty_id]
