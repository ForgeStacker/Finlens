# FRD - Functional Requirements Document

- **Project Name:** FinLens
- **Document Type:** Functional Requirements Document (FRD)
- **Audience:** Product Owner; Engineering; QA / Validation; Future Contributors
- **Document Nature:** Living, controlled
- **Traceability:** Must map back to BRD
- **Stability:** Medium-High (changes when behavior changes)

## 1. Purpose of This Document
This document defines WHAT the FinLens system must do in terms of observable behavior.

**It answers:**

- What capabilities the system provides
- How users interact with the system
- How data flows through the system
- What the system must and must not do

**This document does NOT define:**

- How things are implemented
- Which language, framework, or libraries are used
- Internal optimizations
- UI visual design specifics

If something is not defined here, it is not guaranteed behavior.

## 2. System Overview (Functional View)

FinLens is a single-command, offline-first system that:

1. Scans configured cloud accounts
2. Collects and enriches cloud data
3. Produces structured, processed output
4. Generates a self-contained interactive report
5. Enables human decision-making

## 3. System Actors

| Actor | Description |
| --- | --- |
| Operator | Person running finlens scan |
| End User | Person viewing the generated report |
| Cloud Provider | AWS APIs |
| FinLens System | Backend + UI |

## 4. High-Level Functional Flow
1. Operator executes scan command
2. System loads configuration
3. System scans cloud resources
4. System enriches and processes data
5. System generates report artifacts
6. End user views report

## 5. Functional Scope

### 5.1 In Scope

- Configuration-driven scanning
- AWS account data collection
- Cost and usage processing
- Insight enrichment
- Report generation
- Offline UI consumption

### 5.2 Out of Scope

- Live dashboards
- Real-time updates
- Background daemons
- Automated remediation
- Notifications or alerts
- User authentication

## 6. Functional Requirements - Backend
### FR-01: Single Command Execution

**Description:** The system shall support execution via a single command.

**Behavior:**

- Operator executes finlens scan
- No mandatory CLI arguments
- Command triggers full scan lifecycle

**Rationale:** Supports simplicity and non-technical usage (BRD alignment).

### FR-02: Configuration Loading

**Description:** The system shall load execution parameters from configuration files.

**Behavior:**

- Profiles, regions, and services are read from config files
- Missing or invalid config results in clear error messages
- Defaults are applied where defined

**Constraints:**

- No runtime flags override config

### FR-03: Cloud Authentication

**Description:** The system shall authenticate using local cloud credentials.

**Behavior:**

- Uses locally configured AWS profiles
- No credentials stored or persisted
- Failure to authenticate results in graceful failure per profile

### FR-04: Service-Based Scanning

**Description:** The system shall scan cloud resources service-by-service.

**Behavior:**

- Only configured services are scanned
- Each service scan is isolated
- Failure in one service does not abort entire scan

### FR-05: Resource Discovery

**Description:** The system shall discover resources for each service.

**Behavior:**

- Collects resource identifiers and metadata
- Associates resources with region and account
- Ignores unsupported resource types

### FR-06: Cost Data Collection

**Description:** The system shall collect cost data for scanned resources.

**Behavior:**

- Monthly cost attribution
- Currency defined in configuration or defaults
- Missing cost data handled explicitly

### FR-07: Metrics & Usage Collection

**Description:** The system shall collect usage or utilization metrics where applicable.

**Behavior:**

- Metrics collection is best-effort
- Missing metrics do not fail scan
- Metric time window is consistent per scan

### FR-08: Data Enrichment

**Description:** The system shall enrich raw data into meaningful signals.

**Behavior:**

- Calculate utilization indicators
- Derive health or risk flags
- Generate optimization hints

**Constraint:**

- Enrichment logic must be explainable

### FR-09: Data Processing

**Description:** The system shall transform collected and enriched data into structured output.

**Behavior:**

- Data organized by Account  Service  Resource
- Output is deterministic
- Raw data not exposed to UI directly

### FR-10: Processed Output Generation

**Description:** The system shall generate processed JSON output.

**Behavior:**

- JSON represents complete account state
- JSON is human-readable
- JSON is self-sufficient (no external calls needed)

### FR-11: Metadata Generation

**Description:** The system shall generate metadata about the scan.

**Behavior:**

- Includes timestamp, profiles, regions, services
- Includes FinLens version
- Includes currency

### FR-12: Report Packaging

**Description:** The system shall generate a self-contained report directory.

**Behavior:**

- Contains processed data
- Contains metadata
- Contains UI assets
- Directory is portable

### FR-13: Error Handling & Logging

**Description:** The system shall handle failures gracefully.

**Behavior:**

- Logs errors clearly
- Continues scan where possible
- Surfaces partial success

## 7. Functional Requirements - Frontend (UI)
### FR-14: Offline Operation

**Description:** The UI shall operate fully offline.

**Behavior:**

- No network calls
- No backend dependency
- Loads only local assets and JSON

### FR-15: JSON Consumption

**Description:** The UI shall consume processed JSON as its only data source.

**Behavior:**

- No mutation of data
- No enrichment in UI
- UI reflects JSON truth exactly

### FR-16: Overview Presentation

**Description:** The UI shall present a high-level service overview.

**Behavior:**

- Shows limited services initially
- Displays cost, count, and health indicators
- Allows progressive reveal

### FR-17: Service Detail View

**Description:** The UI shall allow detailed inspection of a service.

**Behavior:**

- Tabular resource display
- Default columns shown
- Optional columns user-selectable

### FR-18: Filtering & Sorting

**Description:** The UI shall support data exploration.

**Behavior:**

- Sorting on all visible columns
- Filtering by relevant fields
- No data mutation

### FR-19: Progressive Disclosure

**Description:** The UI shall hide complexity by default.

**Behavior:**

- Simple language by default
- Advanced details optional
- Visual cues over raw numbers

## 8. Functional Constraints

| Constraint | Description |
| --- | --- |
| Deterministic Output | Same input, same output |
| No Runtime Cloud Calls | After scan completion |
| Stateless UI | No persistence |
| Human-Readable Defaults | No jargon by default |

## 9. Traceability to BRD

| BRD Objective | FR Coverage |
| --- | --- |
| Non-tech clarity | FR-16, FR-19 |
| Offline reports | FR-12, FR-14 |
| Decision enablement | FR-08, FR-16 |
| Reduced dependency | FR-01, FR-15 |

## 10. Acceptance Criteria
**This FRD is satisfied when:**

- A complete scan can be run with one command
- A report is generated without cloud access afterward
- A non-technical user can navigate the report
- Engineers can validate data accuracy

## 11. Change Control
**Any change to:**

- User behavior
- Data flow
- Report semantics

**Requires:**

1. Update to this FRD
2. Traceability to BRD
3. Explicit approval
