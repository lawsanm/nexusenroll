# NexusEnroll — Proof of Concept (Part B6)

SCS 2303 Software Architecture, Assignment 3. **Python 3.10+, no third-party dependencies.**

```bash
cd src
python -m nexusenroll.main
```

(`python src/nexusenroll/main.py` also works — the script inserts its own parent on `sys.path`.)

---

## What you are looking at

This package **is** the Business Logic layer — tier 2 of the 3-Tier structure that sits inside
each microservice on `DESIGN/diagrams/01-architecture.drawio`. Presentation is a console script
and persistence is in-memory, because the brief asks Part B to focus on the business tier and
makes UI optional.

| Package | Role | Diagram |
|---|---|---|
| `domain/` | Business entities and their invariants | 02 |
| `patterns/` | The seven design patterns, one module each | 03 |
| `repositories/` | `I*Repository` interfaces + in-memory implementations | 01 (data access tier) |
| `services/` | The student, faculty and administrator modules | — |
| `composition_root.py` | The single place objects are wired together | 03, rejected-patterns panel |
| `seed.py` | Demo data shaped so every rule can be shown failing | — |
| `main.py` | Runnable user stories and pattern proofs | 04, 05, 06 |

Every module in `patterns/` opens with a banner naming the pattern's **GoF roles**, the
**requirement it satisfies**, and **what would go wrong without it** — the same
pattern → where → why → what-breaks shape used in `DESIGN/01-design-patterns.md`.

---

## The seven patterns

| # | Pattern | Family | Module | Seen in the demo |
|---|---|---|---|---|
| ① | Strategy | Behavioural | `patterns/strategy_validation.py` | acts 1.4, 3.4 |
| ② | Command | Behavioural | `patterns/command_enrollment.py` | acts 1.3, 4.1 |
| ③ | State | Behavioural | `patterns/state_grades.py`, `patterns/state_course_change.py` | acts 2.2–2.4, 3.1–3.2, 4.2 |
| ④ | Observer | Behavioural | `patterns/observer_notifications.py` | acts 4.3–4.6 |
| ⑤ | Factory Method | Creational | `patterns/factory_reports.py` | acts 3.5, 3.6 |
| ⑥ | Facade | Structural | `patterns/facade_enrollment.py` | acts 1.3, 1.5, 4.1, 4.3 |
| ⑦ | Builder | Creational | `patterns/builder_search.py` | acts 1.1, 1.2, 3.6 |

**Singleton was considered and deliberately rejected.** `composition_root.py` opens with the
full reasoning: it constructs exactly one `NotificationPublisher` and injects that same
reference everywhere, giving an identical uniqueness guarantee with no global access point, no
hidden dependency, and every dependency visible in a constructor signature.

---

## What the demo proves, rather than describes

Act 4 exists because a working pattern is more convincing than a narrated one:

- **4.1 — Command rollback.** Step 3 of `AddCourseCommand.execute()` is forced to raise after
  steps 1 and 2 have already changed state. The act prints `enrolledCount`, the enrolment count
  and the schedule before and after, all unchanged.
- **4.2 — State guard.** `addEntry()` is called on a submission in `PendingApprovalState` and
  again on one in `SubmittedState`. Both raise `IllegalTransition`. Nothing in `GradeSubmission`
  checks a status flag — the state object refuses.
- **4.3–4.5 — Observer decoupling.** A drop publishes two events and returns; the waitlist and
  advisor emails fire with no enrolment code involved. 4.4 attaches a deliberately broken
  observer and shows the drop still succeeding. 4.5 shows a late-added subscriber having seen
  every event without a line of enrolment code knowing it exists.

Act 4.1 is worth reading the git history for: the first run printed
`NO PARTIAL STATE SURVIVED: False` and exposed a real bug in `TransactionManager` — commands
were pushed onto the rollback stack only *after* `execute()` returned, so a command that failed
part-way through was never undone. Fixed by pushing before executing.

---

## Where each design principle is demonstrated

| Principle | Look at |
|---|---|
| Encapsulation | `CourseSection._enrolled_count`, mutated only via `reserve_seat()` / `release_seat()` |
| Programming to an Interface | `EnrollmentValidator` — no import of, and no `isinstance` against, any concrete rule |
| Composition over Inheritance | `CourseSection` composes `TimeSlot`; the validator composes rules instead of subclassing |
| Single Responsibility | validator / command / transaction manager / publisher are four classes, four reasons to change |
| Open/Closed | `CreditLimitRule` — a new class and one `add_rule()` call, zero edits elsewhere |
| Liskov Substitution | `repositories/in_memory.py` honours the interface contracts exactly (empty list, never `None`) |
| Interface Segregation | `ValidationRule`, `EnrollmentCommand`, `EventObserver`, `NotificationChannel`, `Report` |
| Dependency Inversion | `repositories/interfaces.py` is owned by the business layer; `EnrollmentFacade` injects everything |
| DRY | one validation loop; one State shape serving two workflows |
| KISS | local transaction over a Saga; in-memory repositories over a database |
| Fail Fast | `CourseSearchQueryBuilder.build()`; `GradeState` defaults raising `IllegalTransition` |
