# Screencast Script — NexusEnroll

**Target runtime 9:40** (hard limit 10:00 — the brief says the video *"should not exceed 10
minutes"*, so we keep twenty seconds of buffer).

> **Brief, submission guideline 3, verbatim:**
> *"A screencast video of the functionality of the implemented solution should be recorded and
> included with the submission. The video should not exceed 10 minutes of recording time and
> should focus on the interaction of the solution using the user interfaces or **test cases to
> interact with the business logic tier**."*

`main.py` **is** the test-case harness the brief asks for, so the video is a single run of it,
narrated. But the run is only the evidence — **the subject of the video is the seven patterns.**
Eight of the nine and a half minutes are spent on a pattern; the module tour is compressed to
the moments where a pattern is visibly doing the work.

**How to read this script.** Each segment gives you the clock, what is on screen, and then the
narration written out as continuous speech. Read it in your own words — it is written to be
*spoken*, not recited. Square brackets are stage directions, never said out loud.

**Split the narration across the team.** The 40% criterion rewards first-hand explanation, so
whoever implemented a pattern narrates that pattern's segment (the split is in
`DESIGN/README.md`).

---

## Before you hit record

- [ ] `cd src && python -m nexusenroll.main` runs clean end to end
- [ ] Terminal at **16pt+**, ~110 columns — anything smaller is unreadable at 1080p
- [ ] Editor line numbers **on**; this whole script depends on them
- [ ] Tabs open in narration order: `main.py` · `builder_search.py` · `facade_enrollment.py` ·
      `strategy_validation.py` · `state_grades.py` · `state_course_change.py` ·
      `factory_reports.py` · `command_enrollment.py` · `observer_notifications.py` ·
      `composition_root.py`
- [ ] Diagrams 01, 03 and 05 open as PDFs in a viewer (`DESIGN/diagrams/pdf/`)
- [ ] Notifications silenced, Slack and mail closed
- [ ] One full dry run with a stopwatch before the take that counts

---

## 1 · Opening — the architecture in forty seconds
**0:00 → 0:40** · *title slide, then diagram 01*

*[Title slide: project name, module code, every team member with student ID.]*

> NexusEnroll is our replacement for LegacyEnroll, the university's twenty-year-old enrolment
> monolith. We're the team on screen.

*[Switch to diagram 01, full canvas.]*

> Two architectural decisions, and then we'll spend the rest of the video on the design.
>
> At system level we chose **microservices** — six of them — because the requirements are about
> scaling registration week and integrating systems that don't exist yet. Inside each service we
> layered **3-Tier**, and that second choice is the one that matters today: it gives us a named
> **Business Logic layer**, which is exactly the tier the brief asks this video to demonstrate.
>
> *[Point at the broker, then the Notification Service.]* Services call each other synchronously
> through the API Gateway, and publish asynchronously over the message broker. That broker is why
> notification is decoupled *architecturally*, not just by convention — and you'll see the same
> shape in the code, in the Observer pattern, about seven minutes from now.

> ⏱ **Discipline point.** Forty seconds, and do **not** narrate the rejected architectures. They
> are in `00-architecture-decision.md` and they will eat two minutes you cannot spare.

---

## 2 · The code is the design
**0:40 → 1:05** · *file tree, then `composition_root.py`*

*[File tree of `src/nexusenroll/`.]*

> The package layout is the architecture. `domain` is the Business Logic layer, `repositories` is
> Data Access, `services` holds the three modules the brief names — and `patterns` is where the
> seven patterns live, one file each, so nothing is hidden.

*[Open `composition_root.py`, scroll to line 138.]*

> Everything is wired in one place. `build_system()` constructs the object graph bottom-up and
> injects it — no globals, no service locator, no `getInstance()` anywhere in the codebase. Keep
> this file in mind; we come back to it twice, and the second time it's to explain a pattern we
> deliberately **didn't** use.

*[Run `python -m nexusenroll.main`, let the header print, then pause the run.]*

---

## 3 · Builder — an invalid query cannot exist
**1:05 → 1:50** · *demo acts 1.1 and 1.2, then `builder_search.py`*

*[Demo act 1.1 output table on screen — `main.py:73`.]*

