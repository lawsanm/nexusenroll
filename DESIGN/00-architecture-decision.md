# Part A — Architectural Design: Decision & Justification

**System:** NexusEnroll — Nexus University Course Enrolment System
**Document purpose:** Report-ready text for Part A1 (selection), A2 (justification, 15%) and A3 (description, 15%).

---

## A1. Selected Architectural Pattern

> **Selected: A hybrid of Microservices Architecture (system level) and 3-Tier Architecture (service level).**
>
> NexusEnroll is decomposed into six independently deployable microservices aligned to
> business capabilities. Each individual microservice is *internally* structured as three
> layers — Service API layer, Business Logic layer, and Data Access layer. Synchronous
> client traffic enters through an API Gateway; cross-service events travel asynchronously
> over a Message Broker.

The assignment brief permits "one or a combination of patterns to complement the overall
solution architecture." This combination is deliberate, not a hedge — the two patterns
answer two different questions:

| Question | Answered by |
|---|---|
| How do we scale enrolment under peak load, and add a financial aid system later without touching enrolment code? | **Microservices** (system decomposition) |
| Where exactly does the business logic live, separated from presentation and persistence? | **3-Tier** (internal service structure) |

The second point matters directly for grading: Part B4 instructs us to *"focus your design
efforts on the core business logic layer"* and *"exclude presentation and other functional
tiers."* The internal 3-tier layering gives us a named, bounded Business Logic layer that the
detailed design, UML diagrams, and proof-of-concept code all target.

---

## A2. Justification

### 2.1 Scalability — the peak enrolment problem

The requirement states the system *"must be able to handle a high volume of simultaneous
users, especially during peak enrolment periods."* This load is **not uniform**. During
registration week, enrolment and catalogue browsing traffic spikes by orders of magnitude
while grade submission and reporting traffic stays near zero. At end of semester the
opposite is true.

Microservices allow **asymmetric horizontal scaling**: we run many instances of the
Enrolment Service and Course Catalogue Service during registration week, and scale the
Academic Records Service up only at grading time. A monolithic 3-Tier deployment can only
scale as a single unit, meaning we would provision peak capacity for *every* module
simultaneously — paying for idle Reporting and Grade capacity to survive registration week.

The Reporting & Analytics Service additionally reads from a **read replica / read-optimised
store** rather than the transactional databases. Administrator reports such as *"all Business
school courses over 90% capacity"* are analytical scans; isolating them prevents a heavy
report from degrading enrolment response times during a spike.

### 2.2 Maintainability — escaping the LegacyEnroll problem

The existing system is described as *"a monolithic application that has been in use for over
20 years… difficult to maintain, slow."* Replacing one monolith with a differently-shaped
monolith reproduces the original failure mode. Microservices address the root cause directly:

- **Bounded contexts.** Each service owns one business capability and one datastore. A
  change to grade approval logic cannot accidentally break catalogue search, because they
  do not share code or schema.
- **Independent deployability.** A defect fix in Reporting ships without regression-testing
  or redeploying Enrolment. The 20-year-old system's maintenance cost came largely from the
  fact that any change required revalidating everything.
- **Team parallelism.** Six services map cleanly onto our 5–6 person team, and onto the
  university IT department's long-term ownership model.
- **Strangler-fig migration.** The API Gateway lets us route individual endpoints to
  LegacyEnroll or NexusEnroll during transition, so the legacy system can be retired
  incrementally rather than in one high-risk cutover.

### 2.3 Ability to integrate future services — the financial aid system

The brief specifically names *"the ability to integrate with future services (e.g. a new
financial aid system)"* as an evaluation factor. Our architecture supports this through
**two independent integration seams**:

1. **Synchronous:** the financial aid system calls published REST APIs through the API
   Gateway (e.g. to read a student's current credit load). No existing service is modified.
2. **Asynchronous:** the financial aid system subscribes to domain events already published
   on the Message Broker — `StudentEnrolled`, `StudentDropped`, `GradesSubmitted`. It
   receives the data it needs **without any existing service knowing it exists.**

This is the concrete payoff of event-driven decoupling: adding a consumer is a zero-change
operation on the producer side. In a 3-Tier monolith, the same integration would require
modifying the enrolment business logic to call the financial aid system, adding a dependency
in the wrong direction and violating the Open/Closed Principle at architectural scale.

### 2.4 Modern accessibility — one back-end, two front-ends

The requirements state the front-end *"should be a single-page application (SPA) that
communicates with the back-end via APIs"* and that *"the same back-end services must be
usable by both the web application and a future mobile application."*

The API Gateway satisfies this literally. It is the single entry point exposing one versioned
REST/JSON contract; the SPA and the future mobile app are simply two clients of that same
contract. Because services are API-first by construction — the Service API layer is a named
tier in every service — there is no possibility of business logic leaking into a web-specific
presentation layer that mobile could not reuse.

### 2.5 Decoupled notifications

The brief requires that notification *"be automated and decoupled from the core enrolment
logic."* The Message Broker plus a standalone Notification Service enforces this
architecturally, not merely by convention: the Enrolment Service publishes a
`StudentDropped` event and returns. It holds no reference to, and no knowledge of, the
notification subscribers. Adding "notify the department head" later requires no change to
enrolment code at all. At the class level this is realised with the **Observer** pattern
(see Part B).

### 2.6 Robustness

- **Fault isolation.** If the Notification Service fails, enrolment still succeeds — events
  queue in the broker and are delivered on recovery. In a monolith, a failing email
  subsystem inside the enrolment call path can fail the enrolment itself.
- **Graceful degradation.** If Reporting is down, students can still register.
- **Retry and dead-letter handling.** Broker-mediated delivery gives us at-least-once
  semantics with a dead-letter queue, feeding the required *"administrators should be
  notified of any system-wide errors"* behaviour.

### 2.7 The critical trade-off we accepted: transaction boundaries

Microservices are known to complicate transactions, and the brief has a hard requirement:

> *"All enrolment operations (adding/dropping a course) must be treated as transactions…
> either the entire operation succeeds (the student is enrolled, the class capacity is
> updated, and the schedule is modified) or the entire operation fails, leaving no partial
> state changes."*

**Design decision:** we deliberately placed *all three* of those state changes — enrolment
record, section capacity, and student schedule — **inside the Enrolment Service's own
bounded context.** This makes the enrolment transaction a **single local ACID transaction**,
not a distributed one. We therefore satisfy the all-or-nothing requirement without incurring
the complexity, partial-failure surface, and compensating-logic burden of a Saga or
two-phase commit.

This is a service-boundary decision driven by a transactional invariant, and it is worth
stating explicitly in the report: *the transaction requirement dictated where we drew the
service boundary, rather than the boundary dictating a distributed transaction.* Within the
Business Logic layer the transaction is implemented with the **Command** pattern, giving each
operation `execute()` / `undo()` semantics and a clean rollback path.

Cross-service consistency (e.g. Academic Records reflecting a new enrolment) is **eventual**
and event-driven, which is acceptable because no business invariant requires it to be
immediate.

---

## A3. Rejected Alternatives — Why Not the Others

A justification is only credible if it says what was rejected and why. Include this section
in the report.

### Pure 3-Tier Architecture — rejected

| Consideration | Assessment |
|---|---|
| Simplicity | ✅ Genuinely the simplest to build and diagram |
| Peak-load scalability | ❌ Scales only as a whole unit; cannot scale enrolment independently of reporting |
| Shared database | ❌ Single RDBMS becomes the bottleneck and single point of failure precisely at peak |
| Maintainability | ❌ Reproduces LegacyEnroll's core defect — one deployable unit where any change risks everything |
| Future integration | ❌ Financial aid integration requires editing existing business logic |
| Fault isolation | ❌ A failure in reporting or notification can take down enrolment |

**Verdict:** rejected as the *system-level* pattern because it cannot answer the explicit
scalability and future-integration requirements. **Retained as the service-level pattern,**
where its separation-of-concerns strength applies without its deployment-coupling weakness.

### Service-Oriented Architecture (SOA) — rejected

| Consideration | Assessment |
|---|---|
| Integration | ✅ An ESB is a strong integration story for the financial aid system |
| Reuse | ✅ Coarse-grained shared services promote reuse |
| Central bottleneck | ❌ The ESB is a single point of failure and a throughput ceiling — the exact opposite of what peak enrolment needs |
| Granularity | ❌ Coarse-grained services prevent scaling *just* enrolment |
| Shared data layer | ❌ Typically retains a shared data tier, reintroducing schema coupling |
| Governance overhead | ❌ ESB configuration and canonical-schema governance is heavy for a university IT department and for a 4-week project |

**Verdict:** rejected. SOA's integration advantage is fully obtainable from an API Gateway
plus a message broker, without inheriting the ESB bottleneck.

### Pure Microservices (no internal tier structure) — rejected

Not wrong, but **incomplete for this assignment.** It describes decomposition without
prescribing internal organisation, leaving no named business logic layer for Part B to
target. Adding 3-Tier layering inside each service costs nothing and makes the design
explicit.

---

## A4. Component Responsibilities

For the Part A3 requirement: *"For each major component, briefly describe its function and
responsibilities."*

### Presentation clients (out of design scope, shown for context)

| Component | Responsibility |
|---|---|
| Web SPA | Single-page application; all rendering client-side, communicates only via REST/JSON |
| Mobile App | Future native client; consumes the identical API contract |
| Admin Console | Administrator tooling for course/program/account management and reporting |
| Financial Aid System | *Future external system*; integrates via published API + event subscription |

### Cross-cutting infrastructure

| Component | Responsibility |
|---|---|
| **API Gateway** | Single entry point. Request routing, API composition, authentication/authorisation enforcement, rate limiting and throttling (critical during registration surges), API versioning, TLS termination. Shields clients from service topology so services can be split or moved without client changes. |
| **Identity & Access Service** | Issues and validates tokens; owns role definitions (Student / Faculty / Administrator) and enforces role-based access — the basis for "administrators can manually override enrolment rules" while students cannot. |
| **Message Broker (Event Bus)** | Asynchronous, durable, publish/subscribe transport for domain events. Decouples producers from consumers, buffers spikes, provides retry and dead-letter handling. The architectural mechanism satisfying the "decoupled notification" requirement. |

### Business microservices

| Service | Responsibility | Key business-tier objects |
|---|---|---|
| **Course Catalogue Service** | Course and section definitions, degree programs, prerequisite metadata, real-time seat availability, multi-criteria search (department, course number, keyword, instructor). Owns course/program CRUD for administrators and course-change requests from faculty. | `Course`, `CourseSection`, `TimeSlot`, `DegreeProgram`, `CourseCatalog`, `CourseChangeRequest`, `CourseSearchQuery` + `CourseSearchQueryBuilder`, `CatalogQueryDirector` |
| **Enrolment Service** | The transactional core. Add/drop, the three validation rules, waitlist management, administrator overrides, schedule construction. Owns the enrolment ACID transaction. Publishes `StudentEnrolled` / `StudentDropped` / `SeatReleased`. | `EnrollmentFacade`, `Enrollment`, `EnrollmentValidator` + rules, `AddCourseCommand`, `DropCourseCommand`, `TransactionManager`, `Waitlist`, `StudentSchedule` |
| **Academic Records Service** | Grade capture and the Pending→Submitted approval workflow, batch grade processing with per-item error isolation, transcripts, completed-course history, degree progress and remaining-requirement calculation. | `AcademicRecord`, `GradeSubmission` + state classes, `BatchGradeProcessor`, `Grade`, `Transcript`, `ProgressTracker` |
| **User Management Service** | Student, faculty and administrator account lifecycle (create/edit/deactivate), profile and contact data, advisor–advisee relationships, faculty–section assignments. | `Person`, `Student`, `Faculty`, `Administrator`, `AccountManager` |
| **Reporting & Analytics Service** | Generates enrolment statistics by department/semester, faculty workload, course popularity trends, and threshold reports (>90% capacity). Reads from a read-optimised replica; renders to tabular/exportable output. | `ReportFactory`, `EnrolmentStatisticsReport`, `FacultyWorkloadReport`, `CoursePopularityReport`, `CapacityThresholdReport` |
| **Notification Service** | Subscribes to domain events and dispatches notifications through pluggable channels. Holds the observer registry: waitlisted students, academic advisors, system administrators. Contains no enrolment logic. | `NotificationService`, `NotificationPublisher`, `WaitlistObserver`, `AdvisorObserver`, `AdminAlertObserver`, `EmailChannel` |

### Internal layering (present in every service)

| Layer | Responsibility |
|---|---|
| **Service API layer** | REST controllers, request/response DTOs, input validation, serialisation, event publishing/subscribing. Contains **no business rules**. |
| **Business Logic layer** | ⭐ *The design and implementation focus of Part B.* Domain entities, business rules, design pattern participants, transaction orchestration. Depends only on repository **interfaces**, never on concrete persistence — the Dependency Inversion Principle applied at the tier boundary. |
| **Data Access layer** | Repository implementations, ORM mapping, query construction, transaction primitives. Substitutable — the in-memory implementation used in the proof-of-concept satisfies the same interfaces as a production database implementation, which is our Liskov Substitution Principle example. |

---

## A5. Architectural Principles Applied

Useful for cross-referencing Part B5 from Part A:

| Principle | Architectural application |
|---|---|
| Single Responsibility | Each service owns exactly one business capability; each internal layer owns one technical concern |
| Open/Closed | New event consumers (financial aid, analytics) are added without modifying producers |
| Dependency Inversion | The Business Logic layer defines repository interfaces; the Data Access layer implements them — dependencies point inward toward the domain |
| Interface Segregation | The API Gateway exposes role-specific endpoint groups rather than one god-API |
| Separation of Concerns | Enforced twice — horizontally across services, vertically across tiers |
| DRY | Shared capability lives in exactly one owning service; no duplicated enrolment rules |
| KISS | Local ACID transactions chosen over Sagas; API Gateway + broker chosen over an ESB |

---

## A6. Diagram Index

All diagrams are draw.io (`.drawio` / mxGraph XML) files in `DESIGN/diagrams/`.
Open with **File → Open From → Device** at <https://app.diagrams.net>, or the
*Draw.io Integration* extension in VS Code.

| # | File | Diagram | Brief requirement |
|---|---|---|---|
| 1 | `01-architecture.drawio` | System architecture | Part A3 |
| 2 | `02-class-diagram-domain.drawio` | Business-tier domain model | Part B4 — Class Diagram |
| 3 | `03-class-diagram-patterns.drawio` | Design pattern structures | Part B4 / B7 — patterns highlighted |
| 4 | `04-activity-diagrams.drawio` | Activity — enrolment & grade submission | Part B4 — Activity Diagram |
| 5 | `05-sequence-diagrams.drawio` | Sequence — enrol, and drop→waitlist notify | Part B4 — Sequence Diagram |
| 6 | `06-state-diagrams.drawio` | State — GradeSubmission, Enrollment, CourseChangeRequest | Part B4 — State Diagram |
