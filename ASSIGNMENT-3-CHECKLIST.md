# Assignment 3 — NexusEnroll — TODO Checklist

**Course:** Software Architecture (SCS 2303)
**Project:** University Course Enrolment System — A Modernisation Project ("NexusEnroll")
**Released:** 20 July 2026 · **Deadline:** 20 August 2026
**Team size:** 5–6 students

> ⚠️ Prioritise the **Design Pattern Application (40%)** and the **runnable code (20%)** — together they are 60% of the grade.

---

## ✅ Design phase — COMPLETE (16 Aug 2026)

Architecture chosen and justified, and all required UML designed. See `DESIGN/`:

| Deliverable | File | Brief section |
|---|---|---|
| Architecture decision + justification + rejected alternatives | `DESIGN/00-architecture-decision.md` | Part A1–A3 |
| Design patterns: where, why, and what breaks without each | `DESIGN/01-design-patterns.md` | Part B2–B3 |
| Design principles with a concrete example each | `DESIGN/02-design-principles.md` | Part B5 |
| All UML — 6 files, 10 pages, 296 shapes | `DESIGN/diagrams/` | Part B4 |
| Index, import instructions, team work split | `DESIGN/README.md` | — |

**Architecture: Microservices (system level) + 3-Tier (inside each service).**
Chosen over pure 3-Tier and SOA; both rejections are argued in `00-architecture-decision.md` §A3.

**Patterns applied (7, vs. a minimum of 3):** Strategy · Command · State · Observer · Factory Method · Facade · Builder — all three GoF families covered.

**Singleton was considered and deliberately rejected** (conflicts with SRP, DIP and OCP; the composition root in `composition_root.py` gives the same single-instance guarantee). The reasoning is written up as part of the justification, not omitted — §6 of `01-design-patterns.md` plus a rejected-patterns panel on diagram 03.

> 📤 **Export note for the report:** diagrams 01 and 03 are A2-sized canvases. Export those as **PDF → Fit to page**, not PNG, or the text will be illegible on A4. The others export fine as PNG at 200% zoom.

---

## ✅ Implementation phase — COMPLETE (16 Aug 2026)

Part B6 is done and runnable: **`src/nexusenroll/`**, Python 3.10+, no third-party dependencies.

```
cd src && python -m nexusenroll.main
```

| Package | Contents |
|---|---|
| `domain/` | Business entities straight off diagram 02 — the Business Logic layer |
| `patterns/` | One module per pattern, each opening with a banner naming its GoF roles |
| `repositories/` | `I*Repository` interfaces (owned by the business layer) + in-memory implementations |
| `services/` | The student, faculty and administrator modules |
| `composition_root.py` | The single wiring point — this is what replaced Singleton |
| `main.py` | Four acts: the three modules' user stories, then Act 4's pattern proofs (Command, State and Observer, in six steps) |

**Running the demo caught a genuine bug**, which is worth mentioning in the report as
evidence the proof-of-concept is real: `TransactionManager.run_atomic()` pushed commands onto
the rollback stack only *after* `execute()` returned, so a command failing part-way through was
never rolled back — the exact partial state the requirement forbids. Commands are now pushed
before execution. Act 4.1 prints the before/after counts that prove it.

---

## ✅ Screencast script — WRITTEN (16 Aug 2026)

`DESIGN/03-screencast-script.md` — timed to **9:40** against the 10-minute limit, shot by shot.
Demo-led, because submission guideline 3 requires the video to focus on *"test cases to interact
with the business logic tier"*: one run of `main.py` is the spine, and code appears only to
explain a result already on screen. Every talking point cites an exact `file:line`, and all 63
references were verified against the source.

⏭️ **What is genuinely left:** report assembly (Part B7), recording, and the VLE upload.


---

## 📦 Submission Deliverables

- [ ] **Design document** — overall architecture + UML diagrams + OO design + design patterns — *prose and diagrams all exist in `DESIGN/`; still needs assembling into one document*
- [ ] **Source code** — C++, C#, Java, or Python (compressed file) — *code complete in `src/`; still needs zipping*
- [ ] **Screencast video** — max 10 minutes, focused on interacting with the business logic tier via UI or test cases — *script written; not yet recorded*
- [ ] **Upload all three to VLE** on or before 20 August 2026
- [ ] Confirm team composition is 5–6 students — ⚠️ *still unconfirmed; names and student IDs are needed for the title page*

