from app.observability.pii import mask_email


def test_mask_email_keeps_domain() -> None:
    assert mask_email("alice@example.com") == "a***@example.com"


def test_mask_email_blank() -> None:
    assert mask_email("  ") is None
    assert mask_email(None) is None


def test_mask_email_malformed() -> None:
    assert mask_email("not-an-email") == "***"


def test_mask_never_contains_full_local_part() -> None:
    masked = mask_email("guest.full.name@hotel.example")
    assert masked is not None
    assert "guest.full.name" not in masked
    assert masked.endswith("@hotel.example")
