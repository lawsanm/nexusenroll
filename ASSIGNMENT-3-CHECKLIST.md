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

**Singleton was considered and deliberately rejected** (conflicts with SRP, DIP and OCP; the composition root in `main.py` gives the same single-instance guarantee). The reasoning is written up as part of the justification, not omitted — §6 of `01-design-patterns.md` plus a rejected-patterns panel on diagram 03.

> 📤 **Export note for the report:** diagrams 01 and 03 are A2-sized canvases. Export those as **PDF → Fit to page**, not PNG, or the text will be illegible on A4. The others export fine as PNG at 200% zoom.

⏭️ **Next up:** Part B6 — the Python proof-of-concept. Then report assembly and the screencast.


---

## 📦 Submission Deliverables

- [ ] **Design document** — overall architecture + UML diagrams + OO design + design patterns
- [ ] **Source code** — C++, C#, Java, or Python (compressed file)
- [ ] **Screencast video** — max 10 minutes, focused on interacting with the business logic tier via UI or test cases
- [ ] **Upload all three to VLE** on or before 20 August 2026
- [ ] Confirm team composition is 5–6 students

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
- [ ] Student module
- [ ] Faculty module
- [ ] Administrator module

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
| ~~Singleton~~ | Conflicts with SRP, DIP and OCP. The composition root in `main.py` already gives the single-instance guarantee, so `getInstance()` would add a global access point for no benefit. Also un-idiomatic in Python, where a module is already a singleton. |
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

- [ ] Implement the **Student** module
- [ ] Implement the **Faculty** module
- [ ] Implement the **Administrator** module
- [ ] Represent the core components defined in the architecture
- [ ] Show how the design patterns are integrated into all three modules' logic
- [ ] Include a `main()` function or test classes simulating student / faculty / admin user stories
- [ ] *(UI to interface the core business tier is **optional**)*
- [ ] Provide clear comments explaining the code and the role of each design pattern

### B7. Documentation — 10%
Submit a report that includes:

> 📝 The **content** for the first three items is already drafted in `DESIGN/`. What remains is
> assembly into the submission document: paste the prose, export the diagrams as images, add a
> title page, contents page and team member list.

- [ ] Architectural diagrams and justifications — *text ready in `00-architecture-decision.md`; export diagram 01*
- [ ] Class diagrams for the features, highlighting design patterns used — *export diagrams 02 + 03*
- [ ] Description of each design pattern's role and implementation — *text ready in `01-design-patterns.md`*
- [ ] Final, well-commented source code — *blocked on B6*
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
- [ ] Search courses by **department**
- [ ] Search courses by **course number**
- [ ] Search courses by **keyword**
- [ ] Search courses by **instructor**
- [ ] Display real-time: course name and description
- [ ] Display real-time: instructor name
- [ ] Display real-time: available seats vs. total capacity
- [ ] Display real-time: schedule (days, times, location)
- [ ] Display real-time: prerequisites
- [ ] Use case: browse all CS courses for the upcoming semester taught by a specific professor

**Registration and Enrolment** — *Facade ⑥ orchestrates → Strategy ① validates → Command ② commits → Observer ④ notifies*
- [ ] Add a course to the enrolment list
- [ ] Drop a course from the enrolment list
- [ ] Validation — **prerequisite check** (all prerequisites completed)
- [ ] Validation — **capacity check** (course not full)
- [ ] Validation — **time conflict check** (no overlap with enrolled courses)
- [ ] On success: confirm enrolment, update schedule, update academic record
- [ ] Use case: enrol → check prerequisites → check capacity → confirm & update

**Personal Schedule Management** — *`StudentSchedule.asCalendarView()`; mutated only inside Command ②*
- [ ] View current semester schedule
- [ ] View past semester schedules
- [ ] Dynamically build and display a calendar-like view of classes

**Academic Progress Tracking** — *`ProgressTracker` + `DegreeProgram.remainingFor()`*
- [ ] List completed courses with grades received
- [ ] Show courses still required for the degree program

### 2. Faculty Module

**Class Roster Viewing** — *read-only query across `Enrollment` + `Person`*
- [ ] View real-time list of students enrolled in own courses
- [ ] Roster includes student names, IDs, and contact information

**Grade Submission** — *State ③ drives the lifecycle; `BatchGradeProcessor` isolates per-entry errors*
- [ ] Enter and submit final grades per student
- [ ] Grade approval process with a **"Pending"** state before **"Submitted"**
- [ ] Batch grade submission processing
- [ ] Update student academic records on submission
- [ ] Graceful error handling — an invalid grade must not lose other submitted grades
- [ ] Allow the professor to correct the erroneous entry

**Course Information Management** — *State ③ again, on `CourseChangeRequest` (diagram 06 p3)*
- [ ] Submit request to update course description
- [ ] Submit request to add prerequisites
- [ ] Submit request to change course capacity
- [ ] All such requests require **administrator approval**

### 3. Administrator Module

