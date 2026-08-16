# Part B2–B3 — Design Patterns: Identification & Justification

**Weighting: 40% of the total grade — the single largest criterion.**

The brief requires *"a minimum of three distinct object-oriented design patterns"*, that we
*"identify the patterns"*, and that for each we *"explain where and why"* we use it. We apply
**seven**, covering all three GoF families.

The brief's own worked example of the expected phrasing is:
> *"I am using the {PATTERN} to notify the student's academic advisor and the billing system
> whenever a student successfully enrols in a course."*

Every entry below follows that shape: **pattern → where → why → what would go wrong without it.**

---

## Summary table

| # | Pattern | Family | Where it is used | Requirement it satisfies |
|---|---|---|---|---|
| ① | **Strategy** | Behavioural | `EnrollmentValidator` + `ValidationRule` hierarchy | §3.1 the three enrolment validation rules |
| ② | **Command** | Behavioural | `AddCourseCommand` / `DropCourseCommand` + `TransactionManager` | §4 transaction management — all-or-nothing |
| ③ | **State** | Behavioural | `GradeSubmission` + `GradeState` hierarchy; reused for `CourseChangeRequest` | §3.2 grade approval "Pending" → "Submitted" |
| ④ | **Observer** | Behavioural | `NotificationPublisher` + `EventObserver` hierarchy | §4 notification, *"decoupled from the core enrolment logic"* |
| ⑤ | **Factory Method** | Creational | `ReportFactory` + `Report` hierarchy | §3.3 administrator reporting & analytics |
| ⑥ | **Facade** | Structural | `EnrollmentFacade` | §4 SPA/mobile share one back-end API |
| ⑦ | **Builder** | Creational | `CourseSearchQueryBuilder` + `CatalogQueryDirector` → `CourseSearchQuery` | §3.1 multi-criteria catalogue search |

Family coverage: **Creational** ⑤⑦ · **Structural** ⑥ · **Behavioural** ①②③④

§6 records the patterns we **considered and deliberately rejected**, including Singleton and why
it did not survive review. That section is part of the argument, not an appendix — the brief
asks us to justify design choices, and a justified rejection is a design choice.

---

## ① Strategy «Behavioural»

**Where.** In the Enrolment Service business logic layer. `ValidationRule` is the Strategy
interface; `PrerequisiteRule`, `CapacityRule` and `TimeConflictRule` are ConcreteStrategies;
`EnrollmentValidator` is the Context holding a `List<ValidationRule>`.

**Report sentence.**
> *We are using the **Strategy** pattern to encapsulate each of the three enrolment validation
> rules — prerequisite, capacity and time-conflict — as an interchangeable algorithm, so that
> the validator can run all of them uniformly and new rules can be added without modifying it.*

**Why.** The requirements list three validation rules under one heading, and they are
structurally identical: each takes an `EnrollmentRequest`, inspects some state, and returns a
pass/fail with a reason. That is the textbook signature of a family of interchangeable
algorithms. Making each a class buys three things:

1. **Open/Closed compliance.** A credit-limit rule or an academic-standing rule is a new class
   plus one `addRule()` call. `EnrollmentValidator` is never edited.
2. **Independent testability.** `TimeConflictRule` can be unit-tested against two overlapping
   `TimeSlot` objects with no database, no student, and no enrolment.
3. **Aggregate error reporting.** Because the Context iterates rather than short-circuits, the
   student is told *every* reason the enrolment failed, not just the first. A single monolithic
   `validate()` with early returns cannot do this without contortions.

**Without it.** One `validate()` method with three nested `if` blocks. Each new rule deepens
the nesting, every rule change risks the others, and the failure message can only report one
problem at a time.

**Nuance worth stating in the report.** `CapacityRule` is *skipped* when the request carries
`isAdminOverride`. Because the rule set is a list, the administrator override in §3.3
(*"force-add a student into a full class"*) is implemented by composing a different rule
list — not by adding a special case inside the rule.

---

## ② Command «Behavioural»

**Where.** `EnrollmentCommand` is the Command interface with `execute()` and `undo()`;
`AddCourseCommand` and `DropCourseCommand` are ConcreteCommands; `TransactionManager` is the
Invoker holding a stack of executed commands.

