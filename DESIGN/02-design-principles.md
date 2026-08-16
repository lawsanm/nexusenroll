# Part B5 — Software Design Principles: Concrete Examples

The brief requires:
> *"Ensure your final design adheres to widely accepted software design principles
> (Encapsulation, Programming to an Interface, Composition over Inheritance, SOLID principles,
> etc). **Provide at least one concrete example in your design demonstrating adherence to each
> principle.**"*

"Concrete" is the operative word — each entry below names a specific class and explains the
mechanism, not the definition. Every example is visible on one of the six diagrams.

---

## Encapsulation

**Example: `CourseSection` seat counting.**

```
- totalCapacity: int      (private)
- enrolledCount: int      (private)
+ availableSeats(): int
+ hasAvailableSeat(): bool
+ reserveSeat(): void     raises CapacityExceeded if full
+ releaseSeat(): void     raises IllegalState if already zero
```

The invariant `0 ≤ enrolledCount ≤ totalCapacity` is enforced **inside** the object.
`enrolledCount` is never assigned from outside; the only mutators are `reserveSeat()` and
`releaseSeat()`, each of which validates first. No caller — not the facade, not a command, not
a repository — can put a section into an impossible state.

**Why this example is strong:** the requirement *"Available seats vs. total capacity"* is
displayed to every student browsing the catalogue and is one of the three validation rules.
A corrupted seat count would produce visibly wrong data across the whole system. Encapsulating
it is the difference between an invariant and a hope.

*Diagram: `02-class-diagram-domain`, `CourseSection`.*

---

## Programming to an Interface

**Example: `EnrollmentValidator` depends on `ValidationRule`, never on a concrete rule.**

```python
class EnrollmentValidator:
    def __init__(self, rules: list[ValidationRule]):   # the abstraction
        self._rules = rules

    def validate_all(self, request) -> ValidationResult:
        result = ValidationResult()
        for rule in self._rules:                       # no isinstance, no type check
            result.merge(rule.validate(request, self._ctx))
        return result
```

The validator has no import of, and no knowledge of, `PrerequisiteRule`, `CapacityRule` or
`TimeConflictRule`. It knows only that each element honours the `ValidationRule` contract.

**Second instance:** `EnrollmentFacade` declares `IEnrollmentRepository`, not
`SqlEnrollmentRepository`. The business logic layer is written against a repository interface
it defines itself, and the data access layer implements it.

*Diagrams: `03-class-diagram-patterns` zones ① and ⑥.*

---

## Composition over Inheritance

**Example: `CourseSection` composes `TimeSlot` objects.**

The rejected alternative was an inheritance hierarchy —
`ScheduledEntity` → `WeeklyScheduledEntity` → `TwiceWeeklySection` — to express meeting
patterns. Instead, a section **holds** a `List<TimeSlot>`:

- A course meeting Monday and Wednesday is *two `TimeSlot` objects*, not a different class.
- Adding a lab session is a data change, not a code change.
- `hasConflictWith()` is one loop over slots, identical for every meeting pattern.

**Second, stronger instance:** `EnrollmentValidator` **composes** its rules rather than being
subclassed per rule set. Standard student enrolment, administrator override enrolment, and
(future) graduate enrolment are three *different rule lists* passed into the same class — not
three subclasses of a `BaseValidator`. An inheritance approach would need a new subclass per
combination, and combinations multiply.

*Diagrams: `02-class-diagram-domain` (`CourseSection ◆── TimeSlot`); `03` zone ①.*

---

## S — Single Responsibility Principle

**Example: the four separated responsibilities of enrolment.**

Enrolling a student involves four genuinely different kinds of work, and each has its own
class with one reason to change:

| Class | Sole responsibility | Changes when… |
|---|---|---|
| `EnrollmentValidator` | decide whether an enrolment is permitted | the university changes its rules |
| `AddCourseCommand` | perform and reverse the state changes | the data model changes |
| `TransactionManager` | guarantee atomicity | the transaction strategy changes |
| `NotificationPublisher` | distribute events | recipients change |

A single `EnrollmentService.enrol()` doing all four would have four unrelated reasons to change
and would be the file every team member edits simultaneously.