**Course & Program Management** — *`CourseCatalog` CRUD on `Course` / `DegreeProgram`*
- [ ] Create courses
- [ ] Edit courses
- [ ] Delete courses
- [ ] Define and manage degree programs (required courses and credits)

**Student & Faculty Management** — *`AccountManager`; force-add composes a rule list without `CapacityRule` (Strategy ①)*
- [ ] Add student and faculty accounts
- [ ] Edit student and faculty accounts
- [ ] Deactivate student and faculty accounts
- [ ] Manually override enrolment rules (e.g. force-add a student into a full class)

**Reporting & Analytics** — *Factory Method ⑤ creates the report; Builder ⑦ builds its criteria*
- [ ] Report: enrolment statistics by department and semester
- [ ] Report: faculty workload
- [ ] Report: course popularity trends
- [ ] Use case: all Business school courses currently over **90% capacity**
- [ ] Present report data in a clean, organised format (table / spreadsheet)

### 4. System-Wide Requirements

**Notification System** — *Observer ④ — see sequence diagram 05 page 2*
- [ ] Notification mechanism (e.g. email)
- [ ] Notify students when a waitlisted course becomes available
- [ ] Notify advisors when an advisee drops a critical course
- [ ] Notify administrators of system-wide errors
- [ ] Notification process is **automated and decoupled** from core enrolment logic

**Transaction Management** — *Command ② + `TransactionManager.runAtomic()`*
- [ ] Treat all add/drop enrolment operations as **transactions**
- [ ] All-or-nothing: enrolment + capacity update + schedule modification succeed together
- [ ] No partial state changes on failure

**Robustness** — *`ValidationResult` aggregation · `IllegalTransition` fail-fast · per-observer exception isolation*
- [ ] Error-handling strategies
- [ ] Input validation
- [ ] Redundancy / recovery mechanisms
- [ ] Graceful handling of unexpected inputs

**User Interface (design assumptions to document)**
- [x] Front-end is a single-page application (SPA) communicating via APIs
- [x] Same back-end services usable by both the web app and a future mobile app

---

---

## 🗓️ Remaining plan — 4 days to deadline (16 → 20 Aug 2026)

Ordered by grade impact per hour. The design is done, so nothing below is blocked on decisions.

### Day 1 — skeleton + the two patterns worth the most
- [ ] Create the package layout (`domain/`, `patterns/`, `repositories/`, `services/`, `main.py`)
- [ ] Domain entities as dataclasses, straight off diagram 02
- [ ] In-memory repositories behind the `I*Repository` interfaces
- [ ] **Strategy ①** — `ValidationRule` ABC + the three rules
- [ ] **Command ②** — `EnrollmentCommand` ABC, add/drop, `TransactionManager` with rollback
- [ ] Seed data: ~8 courses, ~5 students, ~3 faculty, one full section, one with prerequisites

### Day 2 — the remaining patterns + all three modules
- [ ] **Observer ④** — publisher + the three observers
- [ ] **Facade ⑥** — `EnrollmentFacade`, all collaborators constructor-injected
- [ ] **State ③** — grade lifecycle with `IllegalTransition` on illegal calls
- [ ] **Factory Method ⑤** — the four reports
- [ ] **Builder ⑦** — `CourseSearchQueryBuilder` + `CatalogQueryDirector`
- [ ] Composition root in `main.py` (this is what replaced Singleton — make it visible)
- [ ] `main.py` user stories for student / faculty / administrator

### Day 3 — report assembly
- [ ] Export every diagram (01 and 03 as **PDF → Fit to page**)
- [ ] Assemble the report from `DESIGN/00`, `01`, `02` + title page + contents + team list
- [ ] Add the well-commented source listing
- [ ] Cross-check every rubric line against this checklist

### Day 4 — screencast + submit (leave buffer)
- [ ] Rehearse once, then record ≤ 10 minutes
- [ ] Compress source, upload document + code + video to VLE
- [ ] Confirm the upload actually appears in VLE — do not assume

**Screencast running order** — lead with the three demos that *prove* a pattern rather than describe it:
1. **Command ② rollback** — force step 3 of `execute()` to raise, then show `enrolledCount` unchanged
2. **State ③ guard** — call `addEntry()` on a `PendingApproval` submission, show `IllegalTransition`
3. **Observer ④ decoupling** — drop a course, watch the waitlist notification fire with no enrolment code involved

Then walk the three modules' user stories, and close on the administrator `>90% capacity` report.

## 📊 Assessment Criteria Weighting

| Criterion | Weight | Status |
|---|---|---|
| Architectural Choice & Justification | 15% | ✅ designed |
| Architectural Diagram & Description | 15% | ✅ designed |
| **Design Pattern Application** | **40%** | ✅ designed · ⏭️ implement |
| Implementation & Code Quality | 20% | ⏭️ not started |
| Documentation | 10% | ⏭️ assemble from DESIGN/ |

---

> *"You don't understand anything until you learn it more than one way"* — Marvin Minsky