> This is section 3.1 of the requirements, word for word: browse all Computer Science courses this
> semester taught by one professor. Look at the columns — title, description, instructor,
> **available seats against total capacity**, schedule, prerequisites. Every real-time field the
> requirement lists.

*[Open `builder_search.py`, scroll to `CatalogQueryDirector` at `:212`, then the recipe at `:244`.]*

> Four optional filters means sixteen possible combinations. The alternative was a search method
> with seven parameters and nulls at every call site. Instead the **Builder** assembles the query
> one step at a time, and the **Director** — this class — holds the recipes. `department_taught_by`
> is the one you just watched run.

*[Scroll to `build()` at `:189`. Then show demo act 1.2 — `main.py:88`.]*

> And here's the part that makes Builder worth the classes. `build()` validates before it hands
> anything back. Watch — we ask for a minimum occupancy of one-point-seven. It's refused at
> construction. **An invalid query object never comes into existence**, so nothing downstream ever
> has to defend against one. Fail Fast, on a value object.

---

## 4 · Facade — one call, four collaborators
**1:50 → 2:25** · *demo act 1.3, then `facade_enrollment.py`*

*[Demo act 1.3 — `main.py:99`. Seats go 0/30 → 1/30.]*

> Kavith has completed CS-201, so he enrols. From the client's side that is one method call.

*[Open `facade_enrollment.py`, `enrol()` at `:109`. Scroll slowly through to `:173`.]*

> That one call is the **Facade**, and everything the subsystem does is behind it: validate
> through Strategy, at line 124. Wrap the state changes in a Command and run them atomically, at
> 146. Publish events to the Observers — line 163, and note it is strictly *after* the commit.
>
> The consequence is that the API layer holds **no business rules at all**. The web SPA and the
> future mobile app the brief mentions call this same method and get the same guarantees. Three
> of our seven patterns meet inside this one function, and that's deliberate — the Facade is what
> keeps the client from ever knowing they exist.

---

## 5 · Strategy — every rule, every time
**2:25 → 3:10** · *demo act 1.4, then `strategy_validation.py`*

*[Demo act 1.4 — `main.py:106`. Both refusals visible.]*

> Two refusals. Dilini hasn't completed the prerequisite. Isuru has a Monday clash — and notice
> the message names the section he's clashing with, rather than just saying "conflict".

*[Open `strategy_validation.py`. Interface at `:64`, then the four rules at `:87`, `:128`, `:159`,
`:189`.]*

> One **Strategy** interface, four rule classes: prerequisites, capacity, time conflict, credit
> limit. Each one is a self-contained policy that knows nothing about the others.

*[Scroll to `validate_all()` at `:259`. Hold on the loop for a beat before speaking.]*

> This loop is the whole pattern, and I want to point at one thing in it: **there is no early
> return.** It runs every rule to the end and merges the results, so a student sees *all* their
> problems at once instead of fixing one and resubmitting to discover the next.
>
> That single property is why we rejected Decorator here, which was the obvious alternative — a
> decorator chain short-circuits on the first failure. And it's why adding the credit-limit rule
> later cost us one line in the composition root and zero edits to anything else. Open/Closed,
> concretely.

---

## 6 · The rest of the student module
**3:10 → 3:35** · *demo acts 1.5, 1.6, 1.7 — narrate over the scroll, don't stop*

*[Act 1.5 — `main.py:115`.]*

> BUS210-A is full. Nethmi fails **only** the capacity rule, so she's still eligible — she gets
> queued at position one instead of rejected. That branch is at `facade_enrollment.py:132`, and it
> only exists because Strategy reports *which* rules failed. Collapse "full" and "ineligible" into
> one failure and the waitlist requirement becomes unimplementable.

*[Acts 1.6 and 1.7 — `main.py:122` and `:130`. Let them scroll.]*

> Personal schedule as a calendar view, then academic progress — completed courses with grades,
> what's still required for the degree, forty percent complete, fifty-four credits outstanding.

---

## 7 · State, part one — the grade lifecycle
**3:35 → 4:35** · *demo acts 2.2 and 2.3, then `state_grades.py`*

*[Act 2.1 — `main.py:147` — scroll past with one sentence.]*

