"""PII masking for structured logs (shared contract with pms-core)."""


def mask_email(email: str | None) -> str | None:
    """Mask as ``a***@domain``; blank → ``None``; malformed → ``***``."""
    if email is None:
        return None
    trimmed = email.strip()
    if not trimmed:
        return None
    at = trimmed.find("@")
    if at <= 0 or at == len(trimmed) - 1:
        return "***"
    return f"{trimmed[0]}***{trimmed[at:]}"
