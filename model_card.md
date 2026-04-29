# Model Card: PawPal AI Pet-Care Scheduling Agent

## Intended Use

PawPal AI is intended to help pet owners convert everyday care requests into organized schedules. It is useful for planning feeding, walking, litter cleaning, grooming, playtime, medication reminders, and other routine care tasks.

## Not Intended For

This system is not intended for veterinary diagnosis, medication dosage, emergency triage, treatment planning, or professional medical decision-making. If a pet may be sick, injured, poisoned, or in distress, the user should contact a licensed veterinarian or emergency veterinary clinic.

## AI Components

- **RAG retriever:** Searches local markdown files in `knowledge/` for relevant pet-care context.
- **Gemini parser:** Uses Gemini structured output to convert natural language into task JSON when `GEMINI_API_KEY` is configured.
- **Deterministic fallback parser:** Provides reproducible keyword-based parsing without external API access.
- **Guardrails:** Validate structured plans and warn on medical or emergency language.
- **Scheduler:** The final schedule is produced by deterministic PawPal logic, not by the language model.

## Data Sources

The retrieval system uses local project files:

- `knowledge/dog_care.md`
- `knowledge/cat_care.md`
- `knowledge/medication_safety.md`

These files are small educational references and should be reviewed before production use.

## Reliability And Guardrails

Reliability measures include:

- Unit tests with `pytest`
- `eval_cases.py` end-to-end evaluation cases
- Structured JSON validation before scheduling
- Fallback parsing when Gemini is unavailable
- Medical and emergency warnings
- JSONL logging for agent runs

The system checks both raw user input and parsed JSON, which reduces the chance that safety-sensitive words are lost during parsing.

## Limitations And Bias

The fallback parser relies on fixed keywords, so it can miss slang, misspellings, or unusual phrasing. The local knowledge base is limited and may not reflect every species, breed, age, disability, or medical condition. If Gemini is enabled, outputs may vary and can reflect limitations in the model or prompt.

## Misuse Risks

Users could misuse the app as a substitute for veterinary advice. To reduce this risk, the app displays disclaimers for medication and emergency terms and does not generate dosage, diagnosis, or treatment instructions.

## Testing Results

Current validation includes unit tests for the scheduler, retriever, guardrails, AI agent fallback, scheduler adapter, and logger. The evaluation harness checks five representative scenarios and prints a pass/fail summary.

## AI Collaboration Reflection

AI assistance was useful for breaking the final project requirements into concrete engineering steps: RAG, parser, guardrails, scheduler adapter, logging, evaluation, and documentation. A helpful suggestion was to keep Gemini parsing separate from deterministic scheduling, because that makes the system easier to test and explain.

One flawed suggestion was to rely only on the structured plan for medical and emergency warnings. Testing showed that fallback parsing could remove emergency words from the structured task name, so the guardrails were updated to inspect the raw user input as well.