---

## Part A: Architectural Design — 30%

### A1. Select architectural pattern(s)
- [x] Choose from: **Microservices** / **SOA** / **3-Tier** (one or a combination)
- [x] Decide whether to combine patterns (e.g. 3-Tier layering inside each microservice)

### A2. Justify the choice — 15%
- [x] Explain why it is the best fit for the university's needs
- [x] Address **scalability** (peak enrolment periods, high concurrent users)
- [x] Address **maintainability** (replacing the 20-year-old "LegacyEnroll" monolith)
- [x] Address **future integration** (e.g. a new financial aid system)

### A3. Draw and describe the architecture — 15%
- [x] Create a clear architecture diagram
- [x] Label all layers / tiers / services
- [x] Label communication pathways (REST APIs, message bus, etc.)
- [x] Write a brief function + responsibility description for each major component

---

## Part B: Detailed Design & Implementation — 70%

### B1. Core feature scope
- [x] Student module — `src/nexusenroll/services/student_service.py`
- [x] Faculty module — `src/nexusenroll/services/faculty_service.py`
- [x] Administrator module — `src/nexusenroll/services/admin_service.py`

### B2–B3. Apply design patterns — 40%
- [x] Use a **minimum of 3 distinct** object-oriented design patterns
- [x] Explicitly **identify** each pattern used
- [x] For each pattern, explain **where** and **why** it is used
- [x] Cover the pattern families:
  - [x] **Creational** — Factory Method ⑤ + Builder ⑦
  - [x] **Structural** — Facade ⑥
  - [x] **Behavioural** — Strategy ① · Command ② · State ③ · Observer ④
- [x] Document the patterns **considered and rejected**, with reasons *(not required by the brief — added because the 40% criterion rewards demonstrated judgment)*

**LOCKED — the seven patterns being implemented.** Full write-up: `DESIGN/01-design-patterns.md`.
Class structures: `DESIGN/diagrams/03-class-diagram-patterns.drawio`, zones ①–⑦.

| # | Pattern | Family | Where | Requirement it satisfies |
|---|---|---|---|---|
| ① | **Strategy** | Behavioural | `EnrollmentValidator` + `ValidationRule` × 3 | §3.1 the three validation rules |
| ② | **Command** | Behavioural | `Add`/`DropCourseCommand` + `TransactionManager` | §4 all-or-nothing transactions |
| ③ | **State** | Behavioural | `GradeSubmission`; reused for `CourseChangeRequest` | §3.2 Pending → Submitted approval |
| ④ | **Observer** | Behavioural | `NotificationPublisher` + 3 observers | §4 *"decoupled"* notification |
| ⑤ | **Factory Method** | Creational | `ReportFactory` + `Report` × 4 | §3.3 reporting & analytics |
| ⑥ | **Facade** | Structural | `EnrollmentFacade` | §4 one back-end for web + mobile |
| ⑦ | **Builder** | Creational | `CourseSearchQueryBuilder` + `CatalogQueryDirector` | §3.1 multi-criteria catalogue search |

**Rejected, with reasoning documented** (§6 of `01-design-patterns.md` + panel on diagram 03):

| Pattern | Why rejected |
|---|---|
| ~~Singleton~~ | Conflicts with SRP, DIP and OCP. The composition root in `composition_root.py` already gives the single-instance guarantee, so `getInstance()` would add a global access point for no benefit. Also un-idiomatic in Python, where a module is already a singleton. |
| ~~Abstract Factory~~ | One product family only — Factory Method is the right granularity (YAGNI) |
| ~~Decorator~~ | A chain short-circuits; the requirement benefits from reporting *every* failed rule |
| ~~Proxy~~ | No requirement drives it — premature optimisation (KISS) |
| ~~Template Method~~ | Closest call; the four reports differ in aggregation shape, not one substitutable step |
| ~~Chain of Responsibility~~ | The university has single-administrator approval, not an escalation hierarchy |

