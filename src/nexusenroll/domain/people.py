"""User Management context -- Person and its three subclasses.

Diagram 02, USER MANAGEMENT CONTEXT band.

DRY: firstName / lastName / email / phone / isActive / getFullName() /
deactivate() are declared once on Person and inherited, rather than repeated
on Student, Faculty and Administrator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .enums import AcademicStanding, Role


@dataclass
class Contact:
    """Value object returned by Person.getContactInfo()."""

    email: str
    phone: str

    def __str__(self) -> str:  # pragma: no cover - display only
        return f"{self.email} / {self.phone}"


@dataclass
class Person(ABC):
    """«abstract» Person -- diagram 02.

    Encapsulation note: `is_active` is only ever flipped by `deactivate()` /
    `reactivate()`, never assigned from outside.
    """

    person_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    is_active: bool = True

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_contact_info(self) -> Contact:
        return Contact(self.email, self.phone)

    def deactivate(self) -> None:
        """Administrator module: "deactivate student and faculty accounts"."""
        self.is_active = False

    def reactivate(self) -> None:
        self.is_active = True

    @abstractmethod
    def get_role(self) -> Role:
        """Polymorphic -- each subclass answers for itself."""


@dataclass
class Student(Person):
    student_id: str = ""
    enrolment_year: int = 2026
    standing: AcademicStanding = AcademicStanding.GOOD
    program_id: str = ""
    advisor_id: str | None = None

    def get_role(self) -> Role:
        return Role.STUDENT


@dataclass
class Faculty(Person):
    faculty_id: str = ""
    department: str = ""
    title: str = "Lecturer"
    advisee_ids: list[str] = field(default_factory=list)

    def get_role(self) -> Role:
        return Role.FACULTY

    def get_advisees(self) -> list[str]:
        return list(self.advisee_ids)


@dataclass
class Administrator(Person):
    admin_id: str = ""
    permissions: set[str] = field(default_factory=set)

    def get_role(self) -> Role:
        return Role.ADMINISTRATOR

    def can_override_enrolment(self) -> bool:
        """Gate for the "force-add a student into a full class" requirement."""
        return "OVERRIDE_ENROLMENT" in self.permissions
