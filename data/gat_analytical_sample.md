# GAT General Analytical Reasoning Prep Guide

## Linear Sequencing Puzzles

### Core Methodology
Linear sequencing involves ordering entities (people, tasks, presentations, cars) in a straight line from 1 to $N$ (or Monday to Sunday).

1. **Step 1: Define Entities and Positions:** Note the exact number of slots $1, 2, \dots, N$.
2. **Step 2: Symbolize Initial Rules:**
   - "A is immediately before B": $[A][B]$ (a fused block).
   - "A is before B (not necessarily immediately)": $A < B$.
   - "Exactly two entities between A and B": $A \_ \_ B$ or $B \_ \_ A$.
   - "A cannot be in slot 1": $A \neq 1$.
3. **Step 3: Combine Clues into Super-Blocks:** Look for shared variables across rules to establish anchor positions.

### Common GAT Traps
- **Trap 1 (Assuming Immediate Precedence):** Confusing "X arrives before Y" ($X < Y$) with "X arrives immediately before Y" ($[X][Y]$).
- **Trap 2 (Direction Confusion):** Reversing "ahead of" or "behind". Always establish a left-to-right convention (e.g., 1 = earliest, 5 = latest).
- **Trap 3 (Neglecting Symmetric Constraints):** When given "two persons between M and N", students often only test $M$ first and forget $N$ can also come first.

---

## Grouping and Selection Problems

### Core Methodology
Grouping involves selecting a subset of candidates from a larger pool or partitioning them into two or more distinct committees or teams under compatibility rules.

### Typical Rule Patterns:
1. **Conditional Inclusion ($P \implies Q$):** "If Ali is selected, then Bilal must be selected."
   - **Valid Contrapositive:** If Bilal is NOT selected, Ali CANNOT be selected ($\neg Q \implies \neg P$).
   - **Invalid Fallacy:** If Bilal is selected, Ali must be selected (False converse).
2. **Mutual Exclusion ($P \implies \neg Q$):** "Ali and Bilal cannot both be on the team." (At most one can be chosen, or neither).
3. **Co-requisite ($P \iff Q$):** "Ali is selected if and only if Bilal is selected." (Either both are on the team, or neither is).

### Common GAT Traps
- **Trap 1 (The Converse Error):** Assuming that if Bilal is selected, Ali must also be selected.
- **Trap 2 (Mutual Exclusion Misunderstanding):** Assuming that because Ali and Bilal cannot both be selected, one of them *must* be selected. In reality, both could be left out!

---

## Sample Analytical Scenario: University Department Presentations

### Premise
Six professors—Farooq, Ghazala, Hamid, Imran, Junaid, and Khalid—are scheduled to deliver lectures on six consecutive days from Monday through Saturday:
- Day 1: Monday, Day 2: Tuesday, Day 3: Wednesday, Day 4: Thursday, Day 5: Friday, Day 6: Saturday.

### Conditions:
1. Imran must present on Wednesday (Day 3).
2. Farooq must present earlier in the week than Ghazala ($F < G$).
3. Khalid must present on the day immediately after Hamid ($[H][K]$).
4. Neither Farooq nor Khalid can present on Saturday (Day 6).

### Deductions:
- Since Imran is on Wednesday (3), the consecutive block $[H][K]$ must fit either on (Monday, Tuesday) or (Thursday, Friday). It cannot be on (Friday, Saturday) because Khalid cannot present on Saturday.
- If $[H][K]$ is on (Thursday, Friday), then Farooq and Ghazala must be on Monday and Tuesday respectively (since $F < G$), leaving Junaid for Saturday.
