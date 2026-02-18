# Data Contract Document - JSON Schema

*Philosophy*

- **Project Name:** FinLens
- **Document Type:** Data Contract / Data Architecture
- **Audience:** Architects; Engineers; UI Developers; Future Contributors; Auditors
- **Document Nature:** Highly Controlled, Living
- **Stability:** Very High (breaking changes are rare and expensive)

## 1. Purpose of This Document
This document defines the data contract between:

- Backend (scanner + processor)
- Frontend (UI)
- Future versions of FinLens
- Humans reading archived reports

**It answers:**

- What data exists
- How data is structured
- What guarantees the data provides
- How data evolves safely over time

Processed JSON is the product. Everything else exists to create or interpret it.

## 2. Core Data Philosophy (Non-Negotiable)

### 2.1 JSON Is the Source of Truth

- The processed JSON represents the complete, final, authoritative state
- UI must never infer, guess, or recalculate data
- Backend must never rely on UI logic

### 2.2 JSON Must Be Human-Readable

- A human should understand the file without tools
- Clear naming over compactness
- Explicit fields over implicit meaning

### 2.3 JSON Must Be Long-Lived

- Reports may be opened years later
- Meaning must survive:
  - Cloud API changes
  - FinLens version changes
  - UI rewrites

## 3. Contract Boundaries

### 3.1 What the Backend Guarantees

- Data accuracy at scan time
- Deterministic structure
- Explicit meaning of all fields
- Stable schema version

### 3.2 What the UI Guarantees

- Faithful rendering of JSON
- No data mutation
- No hidden enrichment
- Respect for schema versioning

## 4. Data Classification

| Data Type | Description | Mutability |
| --- | --- | --- |
| Metadata | Scan context | Immutable |
| Account Data | Processed account state | Immutable |
| Derived Signals | Enrichment outputs | Immutable |
| UI State | Filters, sorting | Ephemeral |

Only UI state is allowed to change.

## 5. High-Level JSON Structure
**Processed Report**

```
schema_version
generated_at
account
  account_id
  account_name
  currency
  services
    service[]
      service_name
      summary
      resources[]
```
This hierarchy is fixed.

## 6. Root-Level Contract

### 6.1 schema_version

**Purpose:** Controls compatibility between generator and consumer.

**Rules:**

- Required
- Semantic versioning
- UI behavior may vary by version

### 6.2 generated_at

**Purpose:** Defines when the data snapshot was taken.

**Rules:**

- ISO-8601 format
- Informational only
- UI must never use it for logic

## 7. Account-Level Contract

### 7.1 account Object

Represents one cloud account at a specific moment.

**Required Fields:**

- account_id
- account_name
- currency
- services

No cross-account data allowed.

## 8. Service-Level Contract

### 8.1 service Object

Represents one cloud service (e.g., EC2, Lambda).

**Required Fields:**

- service_id
- service_name
- region_scope
- summary
- resources

### 8.2 service.summary Object

**Purpose:** Enable decision-making without drilling down.

**Typical Fields:**

- resource_count
- monthly_cost
- health_status
- optimization_potential
- risk_level

**Rules:**

- Aggregated from resources
- Must be explainable
- No hidden math

## 9. Resource-Level Contract

### 9.1 resource Object

Represents one cloud resource.

**Required Fields:**

- resource_id
- resource_name
- region
- cost
- utilization
- health
- optimization

### 9.2 Explicit Nullability Rule

**If data is unavailable:**

- Field must exist
- Value must be null
- Never omit silently

This preserves trust.

## 10. Cost Representation Rules
- Costs are:
  - Monthly
  - Numeric
  - In declared currency
- Zero cost = missing cost
- Cost breakdowns must be explicit

## 11. Utilization & Metrics Philosophy
- Utilization is contextual, not absolute
- Values must include:
  - Metric name
  - Time window
  - Interpretation hint

No raw metrics without explanation.

## 12. Health & Risk Signals

### 12.1 Health

- Represents current operational state
- Example values:
  - healthy
  - warning
  - unhealthy

**Must include:**

- Reason
- Evidence reference

### 12.2 Risk

- Represents potential future issue
- Must never be alarmist
- Must include reasoning

## 13. Optimization Hints
**Rules**

- Hints are suggestions, not actions
- Each hint must include:
  - Reason
  - Potential impact
  - Confidence level

No automated recommendations without context.

## 14. Naming & Semantic Rules
- snake_case keys
- No abbreviations unless industry-standard
- No overloaded fields
- Same name = same meaning everywhere

## 15. Ordering Rules
- Arrays must have stable ordering
- Sorting rules must be deterministic
- UI may re-order visually but not mutate data

## 16. Schema Evolution Strategy

### 16.1 Allowed Changes

- Adding new fields
- Adding new services
- Adding optional fields

### 16.2 Breaking Changes (Rare)

**Breaking changes include:**

- Renaming fields
- Changing meanings
- Removing fields

**Require:**

1. Schema version bump
2. Migration strategy
3. Explicit documentation

## 17. Backward Compatibility Policy
- UI should support at least N-1 versions
- Older reports must remain readable
- Best-effort rendering is acceptable, failure is not

## 18. Validation Rules
**Before a report is considered valid:**

- Schema version present
- Required fields present
- No silent drops
- JSON is parseable and readable

## 19. Anti-Patterns (Explicitly Forbidden)
- UI-derived calculations
- Implicit meanings
- Magic numbers
- Schema-less extensions
- "Temporary" fields

There is no such thing as temporary in data contracts.

## 20. Governance & Ownership

- Data contract is owned by Product + Architecture
- Any change requires:
  - Impact analysis
  - Document update
  - Version bump (if needed)

## 21. Acceptance Criteria
**This data contract is satisfied when:**

- UI can render reports without backend
- Humans can understand JSON directly
- Old reports survive new releases
- Decisions can be traced to data