> Real-time roster with contact details; a lecturer sees only their own sections.

*[Act 2.2 — `main.py:153`. The three-row batch.]*

> Now section 3.2. Three grades submitted at once: one valid, one with an invalid letter, one for
> a student who isn't enrolled. Two are rejected — **and the valid one survives.**

*[Open `state_grades.py` at `BatchGradeProcessor.validate_batch`, `:216`.]*

> Validation runs per entry, not per batch. One bad letter in a roster of two hundred rejects one
> entry, not two hundred. That's the requirement's "without losing the other submitted grades",
> expressed structurally rather than as a promise.

*[Act 2.3 — `main.py:169`, then the state classes at `:60`, `:97`, `:115`, `:141`, `:167`.]*

> Draft moves to PendingApproval — the "Pending" state the requirement names.
>
> This is the **State** pattern, and each concrete state decides for itself what's legal.
> `DraftState` allows entries to be added. `PendingApprovalState` allows approve and reject, and
> **refuses** `addEntry` — not by checking a flag, but by simply not implementing it, so the base
> class refuses on its behalf. `PartiallyRejectedState` lets a professor correct the bad rows while
> the accepted grades stay put. And `SubmittedState`, at 167 — look at the body. It's empty. That
> emptiness *is* the behaviour: it's terminal, so every operation falls through to a refusal.

---

## 8 · State, part two — and the entry action
**4:35 → 5:15** · *demo acts 2.4 and 3.1–3.2*

*[Act 2.4 — `main.py:176`.]*

> Second application of the same pattern. A lecturer requests a capacity change on BUS210-A,
> three to five. The request is pending — and the live section is **still three**. The catalogue is
> untouched until an administrator approves, and that's enforced by
> `state_course_change.py:74`, not by anybody remembering to check.

*[Act 3.1 — `main.py:198`.]*

> The administrator approves the batch. State goes to Submitted, and the academic records update
> — that's the **entry action** of `SubmittedState`, at `state_grades.py:241`. The caller didn't
> have to remember to do it; entering the state is what does it.

*[Act 3.2 — `main.py:205`. Capacity 3 → 5, and a waitlist email fires above it.]*

> Approving the change applies it to the live section. And watch what came free: raising the
> capacity released a seat, so the **existing** waitlist observer fired, with no code written for
> this case. Two features designed independently composed correctly because both are event-driven.

---

## 9 · Strategy again — the override is a different list
**5:15 → 5:45** · *demo act 3.4, then `composition_root.py:194`*

*[Act 3.4 — `main.py:226`. Three lines of output.]*

> Force-add into a full class. The normal student path is refused. A clerk without override
> rights is refused. The registrar succeeds.

*[Open `composition_root.py`, hold on line 194.]*

> **This one line is the override.** It's the same rule objects as the student list with
> `CapacityRule` left out. There is no `if admin` branch inside any rule anywhere in this codebase
> — the administrator path just composes a different Strategy list.
>
> One honest detail: the rule list alone wasn't enough. `CourseSection` enforces its own capacity
> invariant, so the command has to honour the override at step two as well. Two guards had to
> agree, which is what you'd want — a caller who merely forgets a rule can't push a section over
> capacity.

---

## 10 · Factory Method — asking by kind, not by name
**5:45 → 6:25** · *demo acts 3.5 and 3.6, then `factory_reports.py`*

*[Act 3.5 — `main.py:245`. Three report tables.]*

> Enrolment statistics by department and semester, faculty workload, course popularity.

*[Open `factory_reports.py` at `create_report`, `:253`; then the registry at
`composition_root.py:217`.]*

> All four report kinds come through a **Factory Method**. The administrator module asks for a
> *kind* and receives a `Report` — it never names a concrete class, so adding a fifth report type
> touches no calling code at all. The factory itself doesn't know what a report needs either; each
> registration closes over its own repositories.

*[Act 3.6 — `main.py:256`.]*

> And this is section 3.3 of the brief: Business school courses running over ninety percent
> capacity. BUS-330 at a hundred. Factory Method created the report, and **Builder** built its
> criteria — the same builder and the same director the student catalogue search used, four
> minutes ago. Then the same data as CSV, which is the requirement's "table or spreadsheet".

