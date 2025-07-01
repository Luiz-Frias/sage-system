# Decision Log Template

## Decision Metadata
- **Decision ID**: [Auto-generated UUID]
- **Timestamp**: [ISO-8601 format]
- **Agent ID**: [Agent making the decision]
- **Wave ID**: [If part of a wave coordination]
- **Decision Type**: [technical | architectural | business | operational]

## Context

### Domain and Task
- **Domain**: [e.g., insurance, ecommerce, saas]
- **Task Description**: [Clear description of what needs to be decided]
- **Triggering Event**: [What initiated this decision]

### Constraints
List all constraints affecting this decision:
- [ ] Performance requirements
- [ ] Security requirements
- [ ] Compliance requirements
- [ ] Resource limitations
- [ ] Time constraints
- [ ] Dependency constraints

### Dependencies
- **Upstream Dependencies**: [Decisions/components this depends on]
- **Downstream Impact**: [What will be affected by this decision]
- **Related Decisions**: [Link to related decision IDs]

## Analysis

### Requirements Summary
Brief summary of key requirements driving this decision.

### Options Considered
For each option:

#### Option 1: [Name]
- **Description**: [Brief description]
- **Pros**:
  - 
  - 
- **Cons**:
  - 
  - 
- **Risk Level**: [low | medium | high]
- **Estimated Effort**: [hours/days/weeks]

#### Option 2: [Name]
- **Description**: [Brief description]
- **Pros**:
  - 
  - 
- **Cons**:
  - 
  - 
- **Risk Level**: [low | medium | high]
- **Estimated Effort**: [hours/days/weeks]

#### Option 3: [Name]
- **Description**: [Brief description]
- **Pros**:
  - 
  - 
- **Cons**:
  - 
  - 
- **Risk Level**: [low | medium | high]
- **Estimated Effort**: [hours/days/weeks]

## Decision

### Selected Option
**Choice**: [Option name]

### Rationale
Detailed explanation of why this option was selected:
- Primary reasons
- How it best meets requirements
- Trade-offs accepted
- Risk mitigation strategies

### Implementation Plan
High-level steps for implementation:
1. 
2. 
3. 

### Success Criteria
Measurable criteria to determine if decision was successful:
- [ ] 
- [ ] 
- [ ] 

## Risk Assessment

### Identified Risks
| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| | low/medium/high | low/medium/high | |
| | low/medium/high | low/medium/high | |

### Contingency Plan
If this decision proves wrong, the fallback approach is:

## Outcome Tracking

### Initial Status
- **Status**: pending
- **Implementation Start**: [Date]
- **Expected Completion**: [Date]

### Progress Updates
[To be filled as implementation progresses]

#### Update [Date]:
- **Current Status**: [pending | in_progress | completed | failed]
- **Progress Notes**: 
- **Blockers**: 
- **Adjustments Made**: 

### Final Outcome
[To be filled after implementation]

- **Final Status**: [success | partial_success | failure]
- **Actual Completion Date**: 
- **Metrics Achieved**:
  - 
  - 
- **Lessons Learned**:
  - What worked well:
  - What could be improved:
  - Recommendations for similar decisions:

## Approval and Review

### Approvals
- **Decision Maker**: [Agent ID]
- **Reviewed By**: [Other agents consulted]
- **Domain Expert Validation**: [If applicable]

### Review Schedule
- **3-Month Review**: [Date] - Assess initial impact
- **6-Month Review**: [Date] - Evaluate long-term effects
- **Annual Review**: [Date] - Consider for pattern library

## References

### Documentation
- [Link to relevant documentation]
- [Link to domain guidelines]
- [Link to architectural principles]

### Related Decisions
- [Decision ID]: [Brief description]
- [Decision ID]: [Brief description]

### External Resources
- [Link to industry best practices]
- [Link to technology documentation]
- [Link to compliance requirements]

---

## Template Usage Notes

1. **When to Use**: For any significant decision that affects system architecture, technology choices, or business logic
2. **Level of Detail**: Adjust based on decision impact - critical decisions need more thorough documentation
3. **Living Document**: Update the outcome tracking section as implementation progresses
4. **Pattern Extraction**: Well-documented decisions can become patterns for future use
5. **Search Optimization**: Use consistent terminology to enable effective searching across decisions

### Quick Decision Categories
- **Technical**: Language choice, framework selection, algorithm selection
- **Architectural**: Service boundaries, communication patterns, data flow
- **Business**: Feature prioritization, domain rule interpretation
- **Operational**: Deployment strategies, monitoring approaches, scaling decisions