### B4. Core business logic design + UML
- [x] Restrict design focus to the **business logic layer** (exclude presentation & other tiers)
- [x] Identify the primary business-tier objects
- [x] Define the relationships between those objects
- [x] **Class Diagram** — structure and relationships of classes (highlight the patterns)
- [x] **Activity Diagram** — flow of key business processes
- [x] **Sequence Diagram** — object interactions in specific scenarios
  - [ ] *(Optional alternative: Collaboration Diagram, focusing on object roles)*
- [x] **State Diagram** — lifecycle of key objects

### B5. Software design principles
Provide **at least one concrete example** in the design for each:

- [x] Encapsulation
- [x] Programming to an Interface
- [x] Composition over Inheritance
- [x] **S** — Single Responsibility Principle
- [x] **O** — Open/Closed Principle
- [x] **L** — Liskov Substitution Principle
- [x] **I** — Interface Segregation Principle
- [x] **D** — Dependency Inversion Principle
- [x] DRY (Don't Repeat Yourself)
- [x] KISS (Keep It Simple, Stupid)
- [x] Justify overall design choices against these principles

### B6. Implement the solution — 20%
Write a small, **runnable** proof-of-concept application:

> ✅ **Done — `src/nexusenroll/`.** Run with `cd src && python -m nexusenroll.main`
> (Python 3.10+; no third-party dependencies). Output is four acts: the three
> modules' user stories, then the three pattern proofs.

- [x] Implement the **Student** module
- [x] Implement the **Faculty** module
- [x] Implement the **Administrator** module
- [x] Represent the core components defined in the architecture — `domain/` is the Business Logic layer, `repositories/` the Data Access layer, split by bounded context as on diagram 01
- [x] Show how the design patterns are integrated into all three modules' logic
- [x] Include a `main()` function or test classes simulating student / faculty / admin user stories
- [x] *(UI to interface the core business tier is **optional**)* — console output only, as permitted
- [x] Provide clear comments explaining the code and the role of each design pattern — every pattern module opens with a banner naming its GoF roles, the requirement it satisfies, and what breaks without it

### B7. Documentation — 10%
Submit a report that includes:

> 📝 The **content** for the first three items is already drafted in `DESIGN/`. What remains is
> assembly into the submission document: paste the prose, export the diagrams as images, add a
> title page, contents page and team member list.

- [ ] Architectural diagrams and justifications — *text ready in `00-architecture-decision.md`; export diagram 01*
- [ ] Class diagrams for the features, highlighting design patterns used — *export diagrams 02 + 03*
- [ ] Description of each design pattern's role and implementation — *text ready in `01-design-patterns.md`*
- [ ] Final, well-commented source code — *code done in `src/nexusenroll/`; still needs pasting into the report as a listing*
- [ ] Add title page, table of contents, team member names and student IDs
- [ ] Include the design-principles section — *text ready in `02-design-principles.md`*
- [ ] Include the rejected-alternatives sections (architecture + patterns) — *evidence of judgment, cheap marks*

---

## 🎯 Functional Requirements to Implement / Model

> ℹ️ **These boxes track implementation, not design.** Every item below is already *modelled* in
> `DESIGN/` — the domain classes exist on diagram 02, the patterns that serve them on diagram 03.
> Tick them as the Python code goes in. The pattern annotations show which pattern each group of
> requirements routes through, so you always know which class to open.

### 1. Student Module

**Course Catalogue Browse** — *Builder ⑦ builds the query; `CourseSearchQuery.matches()` filters*
- [x] Search courses by **department**
- [x] Search courses by **course number**
- [x] Search courses by **keyword**
- [x] Search courses by **instructor**
- [x] Display real-time: course name and description
- [x] Display real-time: instructor name
- [x] Display real-time: available seats vs. total capacity
- [x] Display real-time: schedule (days, times, location)
- [x] Display real-time: prerequisites
- [x] Use case: browse all CS courses for the upcoming semester taught by a specific professor — demo act 1.1

**Registration and Enrolment** — *Facade ⑥ orchestrates → Strategy ① validates → Command ② commits → Observer ④ notifies*
- [x] Add a course to the enrolment list
- [x] Drop a course from the enrolment list
- [x] Validation — **prerequisite check** (all prerequisites completed)
- [x] Validation — **capacity check** (course not full)
- [x] Validation — **time conflict check** (no overlap with enrolled courses)
- [x] On success: confirm enrolment, update schedule, update academic record
- [x] Use case: enrol → check prerequisites → check capacity → confirm & update — demo acts 1.3–1.5

**Personal Schedule Management** — *`StudentSchedule.asCalendarView()`; mutated only inside Command ②*
- [x] View current semester schedule
- [x] View past semester schedules — `past_schedules()`; the seed only populates Fall 2026, so the demo shows one
- [x] Dynamically build and display a calendar-like view of classes — demo act 1.6

**Academic Progress Tracking** — *`ProgressTracker` + `DegreeProgram.remainingFor()`*
- [x] List completed courses with grades received
- [x] Show courses still required for the degree program — demo act 1.7

### 2. Faculty Module

**Class Roster Viewing** — *read-only query across `Enrollment` + `Person`*
- [x] View real-time list of students enrolled in own courses — a lecturer sees only their own sections
- [x] Roster includes student names, IDs, and contact information — demo act 2.1

**Grade Submission** — *State ③ drives the lifecycle; `BatchGradeProcessor` isolates per-entry errors*
- [x] Enter and submit final grades per student
- [x] Grade approval process with a **"Pending"** state before **"Submitted"**
- [x] Batch grade submission processing — demo act 2.2
- [x] Update student academic records on submission — entry action of `SubmittedState`, demo act 3.1
- [x] Graceful error handling — an invalid grade must not lose other submitted grades
- [x] Allow the professor to correct the erroneous entry — `correctEntry()`, legal only in `PartiallyRejectedState`

**Course Information Management** — *State ③ again, on `CourseChangeRequest` (diagram 06 p3)*
- [x] Submit request to update course description
- [x] Submit request to add prerequisites
- [x] Submit request to change course capacity — demo act 2.4
- [x] All such requests require **administrator approval** — the live section is mutated only on entry to `ApprovedState`

### 3. Administrator Module

**Course & Program Management** — *`CourseCatalog` CRUD on `Course` / `DegreeProgram`*
- [x] Create courses
- [x] Edit courses
- [x] Delete courses — refuses to orphan existing sections
- [x] Define and manage degree programs (required courses and credits)

**Student & Faculty Management** — *`AccountManager`; force-add composes a rule list without `CapacityRule` (Strategy ①)*
- [x] Add student and faculty accounts
- [x] Edit student and faculty accounts
- [x] Deactivate student and faculty accounts — demo act 3.3
- [x] Manually override enrolment rules (e.g. force-add a student into a full class) — demo act 3.4, guarded on the administrator's own permission set

**Reporting & Analytics** — *Factory Method ⑤ creates the report; Builder ⑦ builds its criteria*
- [x] Report: enrolment statistics by department and semester
- [x] Report: faculty workload
- [x] Report: course popularity trends — demo act 3.5
- [x] Use case: all Business school courses currently over **90% capacity** — demo act 3.6
- [x] Present report data in a clean, organised format (table / spreadsheet) — `ReportData.asTable()` and `.asCsv()`

### 4. System-Wide Requirements

**Notification System** — *Observer ④ — see sequence diagram 05 page 2*
- [x] Notification mechanism (e.g. email) — `EmailChannel` behind a `NotificationChannel` interface
- [x] Notify students when a waitlisted course becomes available — `WaitlistObserver` ← `SeatReleased`
- [x] Notify advisors when an advisee drops a critical course — `AdvisorObserver` ← `StudentDropped`, guarded on degree-criticality
- [x] Notify administrators of system-wide errors — `AdminAlertObserver` ← `SystemError`, demo act 4.6
- [x] Notification process is **automated and decoupled** from core enrolment logic — demo act 4.3

**Transaction Management** — *Command ② + `TransactionManager.runAtomic()`*
- [x] Treat all add/drop enrolment operations as **transactions**
- [x] All-or-nothing: enrolment + capacity update + schedule modification succeed together
- [x] No partial state changes on failure — demo act 4.1 forces a step-3 failure and prints all three unchanged

**Robustness** — *`ValidationResult` aggregation · `IllegalTransition` fail-fast · per-observer exception isolation*
- [x] Error-handling strategies — aggregate validation errors, fail-fast transitions, per-observer isolation
- [x] Input validation — `Builder.build()` invariants, per-entry grade validation, capacity guards inside `CourseSection`
- [x] Redundancy / recovery mechanisms — command rollback; a failing observer cannot fail a committed enrolment (demo act 4.4)
- [x] Graceful handling of unexpected inputs — invalid grades and unenrolled students are rejected per entry, never per batch

**User Interface (design assumptions to document)**
- [x] Front-end is a single-page application (SPA) communicating via APIs
- [x] Same back-end services usable by both the web app and a future mobile app

---

---

## 🗓️ Remaining plan — 4 days to deadline (16 → 20 Aug 2026)

Ordered by grade impact per hour. Design and code are both done, so nothing below is blocked.

### Day 1 — skeleton + the two patterns worth the most ✅ DONE
- [x] Create the package layout (`domain/`, `patterns/`, `repositories/`, `services/`, `composition_root.py`, `main.py`)
- [x] Domain entities as dataclasses, straight off diagram 02
- [x] In-memory repositories behind the `I*Repository` interfaces
- [x] **Strategy ①** — `ValidationRule` ABC + the three rules (plus `CreditLimitRule` as a live Open/Closed demo)
- [x] **Command ②** — `EnrollmentCommand` ABC, add/drop, `TransactionManager` with rollback
- [x] Seed data: 8 courses, 5 students, 3 faculty, one full section, one with prerequisites

### Day 2 — the remaining patterns + all three modules ✅ DONE
- [x] **Observer ④** — publisher + the three observers (plus `AuditObserver` as the financial-aid stand-in)
- [x] **Facade ⑥** — `EnrollmentFacade`, all collaborators constructor-injected
- [x] **State ③** — grade lifecycle with `IllegalTransition` on illegal calls; applied again to `CourseChangeRequest`
- [x] **Factory Method ⑤** — the four reports
- [x] **Builder ⑦** — `CourseSearchQueryBuilder` + `CatalogQueryDirector`
- [x] Composition root — given its own file, `composition_root.py`, with the Singleton reasoning at the top
- [x] `main.py` user stories for student / faculty / administrator

### Day 3 — report assembly
- [ ] Export every diagram (01 and 03 as **PDF → Fit to page**)
- [ ] Assemble the report from `DESIGN/00`, `01`, `02` + title page + contents + team list
- [ ] Add the well-commented source listing
- [ ] Cross-check every rubric line against this checklist

### Day 4 — screencast + submit (leave buffer)
- [x] Write the screencast script — `DESIGN/03-screencast-script.md`, timed to 9:40 with every code reference resolved to a real `file:line`
- [ ] Rehearse once with a stopwatch, then record ≤ 10 minutes
- [ ] Compress source, upload document + code + video to VLE
- [ ] Confirm the upload actually appears in VLE — do not assume

**Screencast** — the full timed script is `DESIGN/03-screencast-script.md`. Summary of the running
order, leading with the demos that *prove* a pattern rather than describe it:
All three are already scripted as **Act 4** of `main.py`, so the screencast can simply run the demo:

1. **Command ② rollback** — force step 3 of `execute()` to raise, then show `enrolledCount` unchanged *(act 4.1)*
2. **State ③ guard** — call `addEntry()` on a `PendingApproval` submission, show `IllegalTransition` *(act 4.2)*
3. **Observer ④ decoupling** — drop a course, watch the waitlist notification fire with no enrolment code involved *(act 4.3)*; act 4.4 additionally shows a broken observer failing in isolation without failing the drop

Then walk the three modules' user stories, and close on the administrator `>90% capacity` report.

## 📊 Assessment Criteria Weighting

| Criterion | Weight | Status |
|---|---|---|
| Architectural Choice & Justification | 15% | ✅ designed |
| Architectural Diagram & Description | 15% | ✅ designed |
| **Design Pattern Application** | **40%** | ✅ designed · ✅ implemented |
| Implementation & Code Quality | 20% | ✅ runnable — `cd src && python -m nexusenroll.main` |
| Documentation | 10% | ⏭️ assemble from DESIGN/ |

---

> *"You don't understand anything until you learn it more than one way"* — Marvin Minsky
