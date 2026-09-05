-- ============================================================================
-- SmartHotel-PMS — infrastructure smoke checks (run via `task smoke`).
-- Assertion idiom: 1 / (condition)::int → division-by-zero error when the
-- condition is false; with ON_ERROR_STOP psql then exits non-zero.
-- ============================================================================

SELECT 1 / (count(*) = 2)::int AS schemas_present
  FROM information_schema.schemata
 WHERE schema_name IN ('pms', 'pricing');

SELECT 1 / (count(*) = 2)::int AS service_users_present
  FROM pg_roles
 WHERE rolname IN ('pms_user', 'pricing_user');

SELECT 1 / (count(*) = 1)::int AS btree_gist_present
  FROM pg_extension
 WHERE extname = 'btree_gist';

\echo All smoke checks passed.