**Second instance:** `CourseChangeRequest` is a separate entity rather than approval fields
bolted onto `CourseSection`. `CourseSection` describes an offering; `CourseChangeRequest`
tracks an approval workflow. Different responsibilities, different lifecycles, different
classes.

---

## O — Open/Closed Principle

**Example: adding a fourth validation rule.**

To enforce a new maximum-credits-per-semester rule:

```python
class CreditLimitRule(ValidationRule):        # 1. new file
    def validate(self, req, ctx): ...

validator.add_rule(CreditLimitRule(...))      # 2. one line at composition
```

Files modified: **zero.** `EnrollmentValidator`, `EnrollmentFacade`, the existing three rules,
and every caller are untouched. The system is *open* to a new rule and *closed* to
modification.

**Second instance, at architecture scale:** adding the financial aid system as a
`StudentEnrolled` consumer requires no change to the Enrolment Service. Same principle, same
mechanism (polymorphic dispatch over a stable abstraction), two different scales — worth
noting in the report because it links Part A to Part B.

**Third instance:** a new report type is a new `Report` subclass plus one `register()` call.

---

## L — Liskov Substitution Principle

**Example: `InMemoryEnrollmentRepository` substitutes for `SqlEnrollmentRepository`.**

The proof-of-concept runs entirely on in-memory repositories; production would use SQL ones.
Both honour `IEnrollmentRepository` such that **no calling code can distinguish them**:

- `save()` returns nothing and never raises on a valid entity in either implementation.
- `findByStudent()` returns an empty list — never `None` — when there are no matches in both.
- Neither strengthens the interface's preconditions or weakens its postconditions.

This is why the same `EnrollmentFacade` object runs unmodified in the demo and in production —
a substitutability claim we can actually demonstrate rather than assert.

**Second instance:** every `ValidationRule` returns a `ValidationResult` and never raises on a
merely-invalid request. `PrerequisiteRule` does not signal failure by throwing while
`CapacityRule` returns a value — if they differed, `validate_all()`'s uniform loop would break
for one subtype, which is exactly the LSP violation to avoid.

---

## I — Interface Segregation Principle

**Example: `ValidationRule` and `EventObserver` are deliberately one-method interfaces.**

The rejected alternative was one fat `IEnrolmentComponent` with
`validate()`, `execute()`, `undo()`, `onEvent()` and `generate()`. Under that design
`CapacityRule` would be forced to implement `undo()` and `onEvent()` as no-op stubs — a classic
ISP violation, where a client depends on methods it does not use.

Instead the abstractions are minimal and role-specific:

| Interface | Methods | Implemented by |
|---|---|---|
| `ValidationRule` | `validate`, `ruleName` | the three rules |
| `EnrollmentCommand` | `execute`, `undo`, `describe` | the two commands |
| `EventObserver` | `onEvent`, `interestedIn` | the three observers |
| `NotificationChannel` | `send` | `EmailChannel`, future `SmsChannel` |
| `Report` | `generate`, `title`, `export` | the four reports |

No class implements a method it does not need.

**Second instance, at API scale:** the API Gateway exposes role-specific endpoint groups
(`/students/…`, `/faculty/…`, `/admin/…`) rather than one god-API, so a mobile student client
is not coupled to administrator operations.

---

## D — Dependency Inversion Principle

**Example: the Business Logic layer owns the repository interfaces.**

The direction of the dependency is the whole point:

```
Business Logic layer  ──declares──►  IEnrollmentRepository   (abstraction)
                                              ▲
                                              │ implements
Data Access layer     ────────────────────────┘
```

`IEnrollmentRepository` is **declared in the business logic layer**, not in the data access
layer. The high-level policy (enrolment rules) does not depend on the low-level detail
(persistence); both depend on an abstraction that the policy owns. Swapping SQL for MongoDB
touches only the data access layer.

Every collaborator of `EnrollmentFacade` arrives by constructor injection:

```python
class EnrollmentFacade:
    def __init__(self, validator: EnrollmentValidator,
                       tx_manager: TransactionManager,
                       publisher:  NotificationPublisher,
                       enrol_repo: IEnrollmentRepository): ...
```

