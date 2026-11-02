"""Local password generation and conservative strength heuristics."""
import secrets
import string

ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*_-+="


def generate_password(length: int = 24) -> str:
    if not 12 <= length <= 256:
        raise ValueError("Password length must be between 12 and 256")
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def analyze_password(password: str) -> tuple[str, list[str]]:
    if not password:
        return "WEAK", ["Password is empty"]
    advice = []
    if len(password) < 15:
        advice.append("Prefer 15+ characters for a memorable password or passphrase")
    if len(set(password)) <= max(2, len(password) // 4):
        advice.append("Too many repeated characters")
    if password.lower() in {"password", "password123", "12345678", "qwerty123"}:
        advice.append("This is a commonly used password")
    if not advice:
        return "REASONABLE", ["Heuristic only: use unique passwords and a password manager"]
    return "WEAK", advice
