## Context

`send_teilnahmebestaetigung_email` in `core/services/email.py` constructs a Scaleway transactional email API call directly (not via the `send_email` helper) because it includes a PDF attachment. Currently the `"to"` field contains only the participant's address. The order confirmation email (`send_order_confirmation_email`) already sends to both participant and `bildungsplattform@rauchfangkehrer.or.at` via the `send_email` helper.

## Goals / Non-Goals

**Goals:**
- Send every Teilnahmebestätigung email (including PDF attachment) to `bildungsplattform@rauchfangkehrer.or.at` in addition to the participant
- Keep parity with the order confirmation pattern

**Non-Goals:**
- Refactoring the direct API call into the `send_email` helper (attachment support would require changes to the helper)
- Making the CC address configurable via settings
- Changing any other email functions

## Decisions

**Send as a separate API call rather than adding a second `"to"` entry**

The Scaleway transactional email API accepts multiple `"to"` recipients, but sending a second discrete API call (looping over a recipient list) is more robust: if the platform address bounces or errors, the participant still receives their certificate. This matches how `send_email` already works — it loops over `to_emails` with one API call per address.

Implementation: build the recipient list as `[email_address, "bildungsplattform@rauchfangkehrer.or.at"]` and loop the existing API call over both, identical to the `send_email` pattern.

## Risks / Trade-offs

- **Doubled API calls** → Marginal impact; certificates are sent infrequently and one extra call per certificate is negligible.
- **Duplicate PDF generation** → None; the same `pdf_base64` payload is reused for both recipients.
