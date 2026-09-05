-- =============================================================================
-- V2__seed_reference_data.sql — development/test seeds (NEVER applied in prod)
--
-- Lives in db/seed, not db/migration: the Spring profiles will configure
--   dev/test:  spring.flyway.locations = classpath:db/migration, classpath:db/seed
--   prod:      spring.flyway.locations = classpath:db/migration
-- Version numbers are shared across locations — the next SCHEMA migration in
-- db/migration must therefore be V3 or higher. Flyway tolerates the V2 gap in
-- prod (versions must only increase).
--
-- Room-type catalog mirrors the synthetic data generator configuration
-- (STD / DLX / SUI) so dev, tests, and the ML dataset speak the same language.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Rate plans (ADR-0007): price = BAR × price_modifier
-- ---------------------------------------------------------------------------
INSERT INTO pms.rate_plans (code, name, description, refundable, breakfast_included, price_modifier, sort_order) VALUES
  ('FLEX',   'Flexible',        'Free cancellation until the check-in date.',                     TRUE,  FALSE, 1.0000, 10),
  ('NONREF', 'Non-refundable',  'Best price — payment is final, no cancellation.',                FALSE, FALSE, 0.9000, 20),
  ('BB',     'Bed & Breakfast', 'Flexible rate with breakfast for every guest included.',         TRUE,  TRUE,  1.1500, 30);

-- ---------------------------------------------------------------------------
-- Room types (codes, prices and counts match the datagen config, Appendix C)
-- ---------------------------------------------------------------------------
INSERT INTO pms.room_types (code, name, description, capacity, base_price, min_price, max_price, amenities) VALUES
  ('STD', 'Standard Double', 'Cozy double room with a queen bed and city view.', 2, 250.00, 180.00, 450.00,
   '["wifi", "tv", "kettle"]'::jsonb),
  ('DLX', 'Deluxe Double',   'Spacious room with a king bed, workspace and minibar.', 3, 420.00, 300.00, 800.00,
   '["wifi", "tv", "minibar", "air_conditioning", "workspace"]'::jsonb),
  ('SUI', 'Junior Suite',    'Separate living area, panoramic view, premium amenities.', 4, 700.00, 500.00, 1400.00,
   '["wifi", "tv", "minibar", "air_conditioning", "living_area", "bathtub", "coffee_machine"]'::jsonb);

-- ---------------------------------------------------------------------------
-- Rooms: 20× STD (floors 1–2), 10× DLX (floor 3), 5× SUI (floor 4) = 35 rooms
-- ---------------------------------------------------------------------------
INSERT INTO pms.rooms (room_number, room_type_id, floor)
SELECT (100 + n)::text, (SELECT id FROM pms.room_types WHERE code = 'STD'), 1
FROM generate_series(1, 10) AS n;

INSERT INTO pms.rooms (room_number, room_type_id, floor)
SELECT (200 + n)::text, (SELECT id FROM pms.room_types WHERE code = 'STD'), 2
FROM generate_series(1, 10) AS n;

INSERT INTO pms.rooms (room_number, room_type_id, floor)
SELECT (300 + n)::text, (SELECT id FROM pms.room_types WHERE code = 'DLX'), 3
FROM generate_series(1, 10) AS n;

INSERT INTO pms.rooms (room_number, room_type_id, floor)
SELECT (400 + n)::text, (SELECT id FROM pms.room_types WHERE code = 'SUI'), 4
FROM generate_series(1, 5) AS n;

-- ---------------------------------------------------------------------------
-- Staff users — DEV-ONLY credentials (BCrypt, cost 10):
--   admin@smarthotel.local      / admin-dev-password      (ADMIN)
--   reception@smarthotel.local  / reception-dev-password  (RECEPTIONIST)
-- ---------------------------------------------------------------------------
INSERT INTO pms.staff_users (email, password_hash, full_name, role) VALUES
  ('admin@smarthotel.local',
   '$2a$10$TfbhRyhxmwC2Ewza15IhweiQl4OVlUDGAyaFlSzrXgB8dR1Eb/RGa',
   'Dev Admin', 'ADMIN'),
  ('reception@smarthotel.local',
   '$2a$10$sQa6MvMYPhaMAz.J3Ntdu.ohNqDi9DyBGSlWukH.9f//w6qflZ7tq',
   'Dev Receptionist', 'RECEPTIONIST');