**Report sentence.**
> *We are using the **Command** pattern to encapsulate each enrolment operation as an object
> with `execute()` and `undo()`, so that the invoker can roll back every completed step in
> reverse order if any step fails — satisfying the requirement that an enrolment either wholly
> succeeds or wholly fails.*

**Why.** This is the pattern chosen to satisfy an explicit, hard requirement:

> *"All enrolment operations (adding/dropping a course) must be treated as transactions. This
> means either the entire operation succeeds (e.g. the student is enrolled, the class capacity
> is updated, and the schedule is modified) or the entire operation fails, leaving no partial
> state changes."*

`AddCourseCommand.execute()` performs exactly the three state changes the requirement
enumerates, in order, recording each. `undo()` reverses them. `TransactionManager.runAtomic()`
executes commands onto a stack and, on any exception, pops the stack calling `undo()`.

**Why not just a database transaction?** We use both, and they operate at different levels.
The DB transaction protects persistence; the Command stack protects **in-memory domain
state** — a `CourseSection` whose `enrolledCount` was already incremented, a `StudentSchedule`
already mutated. In the proof-of-concept there is no database at all, so the Command rollback
*is* the transaction, which is precisely what makes it demonstrable in a screencast.

**Bonus capability.** The same structure gives the administrator module an audit log for free:
`describe()` on each executed command yields a replayable history of who changed what.

**Without it.** Rollback logic hand-written inline in a `try/except` block, duplicated between
add and drop, and silently incomplete the first time someone adds a fourth state change.

---

## ③ State «Behavioural»

**Where.** `GradeSubmission` is the Context; `GradeState` is the State interface;
`DraftState`, `PendingApprovalState`, `PartiallyRejectedState` and `SubmittedState` are
ConcreteStates. The same pattern is applied a second time to `CourseChangeRequest`.

**Report sentence.**
> *We are using the **State** pattern to model the grade approval lifecycle, so that each
> state object decides for itself which operations are legal — giving us the required
> "Pending" state before the final "Submitted" state, and letting a professor correct a
> rejected grade without losing the ones already accepted.*

**Why.** Two separate requirements land on the same object:

> *"The system must have a process for grade approval (e.g. a "Pending" state before a final
> "Submitted" state)."*

> *"If an error occurs during the process (e.g. an invalid grade is submitted), the system must
> handle it gracefully and allow the professor to correct it **without losing other submitted
> grades**."*

Both are lifecycle concerns, and behaviour differs completely by state: `addEntry()` is legal
in Draft and illegal in PendingApproval; `correctEntry()` is legal only in PartiallyRejected;
`SubmittedState` is terminal. Encoding this as classes means the legality rules live next to
the state they describe, and the interface's default implementation raises
`IllegalTransition` so an unhandled operation **fails loudly rather than corrupting a batch**.

`PartiallyRejectedState` is the direct answer to the error-isolation requirement: its entry
action retains all accepted entries and returns only the rejected ones.

**Without it.** A `status` enum plus an `if/elif` ladder in every mutating method of
`GradeSubmission`. Each new state multiplies branches across multiple methods, and nothing
structurally prevents a caller from editing an already-submitted batch.

**Design-level DRY.** Applying the same pattern to `CourseChangeRequest` — which has the same
Draft → Pending → terminal shape — reuses one design idea for two workflows.

---

## ④ Observer «Behavioural»

**Where.** `NotificationPublisher` is the Subject; `EventObserver` is the Observer interface;
`WaitlistObserver`, `AdvisorObserver` and `AdminAlertObserver` are ConcreteObservers.

**Report sentence.**
> *We are using the **Observer** pattern to notify waitlisted students, academic advisors and
> system administrators whenever an enrolment event occurs, so that the notification process
> is automated and completely decoupled from the core enrolment logic.*

**Why.** The requirement does not merely ask for notifications — it names the design property:

> *"A student drops a course. The notification system must automatically alert any waitlisted
> students that a spot has opened up. This process should be automated and **decoupled** from
> the core enrolment logic."*

The Enrolment Service publishes one event and returns. It holds no reference to any subscriber
and never learns whether delivery succeeded. All three notification requirements are then
independent observer classes:

| Requirement | Observer | Trigger |
|---|---|---|
| *"Students should be notified when a course they are waitlisted for becomes available"* | `WaitlistObserver` | `SeatReleased` |
| *"Advisors should be notified when one of their advisees drops a critical course"* | `AdvisorObserver` | `StudentDropped` + degree-critical guard |
| *"Administrators should be notified of any system-wide errors"* | `AdminAlertObserver` | `SystemError` |

**The architectural payoff.** This is also how the future financial aid system integrates
(Part A2.3): it subscribes to `StudentEnrolled` and receives what it needs with **zero lines
changed** in the Enrolment Service. Observer at class level and event-driven messaging at
architecture level are the same idea at two scales — a point worth making explicitly, because
it ties Part A and Part B together.

**Fault isolation.** `publish()` catches and logs exceptions per observer. A failing email
server cannot fail an enrolment that has already committed.

**Without it.** `EnrollmentFacade` calling `emailService.send(...)` three times inline. Adding
a recipient means editing enrolment code; a mail-server timeout fails the enrolment; and the
word "decoupled" in the requirement is simply not satisfied.

---

## ⑤ Factory Method «Creational»

**Where.** `ReportFactory.createReport(type)` is the factory method; `Report` is the Product
interface; `EnrolmentStatisticsReport`, `FacultyWorkloadReport`, `CoursePopularityReport` and
`CapacityThresholdReport` are ConcreteProducts.

**Report sentence.**
> *We are using the **Factory Method** pattern to create report objects, so that the
> administrator module can request a report by kind and receive a `Report` without knowing
> which concrete class implements it — letting new report types be added without touching any
> calling code.*

**Why.** The requirement is an open-ended list:

> *"The system must generate various reports: Enrolment statistics by department and semester.
> Faculty workload reports. Course popularity trends."*

Plus the §3.3 use case (*Business school courses over 90% capacity*) — a fourth. "Various"
signals a set that will grow. Centralising construction means the administrator module depends
only on the `Report` abstraction, and `availableTypes()` lets the UI populate a report menu
dynamically instead of hard-coding one.

**Without it.** A `switch`/`if` chain on a report-type string at every call site, duplicated
wherever reports are requested, each needing an edit for every new report.

---

## ⑥ Facade «Structural»

**Where.** `EnrollmentFacade` in the Enrolment Service business logic layer, sitting between
the Service API layer and the validator, commands, transaction manager, repositories and
publisher.

**Report sentence.**
> *We are using the **Facade** pattern to expose a single simple entry point over the
> validation, transaction and notification subsystems, so that the Service API layer contains
> no business rules and both the web SPA and the future mobile app consume exactly the same
> back-end operation.*

**Why.** Enrolling a student touches at least six collaborators. Exposing them to the API
layer would push orchestration logic into the presentation tier — the exact coupling the
3-Tier layering exists to prevent, and it would break the requirement that *"the same
back-end services must be usable by both the web application and a future mobile
application."* With the facade, `enrol()` is one call with one result, and the sequence diagram
shows the client sending exactly one message and receiving one reply.

The facade is also our **Dependency Inversion** showcase: every collaborator is injected
through the constructor as an interface, so the class depends on abstractions only.

**Without it.** Each API controller orchestrating validation, command construction,
transaction control and event publication — duplicated between web and mobile controllers,
and drifting apart over time.

---

## ⑦ Builder «Creational»

**Where.** In the Course Catalogue Service business logic layer.
`CourseSearchQuery` is the Product (immutable); `SearchQueryBuilder` is the Builder interface;
`CourseSearchQueryBuilder` is the ConcreteBuilder; `CatalogQueryDirector` is the Director,
holding recipes for the standard queries the system issues repeatedly.

**Report sentence.**
> *We are using the **Builder** pattern to assemble course-search queries step by step, so that
> a student can combine any subset of the four search criteria — department, course number,
> keyword and instructor — without the catalogue service exposing a constructor full of
> optional parameters, and so that a query object cannot exist in an invalid state.*

**Why.** The requirement is explicitly combinatorial:

> *"Students can search for courses by department, course number, keyword, and instructor."*

Four independent optional filters is 16 possible combinations, and the administrator reports add
more (semester, minimum occupancy, school). The two alternatives are both poor:

- **Telescoping constructors** — `CourseSearchQuery(dept)`, `(dept, num)`, `(dept, num, kw)`… an
  overload per combination.
