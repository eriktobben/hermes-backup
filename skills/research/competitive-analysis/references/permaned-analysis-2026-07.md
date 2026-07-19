# permaNED Competitive Analysis (July 2026)

## Competitor Snapshot

- **Company:** Permåned (LeaseCloud AS), part of 3stepIT Group (Swedish parent)
- **URL:** https://www.permaned.no
- **Trustpilot:** 4.8/5.0
- **Customers:** 3000+ business customers, 100 new companies/month
- **Employees:** 11-50

## Value Proposition
"Skaff teknologi på en smartere måte" — lease hardware for a monthly fee instead of buying outright.

## How It Works
1. Choose equipment from catalog
2. Select monthly price tier (24 or 36 month agreement)
3. Credit check (doesn't affect credit score) via DNB/Bisnode
4. Digital signing with bank-ID
5. Delivery 1-2 business days
6. At end: upgrade, return, or buy for 8-12% of value

## Products
- Computers: MacBook, Lenovo, Dell, HP
- Phones: iPhone, Android (Samsung, Google)
- Audio/TV: Bose, Sony, Sonos
- Cameras: Canon, Nikon, Sony, Fujifilm, DJI, Blackmagic
- Office: Speakers, TVs, conference equipment, coffee machines, printers, 3D printers, furniture

## Target Audience
- Self-employed and companies with 2-50 employees
- Specifically: agencies, consultancies, startups, scale-ups
- Industries: media, advertising, PR, architecture, IT, communications, HR

## Strengths
1. **Strong brand** — 4.8/5 Trustpilot, 3000+ customers
2. **Wide product range** — 3000+ products across many categories
3. **Digital-first process** — bank-ID signing, fast delivery
4. **No credit score impact** — soft credit check only
5. **Flexible end-state** — upgrade, return, or buy at 8-12%
6. **International backing** — 3stepIT Group provides scale
7. **Sustainability angle** — reuse/upcycle messaging

## Weaknesses / Gaps
1. **Swedish company** — not native Norwegian, customer service hours limited (10-15)
2. **No team management** — sells per-device, no admin dashboard for teams
3. **No integrations** — no Visma/Fiken/Uni Economy, no MDM, no HR systems
4. **Manual custom orders** — "kontakt oss" for products outside catalog
5. **No bundle/packaging** — no pre-configured team packages
6. **No transparent pricing calculator** — calculator exists but is generic
7. **Limited self-serve** — still requires some human interaction for setup
8. **No device lifecycle management** — no dashboard showing all devices, costs, status
9. **Customer service hours** — man-fre 10:00-15:00 (limited)

## Differentiation Opportunities (ranked)

### High Impact, High Feasibility
1. **Team-first admin dashboard** — see all devices, costs, status per employee
2. **Norwegian integrations** — Visma/Fiken auto-bokføring
3. **100% self-serve checkout** — no human interaction needed
4. **Transparent TCO calculator** — compare leasing vs. buying with real numbers

### High Impact, Medium Feasibility
5. **Industry-specific packages** — "Pakke for konsulenter", "Pakke for designere"
6. **Automatic upgrade suggestions** — proactive outreach when new models launch
7. **Technical support included** — 30 min/mnd per employee

### Medium Impact, High Feasibility
8. **Norwegian-first branding** — local kundeservice, norsk support
9. **API for HR integration** — auto-order when new hire starts
10. **Restverdi-synlighet** — show real-time equipment value

## Technical Notes
- Product prices are rendered client-side (not in initial HTML) — use browser tools for pricing
- Site uses WooCommerce-like structure with product categories
- JSON-LD structured data available for company info
- Heavy navigation menus truncate browser snapshots — use curl + Python extraction for page content
