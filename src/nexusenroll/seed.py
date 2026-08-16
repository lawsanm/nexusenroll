"""Seed data for the proof-of-concept.

Deliberately shaped so that every requirement can be demonstrated:

  * CS-301 has a prerequisite (CS-201)  -> PrerequisiteRule can fail
  * BUS-210 section BUS210-A is FULL    -> CapacityRule can fail and waitlist
  * BUS-330 sits at 92% capacity        -> the >90% administrator report
  * MAT-105 clashes with CS-101 on Mon  -> TimeConflictRule can fail
  * one student is missing a prerequisite, one has completed everything
"""

from __future__ import annotations

from datetime import time

from .domain.catalog import Course, CourseSection, DegreeProgram, Prerequisite, TimeSlot
from .domain.enums import DayOfWeek, Semester
from .domain.people import Administrator, Faculty, Student
from .domain.records import AcademicRecord, Grade

SEMESTER = Semester.FALL_2026


def seed(repos) -> None:
    """`repos` is the Repositories bundle built by the composition root."""
    _seed_people(repos)
    _seed_courses(repos)
    _seed_programs(repos)
    _seed_sections(repos)
    _seed_records(repos)


# ---------------------------------------------------------------------------
def _seed_people(repos) -> None:
    faculty = [
        Faculty("F-01", "Nimal", "Silva", "silva@nexus.edu", "011-2200101",
                faculty_id="F-01", department="Computer Science", title="Professor",
                advisee_ids=["S-01", "S-02"]),
        Faculty("F-02", "Ayesha", "Perera", "perera@nexus.edu", "011-2200102",
                faculty_id="F-02", department="Computer Science", title="Senior Lecturer"),
        Faculty("F-03", "Rohan", "Fernando", "fernando@nexus.edu", "011-2200103",
                faculty_id="F-03", department="Business", title="Lecturer"),
    ]

    students = [
        # S-01 has completed CS-201, so CS-301's prerequisite is satisfied.
        Student("S-01", "Kavith", "Jayawardena", "kavith@nexus.edu", "077-1000001",
                student_id="S-01", program_id="P-CS", advisor_id="F-01"),
        # S-02 has NOT completed CS-201 -> PrerequisiteRule will refuse CS-301.
        Student("S-02", "Dilini", "Ratnayake", "dilini@nexus.edu", "077-1000002",
                student_id="S-02", program_id="P-CS", advisor_id="F-01"),
        Student("S-03", "Tharindu", "Bandara", "tharindu@nexus.edu", "077-1000003",
                student_id="S-03", program_id="P-BUS", advisor_id="F-03"),
        Student("S-04", "Nethmi", "Gunasekara", "nethmi@nexus.edu", "077-1000004",
                student_id="S-04", program_id="P-BUS", advisor_id="F-03"),
        Student("S-05", "Isuru", "Wickrama", "isuru@nexus.edu", "077-1000005",
                student_id="S-05", program_id="P-CS", advisor_id="F-02"),
    ]

    admins = [
        Administrator("A-01", "Sanduni", "Alwis", "registrar@nexus.edu", "011-2200900",
                      admin_id="A-01", permissions={"OVERRIDE_ENROLMENT", "APPROVE"}),
        # Deliberately WITHOUT override rights, to show the permission guard.
        Administrator("A-02", "Kasun", "Herath", "clerk@nexus.edu", "011-2200901",
                      admin_id="A-02", permissions={"APPROVE"}),
    ]

    for person in faculty + students + admins:
        repos.users.save(person)


def _seed_courses(repos) -> None:
    courses = [
        Course("CS-101", "Introduction to Programming",
               "Fundamentals of programming and problem solving with Python.",
               3, "Computer Science", "Computing"),
        Course("CS-201", "Data Structures",
               "Lists, trees, graphs, hashing and their complexity analysis.",
               3, "Computer Science", "Computing",
               [Prerequisite("CS-101", "C")]),
        Course("CS-301", "Algorithms",
               "Design and analysis of algorithms, greedy and dynamic programming.",
               4, "Computer Science", "Computing",
               [Prerequisite("CS-201", "C")]),
        Course("CS-350", "Software Architecture",
               "Architectural patterns, design patterns and quality attributes.",
               3, "Computer Science", "Computing"),
        Course("MAT-105", "Discrete Mathematics",
               "Logic, sets, relations, combinatorics and graph theory.",
               3, "Mathematics", "Science"),
        Course("BUS-210", "Principles of Marketing",
               "Market analysis, segmentation and the marketing mix.",
               3, "Marketing", "Business"),
        Course("BUS-330", "Corporate Finance",
               "Capital structure, valuation and investment appraisal.",
               3, "Finance", "Business"),
        Course("BUS-410", "Strategic Management",
               "Competitive strategy and organisational capability.",
               3, "Management", "Business"),
    ]
    for course in courses:
        repos.courses.save(course)


