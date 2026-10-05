# User Feedback — Low/Mid-Fidelity Prototype Testing

> **Testing period:** September 2026  
> **Prototype scope:** Bites list, Bite detail + quiz flow, Dashboard (recommendations + streaks), Pricing/Checkout page  
> **Session format:** 30-minute moderated think-aloud + 5-question post-session survey (SUS-lite scale 1–5)

---

## Tester 1 — Priya R. (CS Undergraduate, Year 3)

**Background:** Uses YouTube + freeCodeCamp for self-study. Comfortable with Python; new to JavaScript.  
**Session date:** 2026-09-08

### Observations

| Area | Observation | Severity |
|---|---|---|
| Bites list | Immediately understood the difficulty filter; picked "beginner" without prompting. | — (positive) |
| Bite detail | Paused at the code snippet — expected a "Run" button. Felt completion felt incomplete without executing code. | 🔴 High |
| Quiz flow | Appreciated the immediate explanation after each wrong answer. "This is what YouTube is missing." | — (positive) |
| Dashboard | Streak counter visible and motivating. Did not notice the XP bar until pointed out. | 🟡 Medium |
| Pricing | Confused by "Pro" vs "Premium" label inconsistency in two different screens. | 🟡 Medium |

### Post-Session Survey (1 = Strongly Disagree, 5 = Strongly Agree)

| Question | Score |
|---|---|
| The learning flow felt natural and easy to follow | 4 |
| I understood what XP and levels represent | 3 |
| I would use this instead of YouTube for quick concepts | 5 |
| The quiz explanations helped me understand my mistakes | 5 |
| I felt motivated to come back tomorrow | 4 |

**Overall SUS-lite score: 4.2 / 5**

### Key Quote
> *"I wish I could just hit Run and see what the code does right there. That would make it perfect."*

### Actions Taken
- ✅ Inline code execution added to bite detail via Piston API (`blueprints/coding.py`)
- ✅ Plan label terminology standardised to "Pro" across all templates

---

## Tester 2 — Karan M. (Working Software Engineer, 3 YOE)

**Background:** Full-stack developer at a startup. Uses LeetCode for interview prep; has a Udemy Pro subscription he rarely opens.  
**Session date:** 2026-09-14

### Observations

| Area | Observation | Severity |
|---|---|---|
| Onboarding | Registered in under 90 seconds; no friction. | — (positive) |
| Bites list | Wanted to filter by language/tag, not just category. E.g. "Show me Python + Intermediate only." | 🟡 Medium |
| Bite detail | Read content quickly, jumped straight to the quiz. Appreciated the "Skip to quiz" UX pattern. | — (positive) |
| Recommendation engine | Dashboard suggestions felt relevant after completing 3 bites. "It's already figured out I like Python." | — (positive) |
| Coding platform | Tried to paste a 40-line solution — editor felt cramped on a 13" laptop. Requested resizable panel. | 🟡 Medium |
| Leaderboard | Immediately checked it. Suggested showing "top 3 friends" separately from global leaderboard. | 🟢 Low |

### Post-Session Survey

| Question | Score |
|---|---|
| The learning flow felt natural and easy to follow | 5 |
| I understood what XP and levels represent | 5 |
| I would use this instead of YouTube for quick concepts | 4 |
| The quiz explanations helped me understand my mistakes | 4 |
| I felt motivated to come back tomorrow | 4 |

**Overall SUS-lite score: 4.4 / 5**

### Key Quote
> *"This is what LeetCode should have built for teaching. Solve a concept, take a quiz, then go to the problem. The sequence actually makes sense."*

### Actions Taken
- 🔲 Multi-tag filter (backlog — `enhancement` label on GitHub)
- 🔲 Resizable code editor panel (backlog — `enhancement` label)
- 🔲 Friend/social leaderboard (backlog — future milestone)

---

## Tester 3 — Dr. Ananya S. (Instructor / Adjunct Lecturer, CS Dept.)

**Background:** Teaches Data Structures and Web Dev. Has used Moodle and Google Classroom in courses. Evaluating tarunsfxo LMS as a supplementary tool for her 60-student Web Dev class.  
**Session date:** 2026-09-21

### Observations

| Area | Observation | Severity |
|---|---|---|
| Admin panel | Found bite creation form clear; wanted bulk CSV import for 50+ bites. | 🟡 Medium |
| Quiz authoring | Only 4-option MCQ supported. Requested true/false and fill-in-the-blank types. | 🟡 Medium |
| Analytics | Category progress chart directly useful for tracking class-wide comprehension gaps. | — (positive) |
| Certificate | Impressed by automated PDF generation. Wants instructor's name/institution on the cert. | 🟡 Medium |
| Gamification | Concerned streak system punishes students who take weekends off. Suggested "forgiveness day" mechanic. | 🟡 Medium |
| Roles & permissions | Asked for a "Instructor" role between Admin and Student that can manage only their own content. | 🔴 High |

### Post-Session Survey

| Question | Score |
|---|---|
| The learning flow felt natural and easy to follow | 4 |
| I understood what XP and levels represent | 4 |
| I would use this instead of YouTube for quick concepts | 3 |
| The quiz explanations helped me understand my mistakes | 5 |
| I felt motivated to come back tomorrow | 3 |

**Overall SUS-lite score: 3.8 / 5**

### Key Quote
> *"The analytics dashboard is genuinely useful — I can see which topic my students are failing the quiz on and adjust my lecture. I'd integrate this alongside Moodle if you add an Instructor role."*

### Actions Taken
- ✅ Certificate now includes configurable institution/instructor field via `config.py: CERT_ISSUER_NAME`
- ✅ "Forgiveness day" streak logic added to `User.update_streak()` (grace period for 1-day gap on weekends)
- 🔲 Instructor role (backlog — next milestone)
- 🔲 Bulk bite CSV import (backlog)
- 🔲 Additional question types (backlog)

---

## Aggregate Summary

| Metric | Value |
|---|---|
| Testers | 3 (1 student, 1 professional developer, 1 instructor) |
| Average SUS-lite score | **4.1 / 5** |
| Critical issues identified | 2 (inline code execution, Instructor role) |
| Medium issues identified | 8 |
| Issues resolved in current build | 4 |
| Issues in backlog | 6 |

### Top 3 Validated Strengths
1. **Quiz + explanation loop** — all three testers independently praised immediate post-answer explanations.
2. **Recommendation engine** — felt relevant after just 3–5 bites; no onboarding questionnaire needed.
3. **Streak / XP motivation** — students and professionals both reported it increased their intent to return.

### Top 3 Validated Pain Points
1. Code snippets without runnable execution (resolved ✅)
2. Lack of Instructor role for class deployments (backlog)
3. XP bar visibility on dashboard (partially resolved — colour contrast improved)
