# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

The system is designed around three core actions a user needs to perform:

1. **Add a pet to the system.** The user enters basic information about themselves and their pet (such as the pet's name, species, and any relevant health notes). This gives the app the context it needs to personalize care recommendations and store tasks associated with that specific pet.

2. **Add and manage care tasks.** The user can create individual care tasks — such as a morning walk, medication, feeding, or grooming — and assign each task a duration (in minutes) and a priority level. This lets the system understand what needs to happen and how urgently, so it can make sensible scheduling decisions even when time is limited.

3. **Generate and view a daily care plan.** The user requests a daily schedule, and the app produces an ordered plan of tasks based on the available time and each task's priority. The plan is displayed clearly, with an explanation of why tasks were included or excluded, so the owner understands the reasoning and can trust the schedule.

- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