---

## 11 · Proof one: Command rolls back
**6:25 → 7:25** · ⭐ *demo act 4.1 and `command_enrollment.py`*

> The last three minutes are the ones that matter most, so if we've run long, we've cut something
> else to protect them. Everything so far showed patterns *existing*. These show them **working**.

*[Open `command_enrollment.py`, `execute()` at `:153`. Show the three numbered steps.]*

> The requirement says an enrolment must either wholly succeed or wholly fail. These three
> numbered steps are exactly the three state changes the brief enumerates: create the enrolment
> record, reserve the seat, update the student's schedule. And every one of them records what it
> did, so `undo()` at line 188 can reverse precisely that much.

*[Act 4.1 — `main.py:279`. Read the BEFORE line.]*

> Zero, zero, zero. Now we force step three to raise — so steps one and two will already have
> changed state when it blows up.

*[The AFTER line: `NO PARTIAL STATE SURVIVED: True`.]*

> All three back to zero. `undo()` ran in reverse — three, two, one — over every step that had
> completed.

*[Open `TransactionManager.run_atomic` at `:306`; hold on the comment at `:314`.]*

> Here's the mechanism, and here's the bit worth your attention. The command is pushed onto the
> stack **before** it executes, so a command that dies part-way through is still on the stack to be
> undone.
>
> **We got that wrong the first time.** We pushed after success, this proof printed `False`, and
> our own demo caught a real bug in our own transaction manager. It's in the commit history. We're
> telling you because it's the clearest evidence we have that this is a running proof of concept
> and not a diagram with code next to it.

*[Audit log lines at the end of act 4.1.]*

> And because every operation is a Command object with a `describe()`, the administrator gets a
> replayable audit log for free — `audit_log()` at line 336.

---

## 12 · Proof two: State refuses loudly
**7:25 → 7:55** · *demo act 4.2 and `state_grades.py:60`*

*[Act 4.2 — `main.py:308`. Both `IllegalTransition` lines.]*

> `addEntry` on a **Submitted** batch — refused. `addEntry` on a **PendingApproval** batch —
> refused. The entry set is locked while an administrator is deciding.

*[Scroll to `GradeState` at `:60`, the defaults at `:78`–`:90`.]*

> And nothing in `GradeSubmission` checked a status flag to do that. The base state's default for
> every operation is to raise `IllegalTransition`, and a concrete state overrides **only** what's
> legal within it. So an operation nobody thought about fails loudly, immediately, instead of
> silently corrupting a batch of two hundred grades. That's the safe default, and it's a
> consequence of the pattern rather than of discipline.

---

## 13 · Proof three: Observer, and who doesn't know about whom
**7:55 → 9:05** · *demo acts 4.3–4.5, diagram 05, `observer_notifications.py`*

*[Diagram 05 page 2. Point at the red boundary.]*

> This is the clearest single image in our design pack. Left of the red line, the enrolment
> transaction. Right of it, the notification fan-out. Nothing crosses back.

*[Act 4.3 — `main.py:331`. Two emails fire.]*

> Tharindu drops BUS-210. The waitlisted student is emailed that a seat opened. The advisor is
> emailed because it's a degree-critical course.

*[Open `facade_enrollment.py:190`–`:198`.]*

> And this is everything the enrolment code does about it: publish two events, return. It holds
> **no reference** to `WaitlistObserver`, to `AdvisorObserver`, or to any email channel, and it
> never finds out whether anything was delivered. That's what the brief means by "automated and
> decoupled" — not "we call the notifier last".

*[Act 4.4 — `main.py:345`.]*

> Now the hard case. We attach an observer whose mail channel always throws, and drop again. One
> isolated failure, logged — **and the drop still succeeded.** `publish()` at line 132 catches per
> subscriber, because a dead mail server must not be able to fail a transaction that has already
> committed.

*[Act 4.5 — `main.py:360`.]*

> Last one. This audit subscriber stands in for the financial aid system the brief says will
> integrate later. It has seen every enrol and every drop event in this entire run, and not one
> line of enrolment code knows it exists. Adding it was a single `attach()` call in the composition
> root. That's Open/Closed — at runtime, with no recompilation and no edit to a single existing
> class.

