"""The seven design patterns, one module per pattern.

    1 Strategy       «Behavioural»  strategy_validation.py
    2 Command        «Behavioural»  command_enrollment.py
    3 State          «Behavioural»  state_grades.py, state_course_change.py
    4 Observer       «Behavioural»  observer_notifications.py
    5 Factory Method «Creational»   factory_reports.py
    6 Facade         «Structural»   facade_enrollment.py
    7 Builder        «Creational»   builder_search.py

All three GoF families are covered, against a required minimum of three
patterns.  Each module opens with a banner naming the pattern's GoF roles, the
requirement it satisfies, and what would go wrong without it.

Singleton was considered and DELIBERATELY REJECTED -- it conflicts with SRP,
DIP and OCP, and the composition root in composition_root.py already gives the same
single-instance guarantee with none of the cost.  Full reasoning in
DESIGN/01-design-patterns.md section 6 and on diagram 03's rejected-patterns
panel.
"""
