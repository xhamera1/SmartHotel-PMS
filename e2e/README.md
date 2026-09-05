# e2e

Playwright end-to-end suite (TypeScript) running against the dockerized stack
(`app + stubs` compose profiles — external APIs always stubbed). The scenario
catalog (E2E-01…E2E-11) includes fault injection: the pricing service is killed
mid-flow and bookings must still complete at base rates.
