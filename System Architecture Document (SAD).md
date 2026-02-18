# System Architecture Document (SAD)

- **Project Name:** FinLens
- **Document Type:** System Architecture Document
- **Audience:** Architects; Senior Engineers; Product Owner; Future Contributors
- **Document Nature:** Living, controlled
- **Stability:** High (changes only when architectural principles change)

## 1. Purpose of This Document
This document defines HOW the FinLens system is structured at a logical and conceptual level.

**It explains:**

- Major system components
- Responsibilities and boundaries
- Data flow between components
- Architectural principles and constraints

**This document does NOT:**

- Select programming languages or frameworks
- Define deployment pipelines
- Describe UI styling
- Specify exact class or file structures

Architecture exists to control complexity and protect product intent.

## 2. Architectural Drivers
The following drivers shape all architectural decisions:

1. Non-technical user clarity
2. Offline-first operation
3. Deterministic, auditable output
4. Headless backend / decoupled frontend
5. Long-lived report usability
6. Future extensibility without refactoring

## 3. Architectural Style

### 3.1 Primary Style

**Headless, Pipeline-Oriented, Offline-First Architecture**

- Backend produces immutable artifacts
- Frontend consumes artifacts only
- No runtime coupling between backend and frontend

### 3.2 Supporting Patterns

| Pattern | Purpose |
| --- | --- |
| Pipeline | Clear stage separation |
| Plugin-like Services | Service isolation |
| Immutable Data | Auditability |
| Config-Driven Execution | Predictability |
| Progressive Disclosure | UX clarity |

## 4. High-Level Architecture Overview

```
Operator
  finlens scan
Scan Orchestrator
Service Collectors
Enrichment Engine
Data Processor
Report Generator
Static UI + JSON
```

## 5. Component Breakdown

### 5.1 Scan Orchestrator

**Responsibility:**

- Entry point for execution
- Coordinates entire scan lifecycle

**Key Characteristics:**

- Stateless
- Configuration-driven
- No cloud logic

**Constraints:**

- Single command execution
- No runtime user interaction

### 5.2 Configuration Manager

**Responsibility:**

- Load and validate configuration files

**Handles:**

- Profiles
- Regions
- Services
- Defaults

**Failure Behavior:**

- Invalid config fails early
- Clear error reporting

### 5.3 Service Collectors

**Responsibility:**

- Communicate with cloud APIs
- Collect raw resource data

**Design Rules:**

- One collector per cloud service
- No cross-service knowledge
- Read-only behavior

**Failure Isolation:**

- Failure affects only that service

### 5.4 Metrics & Cost Collector

**Responsibility:**

- Collect usage and cost data
- Normalize cost representation

**Constraints:**

- Best-effort collection
- Missing data handled explicitly

### 5.5 Enrichment Engine

**Responsibility:**

- Transform raw data into insights

**Examples:**

- Utilization signals
- Health flags
- Optimization hints

**Design Principle:**

- Explainable logic only
- No opaque heuristics

### 5.6 Data Processor

**Responsibility:**

- Structure enriched data into final form

**Key Output:**

- Processed JSON representing account state

**Constraints:**

- Deterministic ordering
- Stable schema

### 5.7 Report Generator

**Responsibility:**

- Package data and UI assets

**Produces:**

- Self-contained report directory
- Metadata file
- Processed data file

**Constraints:**

- Portable
- Immutable after generation

### 5.8 Frontend (Static UI)

**Responsibility:**

- Interpret and present processed data

**Characteristics:**

- No backend dependency
- No cloud calls
- Purely client-side logic

## 6. Data Flow Architecture

### 6.1 Scan-Time Data Flow

`Config -> Collectors -> Enrichment -> Processing -> JSON`

### 6.2 View-Time Data Flow

`JSON -> UI -> Human decisions`

There is no reverse flow.

## 7. Separation of Concerns

| Layer | Responsibility |
| --- | --- |
| Orchestration | Flow control |
| Collection | Raw data |
| Enrichment | Insight generation |
| Processing | Data structure |
| Presentation | Visualization |

**Each layer:**

- Has one purpose
- Does not leak responsibility

## 8. Extensibility Model

### 8.1 Adding a New Cloud Service

**Required steps:**

1. Add configuration entry
2. Implement service collector
3. Define enrichment rules
4. Extend processor mappings
5. UI automatically adapts

No existing service logic should be modified.

### 8.2 Schema Evolution

- Schema versioning required
- Backward compatibility preferred
- Breaking changes are explicit

## 9. Architectural Constraints

| Constraint | Reason |
| --- | --- |
| No runtime backend | Offline requirement |
| No UI enrichment | Trust & auditability |
| Immutable reports | Compliance |
| Config-only execution | Simplicity |

## 10. Architectural Risks & Mitigation

| Risk | Mitigation |
| --- | --- |
| Over-engineering | Minimal viable layers |
| Tight coupling | Strict boundaries |
| Schema churn | Versioning discipline |
| UX overload | Progressive disclosure |

## 11. Architectural Principles (Binding)
1. Data is the contract
2. UI never guesses
3. Offline is first-class
4. Isolation beats cleverness
5. Humans over systems

## 12. Compliance With Previous Documents

| Document | Alignment |
| --- | --- |
| BRD | Decision-centric |
| FRD | Functional coverage |
| NFR | Offline, deterministic |

## 13. Change Control
**Changes to:**

- Component boundaries
- Data flow direction
- Headless model

**Require:**

- Architectural review
- Impact analysis
- Document update

Architecture Document Status
- Complete
- Authoritative
- Implementation-guiding
