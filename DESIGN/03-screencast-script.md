# Screencast Script — NexusEnroll

**Target runtime: 9 min 40 s** (hard limit 10:00 — the brief's wording is *"should not exceed
10 minutes"*, so leave the buffer).

> **Brief, submission guideline 3, verbatim:**
> *"A screencast video of the functionality of the implemented solution should be recorded and
> included with the submission. The video should not exceed 10 minutes of recording time and
> should focus on the interaction of the solution using the user interfaces or **test cases to
> interact with the business logic tier**."*

That last clause sets the whole shape of this video: it is a **demo-led** recording, not a
slide reading. `main.py` *is* the test-case harness that drives the business logic tier, so the
spine of the video is one uninterrupted run of it, pausing to show the class behind each result.

Every row below names the **exact file and line** to have on screen, so nobody has to hunt for
code while recording.

---

## Before you hit record

- [ ] `cd src && python -m nexusenroll.main` runs clean end to end (it does — verify anyway)
- [ ] Terminal font at **16pt+**, window ~110 columns; anything smaller is unreadable at 1080p
- [ ] Editor open with these files already in tabs, in this order:
      `main.py` · `facade_enrollment.py` · `strategy_validation.py` · `command_enrollment.py` ·
      `state_grades.py` · `observer_notifications.py` · `factory_reports.py` ·
      `builder_search.py` · `composition_root.py`
- [ ] Diagram 01 and diagram 03 exported to PDF and open in a viewer (for sections 1 and 8)
- [ ] Editor line numbers **on** — the whole script depends on them
- [ ] Close Slack/mail; silence notifications
- [ ] Do one full dry run with a stopwatch before the take that counts

**Split the narration across the team.** The 40% criterion rewards first-hand explanation, so
whoever implemented a pattern should be the one narrating it (§ 3–7 map onto the work split in
`DESIGN/README.md`).

---

## § 1 — Title and architecture · 0:00 → 0:45 · *45 s*

| On screen | Say | Code / artefact |
|---|---|---|
| Title slide: project, module code, all team names + student IDs | "NexusEnroll — a modernisation of the university's twenty-year-old LegacyEnroll monolith. Team members are on screen." | title slide |
| Diagram 01, full canvas | "System level, we chose **microservices**; inside each service, **3-Tier**. Microservices answer the scalability and future-integration requirements. The internal 3-tier layering gives us a named Business Logic layer — which is what this whole video is about." | `DESIGN/diagrams/01-architecture.drawio` |
| Point at the broker, then the Notification Service | "Services talk synchronously through the API Gateway and asynchronously over the message broker. That broker is what makes notification *architecturally* decoupled, not decoupled by convention." | same |

> ⏱ **Discipline point.** 45 seconds. Do not narrate the rejected alternatives here — they are
> in the report and they will eat two minutes you cannot spare.

---

## § 2 — The code mirrors the architecture · 0:45 → 1:15 · *30 s*

| On screen | Say | Code |
|---|---|---|
| File tree of `src/nexusenroll/` | "The package layout is the architecture. `domain` is the Business Logic layer, `repositories` is Data Access, `services` holds the three modules the brief names." | `src/nexusenroll/` |
| Open `repositories/interfaces.py`, scroll to the header comment | "These repository interfaces are **declared in the business layer** and implemented in the data layer, so dependencies point inward at the domain. That's Dependency Inversion at the tier boundary." | `repositories/interfaces.py:1-18`, `IEnrollmentRepository` at **:23** |
| Terminal: `cd src && python -m nexusenroll.main` — let the header print, then stop reading aloud | "One command, no dependencies, no database. Four acts: the three modules, then the proofs." | `main.py:375` |

---

## § 3 — Student module · 1:15 → 3:05 · *1 min 50 s*

### 3a. Catalogue search — Builder ⑦ · *40 s*

| On screen | Say | Code |
|---|---|---|
| Demo act **1.1** output table | "The §3.1 use case verbatim: browse all Computer Science courses this semester taught by one professor. Note the columns — name, description, instructor, **available seats versus total capacity**, schedule, prerequisites. Every real-time field the requirement lists." | `main.py:73` |
| `builder_search.py`, `CatalogQueryDirector` | "Four optional filters is sixteen combinations. Rather than a seven-parameter search with nulls everywhere, the **Builder** assembles the query step by step and the **Director** holds the reusable recipes." | `builder_search.py:212`, recipe at **:244** |
| Demo act **1.2** | "And `build()` validates. An occupancy of 1.7 is refused at construction — **an invalid query object can never exist**. Fail Fast on a value object." | `builder_search.py:189-210`; demo `main.py:88` |

### 3b. Enrolment and validation — Facade ⑥ + Strategy ① · *45 s*

| On screen | Say | Code |
|---|---|---|
| Demo act **1.3**: seats 0/30 → 1/30 | "Kavith has completed CS-201, so he enrols. One method call from the client's point of view." | `main.py:99` |
| `facade_enrollment.py`, `enrol()` | "That one call is the **Facade**. Behind it: validate, build a command, run it atomically, publish an event. The API layer holds no business rules, so the web SPA and a future mobile app consume exactly the same operation." | `facade_enrollment.py:109` |
| Demo act **1.4**, both refusals | "Dilini hasn't done the prerequisite — refused. Isuru has a Monday clash — refused, and it names the clashing slot." | `main.py:106` |
| `strategy_validation.py`, `validate_all()` | "Three rules, three classes, one **Strategy** interface. Look at this loop — there is **no early return**. It iterates to the end and merges, so a student sees *every* problem at once, not just the first. That is precisely why we rejected Decorator: a decorator chain short-circuits." | `strategy_validation.py:259-269`; interface at **:64** |

### 3c. Waitlist, schedule, progress · *25 s*

| On screen | Say | Code |
|---|---|---|
| Demo act **1.5** | "BUS210-A is full. Nethmi fails **only** the capacity rule, so she's eligible — she gets queued at position 1 rather than rejected. Collapsing 'full' and 'ineligible' into one failure state would make the waitlist requirement unimplementable." | `main.py:115`; branch at `facade_enrollment.py:132-139` |
| Demo acts **1.6** and **1.7** | "Schedule as a calendar view, then completed courses with grades and what's still required for the degree — 40% complete, 54 credits outstanding." | `main.py:122`, `main.py:130` |

---

## § 4 — Faculty module · 3:05 → 4:35 · *1 min 30 s*

| On screen | Say | Code |
|---|---|---|
| Demo act **2.1** | "Real-time roster with names, IDs and contact details. A lecturer sees only their own sections." | `main.py:147`; `services/faculty_service.py:53` |
| Demo act **2.2** — the three-row batch | "Here's the §3.2 use case. Three grades submitted: one valid, one with an invalid letter, one for a student not enrolled. Two rejected — **and the valid one survives**." | `main.py:153` |
| `state_grades.py`, `BatchGradeProcessor.validate_batch` | "Validation runs **per entry, not per batch**. One bad letter grade in a roster of two hundred rejects one entry, not two hundred. That is the 'without losing other submitted grades' requirement, structurally." | `state_grades.py:216-239` |
| Demo act **2.3** | "Draft to PendingApproval — the 'Pending' state the brief names by name." | `main.py:169` |
| `state_grades.py`, the four state classes | "The **State** pattern. Each ConcreteState decides for itself which operations are legal. `DraftState` permits `addEntry`; `PendingApprovalState` permits approve and reject but **refuses** `addEntry`; `PartiallyRejectedState` permits corrections while keeping accepted grades; `SubmittedState` is terminal — and note its body is empty. That emptiness *is* the behaviour." | `state_grades.py:97`, **:115**, **:141**, **:167** |
| Demo act **2.4** | "Course change request: capacity 3 → 5. It's pending, and the live section is **still 3**. The catalogue is untouched until an administrator approves — enforced by the state machine, not by convention." | `main.py:176`; `state_course_change.py:74` |

---

## § 5 — Administrator module · 4:35 → 6:10 · *1 min 35 s*

| On screen | Say | Code |
|---|---|---|
| Demo act **3.1** | "Administrator approves the batch. State goes to Submitted and the academic records update — that's the **entry action** of `SubmittedState`, not something the caller had to remember to do." | `main.py:198`; `state_grades.py:241` |
| Demo act **3.2** — capacity 3 → 5, waitlist email fires | "Approving the change applies it to the live section. And watch — raising the capacity released a seat, so the **existing** waitlist observer fired with no extra code. Two independently designed features composed because both are event-driven." | `main.py:205`; `state_course_change.py:140-160` |
| Demo act **3.4** | "Force-add into a full class. The standard student path is refused. A clerk without override rights is refused. The registrar succeeds." | `main.py:226` |
| `composition_root.py:194` | "**This one line is the override.** It's the same rule classes with `CapacityRule` left out of the list. There is no `if admin` branch anywhere inside a rule — the administrator path simply composes a different Strategy list." | `composition_root.py:194`; consumed at `services/admin_service.py:126` and **:149** |
| Demo act **3.5** — three report tables | "Enrolment statistics by department and semester, faculty workload, course popularity." | `main.py:241` |
| `factory_reports.py`, `create_report` | "All four created through a **Factory Method**. The administrator module asks by *kind* and receives a `Report` — it never names a concrete class, so a fifth report type touches no calling code." | `factory_reports.py:253`; registry at `composition_root.py:217-234` |
| Demo act **3.6** | "And the §3.3 use case: Business school courses over 90% capacity — BUS-330 at 100%. Factory Method created the report; **Builder** built its criteria, using the same builder as student search. Then the same data as CSV, for the 'table or spreadsheet' requirement." | `main.py:252`; `factory_reports.py:192`, `builder_search.py:255` |

---

## § 6 — The proofs · 6:10 → 9:00 · *2 min 50 s* ⭐ **the most valuable section**

> Lead with these if you have to cut. A pattern shown **working** outscores a pattern described.

### 6a. Command ② rollback · *60 s*

| On screen | Say | Code |
|---|---|---|
| `command_enrollment.py`, `execute()` steps 1–3 | "The requirement says an enrolment either wholly succeeds or wholly fails. These three numbered steps are **exactly** the three state changes the brief enumerates: create the enrolment, reserve the seat, modify the schedule." | `command_enrollment.py:150-176` |
| Demo act **4.1**, BEFORE line | "Zero, zero, zero. Now we force step 3 to raise — steps 1 and 2 will already have changed state." | `main.py:275` |
| AFTER line: `NO PARTIAL STATE SURVIVED: True` | "All three back to zero. `undo()` ran in reverse — 3, 2, 1 — on every completed step." | — |
| `command_enrollment.py:296-309` | "And here's the mechanism. The command is pushed onto the stack **before** it executes, so a command that fails part-way through is still on the stack to be undone. **We got this wrong the first time** — we pushed after success, the proof printed `False`, and the demo caught a real bug in our own transaction manager. It's in the commit history." | `command_enrollment.py:305-308` |
| Audit log lines | "Same structure gives the administrator a replayable audit log for free." | `command_enrollment.py:321` |

> 💡 **Say the bug out loud.** An examiner hearing "our own demo caught a real defect and here's
> the fix" learns the proof-of-concept is genuinely executable. Hiding it gains nothing.

### 6b. State ③ illegal transition · *40 s*

| On screen | Say | Code |
|---|---|---|
| Demo act **4.2**, both `IllegalTransition` lines | "`addEntry` on a **Submitted** batch — refused. `addEntry` on a **PendingApproval** batch — refused. The entry set is locked while an administrator decides." | `main.py:304` |
| `state_grades.py:71-95` | "Nothing in `GradeSubmission` checks a status flag. The base state's defaults raise `IllegalTransition`, and a ConcreteState overrides **only** what's legal in it. So an unhandled operation fails loudly instead of silently corrupting a batch of two hundred grades. Fail Fast." | `state_grades.py:60-95` |

### 6c. Observer ④ decoupling · *70 s*

| On screen | Say | Code |
|---|---|---|
| Diagram 05 page 2, the red boundary | "This is the clearest single image in our design pack. Left of the red line, the enrolment transaction. Right of it, the notification fan-out." | `DESIGN/diagrams/05-sequence-diagrams.drawio` p2 |
| Demo act **4.3** — two emails fire | "Tharindu drops BUS-210. The waitlisted student is emailed that a spot opened; the advisor is emailed because it's a degree-critical course." | `main.py:327` |
| `facade_enrollment.py:190-199` | "And this is all the enrolment code does — publish two events and return. It holds **no reference** to `WaitlistObserver`, `AdvisorObserver` or `EmailChannel`, and never learns whether anything was delivered. That is what the brief means by 'automated and decoupled'." | `facade_enrollment.py:175-200` |
| Demo act **4.4** | "Now we attach an observer whose mail channel always throws, and drop again. One isolated failure logged — **and the drop still succeeded**. A dead mail server cannot fail a transaction that has already committed." | `main.py:341`; `observer_notifications.py:132-149` |
| Demo act **4.5** | "This audit subscriber stands in for the future financial aid system. It has seen all seven enrol and drop events, and not one line of enrolment code knows it exists. Adding it was an `attach()` call — Open/Closed, at runtime." | `main.py:356`; `composition_root.py:171-174` |

---

## § 7 — Singleton rejected · 9:00 → 9:30 · *30 s*

| On screen | Say | Code |
|---|---|---|
| Diagram 03, rejected-patterns panel | "One design decision worth thirty seconds. Exactly one observer registry must exist — a second one would swallow notifications silently. The obvious answer is Singleton." | `DESIGN/diagrams/03-class-diagram-patterns.drawio` |
| `composition_root.py:157-174` | "We rejected it. Singleton conflicts with SRP, DIP and OCP — and we'd already committed to constructor injection everywhere, which means the single-instance guarantee was coming from **the wiring, not the pattern**. So: one publisher, constructed here, injected everywhere. Same guarantee, no global access point, every dependency visible in a constructor. And a Python module is already a singleton, so `getInstance()` would have been un-idiomatic too." | `composition_root.py:1-40` (header) and **:157** |

---

## § 8 — Close · 9:30 → 9:40 · *10 s*

| On screen | Say |
|---|---|
| Diagram 03 full canvas, or the closing table `main.py` prints | "Seven patterns, all three GoF families, every one traceable to a sentence in the requirements. Thank you." |

---

## Pattern → demo act → source, at a glance

Pin this next to the recording setup.

| # | Pattern | Demo act | Class structure | Script § |
|---|---|---|---|---|
| ① | **Strategy** | 1.4, 3.4 | `patterns/strategy_validation.py:64` (interface), `:236` (context), `:259` (the loop) | 3b, 5 |
| ② | **Command** | 1.3, **4.1** | `patterns/command_enrollment.py:90`, `:111` (`execute` at `:150`), `:279` (`run_atomic` at `:291`) | 6a |
| ③ | **State** | 2.2–2.4, 3.1–3.2, **4.2** | `patterns/state_grades.py:60`, `:97`, `:115`, `:141`, `:167`; `patterns/state_course_change.py:40` | 4, 6b |
| ④ | **Observer** | **4.3**–4.6 | `patterns/observer_notifications.py:106` (subject, `publish` at `:132`), `:151`, `:186`, `:227` | 6c |
| ⑤ | **Factory Method** | 3.5, 3.6 | `patterns/factory_reports.py:239` (`create_report` at `:253`), products at `:104`–`:192` | 5 |
| ⑥ | **Facade** | 1.3, 1.5, 4.1, 4.3 | `patterns/facade_enrollment.py:79` (`enrol` at `:109`, `drop` at `:175`) | 3b, 6c |
| ⑦ | **Builder** | 1.1, 1.2, 3.6 | `patterns/builder_search.py:114`, `:140` (`build` at `:189`), `:212` (director) | 3a, 5 |
| — | ~~Singleton~~ | — | replaced by `composition_root.py:157` | 7 |

---

## If you run long — cut in this order

1. § 5 account management chatter (act 3.3) — **the demo already prints it**, just don't narrate
2. § 3c schedule/progress narration — let acts 1.6 and 1.7 scroll silently
3. § 4 roster commentary (act 2.1) — one sentence, not three
4. § 1 architecture — down to 30 s, pointing only at the broker

**Never cut § 6.** It is 40% of the grade demonstrated live.

---

## Recording notes

- **Don't read the terminal aloud.** The examiner can read. Narrate the *why* while the output
  is on screen.
- **Pause the run between acts.** Either `input()` between acts or run each act separately —
  a wall of scrolling output is unwatchable.
- **Scroll to a cited line before speaking about it**, not while. Dead air for one second beats
  narration over a moving screen.
- **One take per section**, stitched afterwards. Re-recording ten minutes because of one stumble
  at 8:30 is a bad trade.
