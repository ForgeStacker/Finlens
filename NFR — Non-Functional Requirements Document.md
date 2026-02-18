# NFR - Non-Functional Requirements Document

- **Project Name:** FinLens
- **Document Type:** Non-Functional Requirements (NFR)
- **Audience:** Product Owner; Engineering; QA / Validation; Security & Compliance Reviewers
- **Document Nature:** Living, controlled
- **Stability:** High (changes rarely, only with strong justification)

## 1. Purpose of This Document
This document defines HOW WELL FinLens must behave, independent of features.

**It specifies:**

- Quality attributes
- Constraints
- Operational expectations
- System characteristics that are not optional

A system can meet all functional requirements and still fail if it violates NFRs.

## 2. NFR Scope
**These requirements apply to:**

- Backend scanning engine
- Data processing pipeline
- Report generation
- Frontend UI
- Overall system behavior

They are global constraints.

## 3. Performance Requirements

### NFR-P1: Scan Performance

**Requirement:** The system shall complete scans within reasonable time for small-to-medium AWS accounts.

**Expectations:**

- No intentional blocking or artificial delays
- Service scans executed independently
- Performance degrades linearly with account size

**Rationale:** Users expect feedback, not overnight jobs.

### NFR-P2: UI Responsiveness

**Requirement:** The UI shall remain responsive after report load.

**Expectations:**

- All interactions are client-side
- Sorting and filtering occur instantly for typical datasets
- No loading spinners after initial load

## 4. Reliability & Fault Tolerance

### NFR-R1: Partial Failure Tolerance

**Requirement:** Failure in one service, region, or account shall not terminate the entire scan.

**Expectations:**

- Errors are isolated
- Scan continues wherever possible
- Failures are clearly reported

### NFR-R2: Deterministic Output

**Requirement:** Given identical inputs, the system shall produce identical outputs.

**Expectations:**

- No randomness
- No time-dependent behavior (except metadata timestamps)
- Stable ordering where applicable

## 5. Availability & Offline Operation

### NFR-A1: Offline Report Usability

**Requirement:** Generated reports shall be fully usable without internet access.

**Expectations:**

- No external CDN usage
- No remote API calls
- All assets bundled locally

### NFR-A2: Post-Scan Independence

**Requirement:** No cloud access shall be required after scan completion.

**Expectations:**

- UI never attempts cloud calls
- Data is frozen at scan time

## 6. Portability & Compatibility

### NFR-C1: Cross-Platform Support

**Requirement:** The system shall run on:

- Linux
- macOS
- Windows

**Expectations:**

- No OS-specific hard dependencies
- File paths handled portably

### NFR-C2: Browser Compatibility

**Requirement:** The UI shall work on modern browsers.

**Expectations:**

- Chrome, Firefox, Edge
- No proprietary browser features

## 7. Security Requirements

### NFR-S1: Credential Handling

**Requirement:** The system shall never store cloud credentials.

**Expectations:**

- Uses local credential providers only
- No credential persistence
- No credential logging

### NFR-S2: Data Privacy

**Requirement:** All collected data shall remain local to the user.

**Expectations:**

- No telemetry
- No data exfiltration
- No hidden network calls

### NFR-S3: Least Privilege Expectation

**Requirement:** The system shall operate with read-only permissions where possible.

**Expectations:**

- No resource mutation
- No write actions to cloud

## 8. Maintainability & Evolvability

### NFR-M1: Service Isolation

**Requirement:** Each cloud service integration shall be isolated.

**Expectations:**

- Clear boundaries per service
- Failure or change in one service does not affect others

### NFR-M2: Backward Compatibility

**Requirement:** New versions of FinLens should not break older reports.

**Expectations:**

- Older JSON schemas remain readable
- UI supports previous versions where feasible

## 9. Usability & UX Quality

### NFR-U1: Non-Technical First

**Requirement:** The system shall prioritize non-technical users by default.

**Expectations:**

- Human-readable language
- Avoidance of cloud jargon
- Progressive disclosure of complexity

### NFR-U2: Cognitive Load Control

**Requirement:** The UI shall avoid overwhelming the user.

**Expectations:**

- Limited default views
- Clear visual hierarchy
- Optional advanced details

## 10. Observability & Transparency

### NFR-O1: Explainability

**Requirement:** All derived insights must be explainable.

**Expectations:**

- No "magic numbers"
- Clear reasoning for optimization hints
- Traceability to underlying data

### NFR-O2: Logging

**Requirement:** The system shall log meaningful operational information.

**Expectations:**

- Errors logged clearly
- Logs usable for troubleshooting
- No sensitive data in logs

## 11. Scalability Constraints

### NFR-SC1: Reasonable Scale Support

**Requirement:** The system shall handle growth gracefully.

**Expectations:**

- Supports increasing resource counts
- No exponential degradation
- UI remains usable with large datasets

## 12. Compliance & Auditability

### NFR-CA1: Audit Readiness

**Requirement:** Reports shall be auditable artifacts.

**Expectations:**

- Immutable after generation
- Timestamped
- Versioned

## 13. Non-Functional Trade-Offs (Explicit)
**The following trade-offs are accepted:**

| Trade-Off | Decision |
| --- | --- |
| Performance vs clarity | Clarity wins |
| Features vs simplicity | Simplicity wins |
| Automation vs trust | Trust wins |

## 14. Acceptance Criteria
**This NFR is satisfied when:**

- Reports work fully offline
- Partial failures do not crash scans
- Non-technical users are not overwhelmed
- No credentials or data leak outside the system

## 15. Change Control
**Any change affecting:**

- Security
- Offline behavior
- Determinism
- Backward compatibility

Requires explicit review and approval.
