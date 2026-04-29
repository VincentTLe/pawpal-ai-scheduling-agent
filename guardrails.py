VALID_PRIORITIES = {"high", "medium", "low"}
VALID_TIMES_OF_DAY = {"morning", "afternoon", "evening", "anytime"}
VALID_RECURRENCES = {"once", "daily", "weekly", "monthly"}

MEDICAL_KEYWORDS = {
    "medicine",
    "medication",
    "pill",
    "pills",
    "dose",
    "dosage",
    "prescription",
    "antibiotic",
    "painkiller",
    "injury",
    "wound",
    "bleeding",
    "blood",
    "seizure",
    "collapse",
    "vomiting",
    "diarrhea",
    "breathing",
    "poison",
    "toxin",
    "emergency",
    "lethargy",
    "not eating",
    "refuses food",
    "limping",
    "surgery",
    "infection",
}

EMERGENCY_KEYWORDS = {
    "seizure",
    "collapse",
    "difficulty breathing",
    "breathing problem",
    "heavy bleeding",
    "poison",
    "toxin",
    "emergency",
    "severe injury",
    "blood",
}


MEDICAL_DISCLAIMER = (
    "This app helps with scheduling only and is not a substitute for "
    "professional veterinary advice. For diagnosis, dosage, treatment, "
    "or emergencies, contact a licensed veterinarian."
)

EMERGENCY_WARNING = (
    "The request may describe an emergency or serious medical issue. "
    "Contact a veterinarian or emergency veterinary clinic as soon as possible."
)


def contains_keyword(text: str, keywords: set[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def detect_medical_content(text: str) -> bool:
    return contains_keyword(text, MEDICAL_KEYWORDS)


def detect_emergency_content(text: str) -> bool:
    return contains_keyword(text, EMERGENCY_KEYWORDS)


def validate_task(task: dict) -> list[str]:
    errors = []

    name = task.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("Task name is required.")

    duration = task.get("duration")
    if not isinstance(duration, int) or duration <= 0:
        errors.append("Task duration must be a positive integer.")

    priority = task.get("priority")
    if priority not in VALID_PRIORITIES:
        errors.append("Task priority must be high, medium, or low.")

    time_of_day = task.get("time_of_day", "anytime")
    if time_of_day not in VALID_TIMES_OF_DAY:
        errors.append("Task time_of_day must be morning, afternoon, evening, or anytime.")

    recurrence = task.get("recurrence", "once")
    if recurrence not in VALID_RECURRENCES:
        errors.append("Task recurrence must be once, daily, weekly, or monthly.")

    return errors


def validate_pet(pet: dict) -> list[str]:
    errors = []

    name = pet.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("Pet name is required.")

    pet_type = pet.get("type")
    if not isinstance(pet_type, str) or not pet_type.strip():
        errors.append("Pet type is required.")

    tasks = pet.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("Each pet must have at least one task.")
        return errors

    for task in tasks:
        if not isinstance(task, dict):
            errors.append("Each task must be a dictionary.")
            continue

        errors.extend(validate_task(task))

    return errors


def validate_plan_input(plan: dict) -> tuple[bool, list[str], list[str]]:
    """
    Validate the structured plan that comes from the AI parser.

    Returns:
        is_valid: True if no errors were found
        errors: blocking issues that should stop scheduling
        warnings: non-blocking safety warnings shown to the user
    """
    errors = []
    warnings = []

    if not isinstance(plan, dict):
        return False, ["Plan must be a dictionary."], warnings

    available_minutes = plan.get("available_minutes")
    if not isinstance(available_minutes, int) or available_minutes <= 0:
        errors.append("Available minutes must be a positive integer.")

    pets = plan.get("pets")
    if not isinstance(pets, list) or not pets:
        errors.append("At least one pet is required.")
        return False, errors, warnings

    all_text = []

    for pet in pets:
        if not isinstance(pet, dict):
            errors.append("Each pet must be a dictionary.")
            continue

        errors.extend(validate_pet(pet))

        all_text.append(str(pet.get("name", "")))
        all_text.append(str(pet.get("type", "")))

        for task in pet.get("tasks", []):
            if isinstance(task, dict):
                all_text.append(str(task.get("name", "")))

    combined_text = " ".join(all_text)

    if detect_medical_content(combined_text):
        warnings.append(MEDICAL_DISCLAIMER)

    if detect_emergency_content(combined_text):
        warnings.append(EMERGENCY_WARNING)

    return len(errors) == 0, errors, warnings
