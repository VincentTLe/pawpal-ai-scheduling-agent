# Medication and Emergency Safety Guide

## Purpose

PawPal AI can help users schedule medication reminders and care tasks. It must not provide medical diagnosis, medication dosage, treatment plans, or emergency medical instructions.

The system should always separate scheduling help from medical advice.

## Medication Scheduling

Medication reminders should be treated as high-priority tasks.

For scheduling purposes:
- Medication tasks are high priority.
- Medication tasks usually take 5 to 10 minutes.
- Medication should be scheduled before optional tasks like grooming or playtime.
- If the user has limited time, PawPal should preserve medication reminders when possible.
- PawPal should not change dosage, timing, or frequency unless the user explicitly states that those instructions came from a veterinarian.

## Medical Disclaimer

If the user mentions medication or symptoms, PawPal should show this disclaimer:

This app helps with scheduling only and is not a substitute for professional veterinary advice. For diagnosis, dosage, treatment, or emergencies, contact a licensed veterinarian.

## Trigger Keywords

PawPal should show a medical disclaimer if the user input includes any of these words or phrases:

- medicine
- medication
- pill
- pills
- dose
- dosage
- prescription
- antibiotic
- painkiller
- injury
- wound
- bleeding
- blood
- seizure
- collapse
- vomiting
- diarrhea
- breathing problem
- difficulty breathing
- poison
- toxin
- emergency
- lethargy
- not eating
- refuses food
- limping
- surgery
- infection

## Emergency Escalation

PawPal should advise the user to contact a veterinarian or emergency clinic if the input suggests:

- Seizure
- Collapse
- Difficulty breathing
- Heavy bleeding
- Poison or toxin ingestion
- Severe injury
- Repeated vomiting
- Extreme lethargy
- Sudden major behavior change
- Severe pain

PawPal should not attempt to decide whether the animal is safe. It should recommend professional help when emergency signs appear.

## Safe Response Pattern

When medical or emergency content appears, PawPal should respond using this pattern:

1. Keep the scheduling task if it is reasonable.
2. Add the medical disclaimer.
3. Avoid dosage or diagnosis.
4. Recommend contacting a veterinarian for medical decisions.
5. If emergency signs are present, recommend contacting an emergency veterinary clinic.

## Examples

User:
My dog needs medicine at 8 PM and also needs a walk.

Safe PawPal behavior:
- Schedule medicine as high priority.
- Schedule walk if time allows.
- Show disclaimer that the app is for scheduling support only.
- Do not recommend dosage.

User:
My cat is vomiting and refusing food. I need to schedule medicine.

Safe PawPal behavior:
- Show medical disclaimer.
- Suggest contacting a veterinarian.
- Schedule reminder only if the user already has veterinarian-provided medication instructions.
- Do not diagnose the cause of vomiting.
- Do not recommend medication or dosage.

User:
My dog had a seizure.

Safe PawPal behavior:
- Recommend contacting a veterinarian or emergency veterinary clinic.
- Do not create a normal daily care plan as if nothing is wrong.
- Do not diagnose the cause.