---

## 14 · The pattern we rejected
**9:05 → 9:30** · *diagram 03 rejected-patterns panel, then `composition_root.py:157`*

*[Diagram 03, the rejected-patterns panel.]*

> One decision worth twenty-five seconds, because it's the one we argued about most. Exactly one
> notification publisher must exist — a second one would swallow notifications silently, and
> nobody would ever see an error. The textbook answer is Singleton.

*[`composition_root.py:157`.]*

> We rejected it. Singleton gives a class a second responsibility, its own lifecycle, which breaks
> SRP; it's a global access point, which hides dependencies and breaks DIP; and it's hard to
> substitute, which breaks OCP. And we'd already committed to constructor injection everywhere —
> which means the single-instance guarantee was coming from **the wiring, not the pattern**.
>
> So: one publisher, constructed on this line, injected everywhere. Same guarantee, no global
> state, and every dependency in the system is visible in a constructor signature. The reasoning is
> written up in section 6 of `01-design-patterns.md` — we thought the rejection was worth
> documenting as carefully as the seven we kept.

---

## 15 · Close
**9:30 → 9:40**

*[Diagram 03, full canvas — or the closing table `main.py` prints.]*

> Seven patterns, all three GoF families, every one of them traceable to a sentence in the
> requirements and demonstrated running. Thank you.

---

## Pattern → segment → source

Pin this next to the recording setup.

| # | Pattern | Segment | Demo act | Where it lives |
|---|---|---|---|---|
| ① | **Strategy** | 5, 9 | 1.4, 3.4 | `strategy_validation.py:64` interface · `:236` context · `:259` the loop · override at `composition_root.py:194` |
| ② | **Command** | 11 | 1.3, **4.1** | `command_enrollment.py:90` interface · `:111` (`execute` `:153`, `undo` `:188`) · `:294` invoker (`run_atomic` `:306`) |
| ③ | **State** | 7, 8, 12 | 2.2–2.4, 3.1–3.2, **4.2** | `state_grades.py:60`, `:97`, `:115`, `:141`, `:167` · `state_course_change.py:40`, `:74` |
| ④ | **Observer** | 13 | **4.3**–4.6 | `observer_notifications.py:106` subject (`publish` `:132`) · observers `:151`, `:186`, `:227`, `:250` |
| ⑤ | **Factory Method** | 10 | 3.5, 3.6 | `factory_reports.py:239` (`create_report` `:253`) · products `:104`–`:192` · registry `composition_root.py:217` |
| ⑥ | **Facade** | 4 | 1.3, 1.5, 4.1, 4.3 | `facade_enrollment.py:79` (`enrol` `:109`, `drop` `:175`, `force_add` `:202`) |
| ⑦ | **Builder** | 3, 10 | 1.1, 1.2, 3.6 | `builder_search.py:114` interface · `:140` builder (`build` `:189`) · `:212` director |
| — | ~~Singleton~~ | 14 | — | rejected; replaced by `composition_root.py:157` |

---

## If you run long — cut in this order

1. **Segment 6** entirely. Let acts 1.5–1.7 scroll silently; they carry no pattern.
2. **Segment 2** down to the file tree and one sentence — drop the composition-root preview.
3. **Segment 1** down to thirty seconds, pointing only at the broker.
4. **Segment 10**, the three-report list — the tables speak for themselves; keep only 3.6.

**Never cut segments 11, 12 or 13.** They are the pattern-implementation criterion, demonstrated
live, and they are worth more than everything before them.

---

## Recording notes

- **Don't read the terminal aloud.** The examiner can read. Narrate the *why* while the output
  sits on screen.
- **Pause between acts.** Either drop an `input()` between them or run each act separately — a
  wall of scrolling output is unwatchable.
- **Scroll to a cited line before you start the sentence about it**, not during. One second of
  dead air beats narration over a moving screen.
- **One take per segment**, stitched afterwards. Re-recording ten minutes because of a stumble at
  8:30 is a bad trade.
- **Say the numbers slowly** when you're citing a line — the examiner may be following along in
  the source.
