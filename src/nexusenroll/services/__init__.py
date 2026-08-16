"""The three modules the brief requires: student, faculty and administrator.

Each module COMPOSES pattern participants rather than reimplementing their
logic, which is what "show how the design patterns are integrated into the
three modules' logic" means in practice:

    StudentModule        -> Builder (7), Facade (6) -> Strategy (1),
                            Command (2), Observer (4)
    FacultyModule        -> State (3) twice, Observer (4)
    AdministratorModule  -> Factory Method (5), Builder (7), Strategy (1)
                            via the override rule list, State (3) for approvals
"""