No `new`, no `getInstance()`, no import of a concrete class anywhere in the class body.

**This principle is why we rejected Singleton.** An earlier draft used
`NotificationService.getInstance()` to guarantee one observer registry. That would have made
every call site depend on a concrete class through a dependency invisible in the constructor
signature — a direct DIP violation, in the very document where we claim DIP adherence. We now
get the single-instance guarantee from the **composition root** instead: `composition_root.py`
constructs one `NotificationPublisher` and injects that reference everywhere. Same guarantee, no
global access point. Full reasoning in §6 of `01-design-patterns.md`.

---

## DRY — Don't Repeat Yourself

**Example: the validation loop exists once.**

`EnrollmentValidator.validate_all()` is the only place rules are iterated and results merged.
Student self-service enrolment, administrator force-add, and waitlist auto-promotion all route
through it with different rule lists. Without Strategy, each of those three entry points would
carry its own copy of the checks — and they would drift.

**Second instance:** `Person` holds `firstName`, `lastName`, `email`, `phone`, `isActive`,
`getFullName()` and `deactivate()` once, inherited by `Student`, `Faculty` and `Administrator`
rather than repeated three times.

**Third instance, design-level:** one State pattern implementation shape serves both
`GradeSubmission` and `CourseChangeRequest`.

---

## KISS — Keep It Simple, Stupid

Three places we deliberately chose the simpler option, and why:

1. **Local ACID transaction instead of a Saga.** We drew the Enrolment Service boundary so
   that all three state changes in the transaction requirement fall inside one service. A Saga
   with compensating transactions would have been the "sophisticated" microservices answer and
   strictly worse: more moving parts, more failure modes, no additional capability.

2. **API Gateway + message broker instead of an ESB.** We get SOA's integration benefit
   without ESB governance overhead or its central throughput bottleneck.

3. **In-memory repositories in the proof-of-concept.** The brief asks for *"a small, runnable
   proof-of-concept"* demonstrating the **design**. A database adds setup friction and
   demonstrates nothing about the patterns. Because of DIP and LSP, this simplification costs
   nothing architecturally — the same business logic runs against either implementation.

**The KISS trap we avoided.** Seven patterns could itself be over-engineering. Each one here
is traceable to a sentence in the requirements document (see `01-design-patterns.md`); none was
added for its own sake. Being able to say *why each pattern exists* is what separates applying
patterns from collecting them.

---

## Additional principles worth one line each

| Principle | Where |
|---|---|
| **Separation of Concerns** | Enforced twice — horizontally across six services, vertically across three tiers |
| **Law of Demeter** | `EnrollmentFacade` calls `validator.validateAll(req)`, never `validator.getRules()[0].getRepo()...` |
| **Tell, Don't Ask** | `section.reserveSeat()` rather than reading `enrolledCount`, incrementing, and writing back |
| **Fail Fast** | `GradeState` base methods raise `IllegalTransition` instead of silently ignoring an illegal call |
| **Composition Root** | All object wiring happens in `composition_root.py`; no class constructs its own dependencies — this is also what replaced the rejected Singleton |

---

## Traceability matrix — principle → class → diagram

| Principle | Primary example | Diagram |
|---|---|---|
| Encapsulation | `CourseSection` seat counters | 02 |
| Programming to an Interface | `EnrollmentValidator` → `ValidationRule` | 03 zone ① |
| Composition over Inheritance | `CourseSection ◆── TimeSlot` | 02 |
| Single Responsibility | validator / command / tx manager / publisher split | 03 all zones |
| Open/Closed | adding `CreditLimitRule` | 03 zone ① |
| Liskov Substitution | `InMemory…` vs `Sql…Repository` | 03 zone ⑥ |
| Interface Segregation | five single-purpose interfaces | 03 all zones |
| Dependency Inversion | `IEnrollmentRepository` declared in business layer | 03 zone ⑥ · 01 |
| DRY | one validation loop | 03 zone ① |
| KISS | local transaction over Saga | 01 · 00 §A2.7 |
| Fail Fast | `Builder.build()` validates, so no invalid `CourseSearchQuery` can exist | 03 zone ⑦ |