def _seed_programs(repos) -> None:
    repos.programs.save(
        DegreeProgram("P-CS", "BSc Computer Science", 60,
                      ["CS-101", "CS-201", "CS-301", "CS-350", "MAT-105"])
    )
    repos.programs.save(
        DegreeProgram("P-BUS", "BBA Business Administration", 60,
                      ["BUS-210", "BUS-330", "BUS-410"])
    )


def _seed_sections(repos) -> None:
    def slot(day, start, end, room):
        return TimeSlot(day, time(start, 0), time(end, 0), room)

    sections = [
        # CS-101: Mon/Wed 09:00 -- clashes with MAT-105 on Monday.
        CourseSection("CS101-A", "CS-101", SEMESTER, "F-02", 40,
                      [slot(DayOfWeek.MON, 9, 11, "LT-1"),
                       slot(DayOfWeek.WED, 9, 11, "LT-1")]),
        CourseSection("CS201-A", "CS-201", SEMESTER, "F-01", 35,
                      [slot(DayOfWeek.TUE, 10, 12, "LT-2")]),
        CourseSection("CS301-A", "CS-301", SEMESTER, "F-01", 30,
                      [slot(DayOfWeek.THU, 13, 15, "LT-3")]),
        CourseSection("CS350-A", "CS-350", SEMESTER, "F-01", 25,
                      [slot(DayOfWeek.FRI, 9, 12, "LAB-1")]),
        # MAT-105 deliberately overlaps CS101-A on Monday morning.
        CourseSection("MAT105-A", "MAT-105", SEMESTER, "F-02", 50,
                      [slot(DayOfWeek.MON, 10, 12, "LT-4")]),
        # BUS210-A is FULL -- seeded to capacity below.
        CourseSection("BUS210-A", "BUS-210", SEMESTER, "F-03", 3,
                      [slot(DayOfWeek.TUE, 14, 16, "LT-5")]),
        # BUS330-A sits at 92% -- the >90% capacity report use case.
        CourseSection("BUS330-A", "BUS-330", SEMESTER, "F-03", 25,
                      [slot(DayOfWeek.WED, 14, 16, "LT-5")]),
        CourseSection("BUS410-A", "BUS-410", SEMESTER, "F-03", 40,
                      [slot(DayOfWeek.THU, 9, 11, "LT-6")]),
    ]
    for section in sections:
        repos.sections.save(section)

    # Pre-fill occupancy through the PUBLIC API (reserve_seat), never by
    # assigning to the private counter -- the encapsulation point holds even
    # for test fixtures.
    for _ in range(3):
        repos.sections.find("BUS210-A").reserve_seat()   # 3/3   -> full
    for _ in range(23):
        repos.sections.find("BUS330-A").reserve_seat()   # 23/25 -> 92%
    for _ in range(18):
        repos.sections.find("CS101-A").reserve_seat()
    for _ in range(12):
        repos.sections.find("BUS410-A").reserve_seat()


def _seed_records(repos) -> None:
    records = {
        "S-01": AcademicRecord("S-01", "P-CS", [
            Grade("S-01", "CS-101", "A", Semester.SPRING_2026),
            Grade("S-01", "CS-201", "B+", Semester.SPRING_2026),
        ]),
        # S-02 stopped at CS-101 -- CS-301 is therefore out of reach.
        "S-02": AcademicRecord("S-02", "P-CS", [
            Grade("S-02", "CS-101", "B", Semester.SPRING_2026),
        ]),
        "S-03": AcademicRecord("S-03", "P-BUS", [
            Grade("S-03", "BUS-210", "A-", Semester.SPRING_2026),
        ]),
        "S-04": AcademicRecord("S-04", "P-BUS", []),
        "S-05": AcademicRecord("S-05", "P-CS", [
            Grade("S-05", "CS-101", "A", Semester.SPRING_2026),
            Grade("S-05", "CS-201", "A-", Semester.SPRING_2026),
        ]),
    }
    for record in records.values():
        repos.records.save(record)
