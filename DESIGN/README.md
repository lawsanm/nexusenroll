# NexusEnroll — Design Package

Design and planning deliverables for **SCS 2303 Software Architecture, Assignment 3**.
Implementation language: **Python**. Deadline: **20 August 2026**.

---

## Architectural decision (locked)

> **Microservices Architecture at system level + 3-Tier Architecture inside each service.**

The brief permits *"one or a combination of patterns."* The combination is deliberate:
microservices answer the scalability and future-integration requirements; the internal 3-tier
layering gives us a named **Business Logic layer** for Part B to target, as Part B4 instructs.
Full justification, including why SOA and pure 3-Tier were rejected, is in
[`00-architecture-decision.md`](00-architecture-decision.md).

---

## Contents

| File | Covers | Brief section | Weight |
|---|---|---|---|
| [`00-architecture-decision.md`](00-architecture-decision.md) | Pattern choice, justification, rejected alternatives, component responsibilities | Part A1–A3 | **30%** |
| [`01-design-patterns.md`](01-design-patterns.md) | Seven patterns applied (where, why, what breaks without each) **plus the patterns considered and rejected, including Singleton** | Part B2–B3 | **40%** |
| [`02-design-principles.md`](02-design-principles.md) | Concrete example per principle + traceability matrix | Part B5 | — |
| `diagrams/*.drawio` | All required UML | Part B4 | 15% + |

## Diagrams

Six files, **ten pages** total, 296 shapes.

| File | Pages | Brief requirement |
|---|---|---|
| `01-architecture.drawio` | System architecture | Part A3 — *"Draw and Describe the Architecture"* |
| `02-class-diagram-domain.drawio` | Business-tier domain model | Part B4 — Class Diagram |
| `03-class-diagram-patterns.drawio` | Seven pattern structures in labelled zones ①–⑦ + a rejected-patterns panel | Part B4 / B7 — *"highlighting the design patterns used"* |
| `04-activity-diagrams.drawio` | ① Course enrolment ② Batch grade submission | Part B4 — Activity Diagram |
| `05-sequence-diagrams.drawio` | ① Student enrols ② Drop → waitlist notification | Part B4 — Sequence Diagram |
| `06-state-diagrams.drawio` | ① GradeSubmission ② Enrollment ③ CourseChangeRequest | Part B4 — State Diagram |

Every diagram requirement in the brief is covered. Collaboration Diagram is the brief's
*optional alternative* to Sequence, so it is intentionally omitted.

---

## Opening the diagrams

**Browser (nothing to install)**
1. Go to <https://app.diagrams.net>
2. **File → Open From → Device**, pick a `.drawio` file
3. Multi-page files appear as tabs along the bottom — check every tab

**VS Code** — install the *Draw.io Integration* extension (`hediet.vscode-drawio`), then just
click any `.drawio` file.

**Exporting for the report**
- `File → Export as → PNG`, tick **Transparent Background** off and set **Zoom 200%** for
  print-quality figures
- For the wide diagrams (01, 03) export as **PDF** with *Fit to page* — they are A2-sized
  canvases and will be unreadable if squeezed into an A4 PNG
- `File → Export as → PNG → Selection Only` to pull out a single pattern zone from diagram 03
  when you want to discuss one pattern in isolation

---

## Reading order

Read the diagrams in this order — each one assumes the previous:

1. **01 Architecture** — where the business logic lives
2. **02 Domain model** — what the business objects are
3. **03 Pattern structures** — how the patterns attach to those objects
4. **04 Activity** — the process flow through them
5. **05 Sequence** — the message-level detail of two scenarios
6. **06 State** — the lifecycles the flows move objects through

Diagrams 02 and 03 share class names and are designed to be read side by side. Diagram 03's
zone numbers ①–⑦ are used consistently across every other diagram and both markdown documents.

---

## Suggested work split (5–6 people)

The design is deliberately partitioned so members can work in parallel without merge conflicts.

| Owner | Deliverable |
|---|---|
| **1** | Part A report sections: architecture write-up from `00`, plus tidy/annotate `01-architecture.drawio` |
| **2** | Student module code: catalogue search + Builder ⑦, Strategy ① rules, schedule |
| **3** | Enrolment core code: Facade ⑥, Command ②, TransactionManager, Observer ④, composition root in `main.py` |
| **4** | Faculty module code: State ③ grade lifecycle, batch processor with error isolation |
| **5** | Administrator module code: Factory Method ⑤ reports, account management, override |
| **6** | Report assembly, diagram export, screencast recording, VLE submission |

Everyone writes the *pattern explanation* prose for the pattern they implemented — first-hand
explanations read better and the 40% criterion rewards exactly that.

---

## Remaining work after this design package

- [ ] Part B6 — implement the Python proof-of-concept against these diagrams
- [ ] Part B7 — assemble the report (pull text from `00`, `01`, `02`; export diagrams as images)
- [ ] Record the ≤10-minute screencast
- [ ] Upload document + source + video to VLE by **20 August 2026**

The full tickable requirement list is in `../ASSIGNMENT-3-CHECKLIST.md`.

**Screencast tip:** the three most persuasive things to demonstrate live are a Command rollback
leaving `enrolledCount` unchanged after a forced failure, an `IllegalTransition` raised when
`addEntry()` is called on a submission in `PendingApprovalState`, and a waitlist notification
firing from a drop. Each proves a pattern works
rather than merely exists.
