## ADDED Requirements

### Requirement: Teilnahmebestätigung is sent to platform email
The system SHALL send every Teilnahmebestätigung email (including the PDF attachment) to `bildungsplattform@rauchfangkehrer.or.at` in addition to the participant's email address.

#### Scenario: Teilnahmebestätigung sent to both participant and platform
- **WHEN** a Teilnahmebestätigung is triggered for a participant
- **THEN** the system sends the email with PDF attachment to the participant's email address AND to `bildungsplattform@rauchfangkehrer.or.at`

#### Scenario: Participant delivery is independent of platform delivery
- **WHEN** the API call to deliver the Teilnahmebestätigung to one recipient fails
- **THEN** the other recipient's delivery SHALL still be attempted (each recipient gets a separate API call)

#### Scenario: Platform copy is identical to participant copy
- **WHEN** the platform email address receives a Teilnahmebestätigung
- **THEN** the email content (subject, HTML body, PDF attachment) SHALL be identical to the participant's copy
