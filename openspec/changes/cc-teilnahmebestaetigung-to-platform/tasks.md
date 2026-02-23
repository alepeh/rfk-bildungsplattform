## 1. Implementation

- [x] 1.1 Refactor `send_teilnahmebestaetigung_email` in `core/services/email.py` to loop over a recipient list (`[email_address, "bildungsplattform@rauchfangkehrer.or.at"]`) instead of sending to a single address, making one API call per recipient with identical payload (subject, HTML, PDF attachment)

## 2. Testing

- [x] 2.1 Add unit test: Teilnahmebestätigung sends to both participant and platform email address
- [x] 2.2 Add unit test: each recipient gets a separate API call (independent delivery)
- [x] 2.3 Add unit test: platform copy has identical subject, HTML body, and PDF attachment
