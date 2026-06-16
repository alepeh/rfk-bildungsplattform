## Why

Teilnahmebestätigungen (participation confirmations with PDF certificate) are currently only sent to the participant. The platform administrators at `bildungsplattform@rauchfangkehrer.or.at` have no record of which certificates were sent. Other transactional emails like the order confirmation (`send_order_confirmation_email`) already CC the platform address — the Teilnahmebestätigung should follow the same pattern for consistency and administrative traceability.

## What Changes

- `send_teilnahmebestaetigung_email` in `core/services/email.py` will also send the Teilnahmebestätigung (including the PDF attachment) to `bildungsplattform@rauchfangkehrer.or.at`
- The platform copy will contain the same content and attachment as the participant email

## Capabilities

### New Capabilities

_(none — this is a small behavioral change to an existing email function)_

### Modified Capabilities

_(no existing specs to modify)_

## Impact

- **Code**: `core/services/email.py` — `send_teilnahmebestaetigung_email` function
- **Behavior**: Each Teilnahmebestätigung will produce two emails instead of one (participant + platform)
- **Email volume**: Marginal increase — one additional email per certificate sent
