"""Phase 10 shared log field contract (mirrors pms-core LogSchemaFieldsTest)."""

REQUIRED_TOP_LEVEL = {"@timestamp", "level", "service", "traceId", "message"}
HTTP_FIELDS = {"http.method", "http.path", "http.status", "durationMs"}
BUSINESS_EVENTS = {
    "PricingDecisionMade",
    "ReservationCreated",
    "ReservationCancelled",
    "GeminiCallCompleted",
}


def test_required_top_level_documented() -> None:
    assert "traceId" in REQUIRED_TOP_LEVEL
    assert "service" in REQUIRED_TOP_LEVEL


def test_http_fields_documented() -> None:
    assert "durationMs" in HTTP_FIELDS


def test_business_events_match_plan() -> None:
    assert "GeminiCallCompleted" in BUSINESS_EVENTS
    assert "PricingDecisionMade" in BUSINESS_EVENTS
