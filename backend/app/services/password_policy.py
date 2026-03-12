from __future__ import annotations


def validate_password_strength(password: str, email: str) -> str | None:
    if len(password) < 12:
        return "Password must be at least 12 characters long."
    if not any(character.islower() for character in password):
        return "Password must include a lowercase letter."
    if not any(character.isupper() for character in password):
        return "Password must include an uppercase letter."
    if not any(character.isdigit() for character in password):
        return "Password must include a number."
    if not any(not character.isalnum() for character in password):
        return "Password must include a symbol."

    normalized_password = password.lower()
    local_part = email.split("@", 1)[0].strip().lower()
    if len(local_part) >= 3 and local_part in normalized_password:
        return "Password must not contain your email name."

    weak_patterns = ("password", "qwerty", "123456", "admin", "solanatrust")
    if any(pattern in normalized_password for pattern in weak_patterns):
        return "Password is too predictable. Choose a less common phrase."

    return None