- **One wide constructor with nullable parameters** — call sites degrade into
  `search(None, None, "algorithms", None, None, True, None)`, where a transposed argument is a
  silent bug rather than a compile error.

Builder gives four concrete benefits here:

1. **Readable, self-documenting call sites.** Each step names the criterion it sets.
2. **An immutable Product.** `CourseSearchQuery` has no setters, so once built it can be safely
   logged, cached, and passed across the service boundary to the Reporting Service without any
   risk of downstream mutation.
3. **Validation at the moment of construction.** `build()` enforces the invariants — at least
   one criterion present (an empty query would return the entire catalogue), occupancy threshold
   within 0.0–1.0, semester not in the past. **An invalid query object can never exist**, which
   is Fail Fast applied to a value object.
4. **The Director removes duplication.** `CatalogQueryDirector` holds the reusable recipes:

```python
class CatalogQueryDirector:
    """Director — knows the recipes; delegates the steps to the builder."""

    def open_sections_for(self, department: str, semester: Semester) -> CourseSearchQuery:
        return (self._builder.reset()
                    .department(department)
                    .semester(semester)
                    .with_available_seats_only()
                    .build())

    def over_capacity_in_school(self, school: str, threshold: float) -> CourseSearchQuery:
        # the §3.3 use case: Business school courses over 90% capacity
        return (self._builder.reset()
                    .school(school)
                    .min_occupancy(threshold)
                    .build())
```

That second recipe is the §3.3 administrator use case verbatim — *"a report on all courses in
the Business school that are currently at over 90% capacity."* It reuses the same builder as
student catalogue search, so the query-construction logic exists once (DRY) even though the two
features live in different modules.

**Client-side example** — the §3.1 use case, *"browse all computer science courses for the
upcoming semester that a specific professor teaches"*:

```python
query = (CourseSearchQuery.builder()
             .department("Computer Science")
             .instructor("Prof. Silva")
             .semester(Semester.FALL_2026)
             .build())
results = catalog.search(query)
```

**Without it.** A seven-parameter `search()` method where most arguments are `None` at every
call site, no single place to validate the combination, and a mutable query object that any
downstream consumer can alter after the fact.

---

## Patterns considered and deliberately rejected

The brief asks us to *justify* design choices. A justified rejection is a design choice, so this
section belongs in the report body rather than an appendix — it is the clearest available
evidence that patterns were selected by analysis rather than collected.

### Singleton «Creational» — rejected

**Where it would have gone.** `NotificationService`, owning the single `NotificationPublisher`
and its observer registry, reached through `NotificationService.getInstance()`.

**The real problem it was meant to solve.** Observers are attached once at start-up. If a second
registry ever came into existence, events dispatched through it would find **no subscribers** and
be discarded with no error — no exception, no log, no waitlisted student ever told that a seat had
opened. Silent failure is the worst failure mode, so the concern was legitimate.

**Why we rejected it.** Singleton conflicts with three of the five SOLID principles, and the
assignment marks us on SOLID adherence in Part B5:

| Principle | The conflict |
|---|---|
| **SRP** | The class acquires a second responsibility — managing its own lifecycle — on top of its actual job of dispatching notifications. Two reasons to change. |
| **DIP** | Every `getInstance()` call site binds to a **concrete class**, and the dependency is invisible in the constructor signature. High-level policy would depend on a low-level detail — the exact inversion the principle forbids, and the opposite of what we claim in `02-design-principles.md`. |
| **OCP** | Substituting a test double or an alternative dispatcher requires modifying the accessor rather than extending through an abstraction. |

It also imposes global mutable state, and tests leak into one another unless a `reset()` hook is
added — a hook whose only purpose is to undo the pattern.

**The decisive argument, specific to our design.** We had already committed to constructor
injection everywhere and to confining `getInstance()` to application start-up. But if the only
call is in the composition root, then the guarantee of a single instance is coming from **the
wiring, not the pattern**. We would have been paying Singleton's full SOLID cost for a global
access point we had promised never to use — a pattern present for its own sake.

**What we do instead.** The **composition root** owns instance lifetime.
`composition_root.py` — called once from `main.py` — constructs exactly one
`NotificationPublisher` and injects that same reference into every collaborator:

```python
# composition_root.py — the ONLY place objects are wired together
publisher = NotificationPublisher()                  # exactly one, by construction
email = EmailChannel()

publisher.attach(EventType.SEAT_RELEASED,   WaitlistObserver(email, repos.waitlists, repos.users))
publisher.attach(EventType.STUDENT_DROPPED, AdvisorObserver(email, repos.users,
                                                            repos.programs, repos.courses))
publisher.attach(EventType.SYSTEM_ERROR,    AdminAlertObserver(email, repos.users))

facade = EnrollmentFacade(validator=validator, tx_manager=tx, publisher=publisher,
                          receiver=receiver, enrol_repo=repos.enrolments,
                          waitlist_repo=repos.waitlists, semester=SEMESTER)
```

This is the *single-instance lifestyle* rather than the *Singleton pattern*: identical
uniqueness guarantee, no global access point, no hidden dependency, and every dependency
visible in the constructor signature. Tests construct their own publisher with a fake channel
and need no reset hook.

**A Python-specific note.** A module is already effectively a singleton in Python — importing
`notification_service` twice yields the same module object. A hand-written `getInstance()` is
therefore un-idiomatic in the implementation language we chose, which reinforces the decision.

**Where Singleton would still be defensible.** We are not claiming the pattern is always wrong.
For genuinely cross-cutting infrastructure — a logger, immutable configuration, a database
connection pool — threading one instance through every constructor is impractical, and the
trade-off inverts. Our notification registry is not cross-cutting: it has exactly one consumer
tree, reachable by injection.

### Other patterns evaluated

| Pattern | Considered for | Why rejected |
|---|---|---|
| **Abstract Factory** | Creating families of related report objects | We have one product family, not several varying by platform or region. Factory Method is the right granularity; Abstract Factory here would be speculative generality (YAGNI). |
| **Decorator** | Chaining the validation rules, each wrapping the next | A decorator chain naturally short-circuits at the first failure, but the requirement benefits from reporting **every** failed rule at once. Strategy plus a flat list gives the same extensibility, is order-independent, and aggregates errors. |
| **Proxy** | Lazy-loading large class rosters | No requirement asks for it and we have no measured performance problem. Adding it would be premature optimisation — rejected on KISS grounds. |
| **Template Method** | Report generation (fetch → filter → aggregate → format) | The closest call of the four. Rejected because the four reports differ in their aggregation *shape*, not merely in one substitutable step, so a fixed skeleton would fit three of them and fight the fourth. Worth revisiting if a fifth report shares the skeleton. |
| **Chain of Responsibility** | Escalating a course-change request through approval levels | The requirement specifies a single administrator approval, not a hierarchy. Would model a workflow the university does not have. |

---

## Where each pattern appears in the diagrams

| Pattern | Class structure | In action |
|---|---|---|
| ① Strategy | `03-class-diagram-patterns` zone ① | Activity p1 fork/join · Sequence p1 msgs 2.1–2.3 |
| ② Command | zone ② | Activity p1 Transaction lane · Sequence p1 msgs 4–4.2 |
| ③ State | zone ③ | Activity p2 · **State diagrams p1 & p3** |
| ④ Observer | zone ④ | **Sequence p2** (clearest evidence) · Architecture broker |
| ⑤ Factory Method | zone ⑤ | Administrator module (independent of enrolment flow) |
| ⑥ Facade | zone ⑥ | Sequence p1 msg 1 / msg 6 · Activity p1 Facade lane |
| ⑦ Builder | zone ⑦ | Course Catalogue Service · admin `>90% capacity` report |

Diagram `03-class-diagram-patterns` also carries a **rejected-patterns panel** recording the
Singleton decision, so the reasoning is visible on the diagram itself and not only in this
document. The composition root that replaces it is shown on the same diagram.

---

## Presentation advice for the screencast and report

- **Lead with Observer using sequence diagram page 2.** The red boundary line makes
  "decoupled" visible in one glance — it is the most persuasive single image in the set.
- **Demonstrate Command by causing a failure.** In the screencast, force step 3 of
  `execute()` to raise, then show `enrolledCount` unchanged afterwards. A working rollback is
  far more convincing than narrating one.
- **Demonstrate State by attempting an illegal transition.** Call `addEntry()` on a
  submission in `PendingApproval` and show `IllegalTransition` raised.
- **Quote the requirement before naming the pattern.** Requirement → problem → pattern reads
  as engineering. Pattern → requirement reads as retrofitting.
