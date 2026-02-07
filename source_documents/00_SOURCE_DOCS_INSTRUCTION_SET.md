---
name: Source Documents Consumption Contract
purpose: Define deterministic input order and validation policy for supervisor planning.
layer: source_context
---

# Objective
Use source documents as structured planning inputs for generated implementation plans.

## Input Order
1. `source_documents/product_architectures/business-architecture.md`
2. `source_documents/product_requirements/data-driven-prd-template.md`
3. `source_documents/product_requirements/insurance-specific-prd.md`
4. `source_documents/product_architectures/data-architecture.md`
5. `source_documents/product_architectures/application-architecture.md`
6. `source_documents/product_architectures/technology-architecture.md`
7. `source_documents/tech-stack.md`
8. `source_documents/product-roadmap.md`
9. `source_documents/product_roadmaps/discovery-and-planning.md`
10. `source_documents/product_roadmaps/development-and-configuration.md`
11. `source_documents/product_roadmaps/deployment-and-go-live.md`

## Output Requirements
Extract and normalize:
1. domain requirements
2. non-functional constraints
3. dependency boundaries
4. rollout and risk constraints
5. quality and compliance gates

## Validation Gates
1. completeness gate:
   - all required source files present
2. consistency gate:
   - cross-document dependencies non-contradictory
3. compliance gate:
   - domain and regulatory requirements mapped
4. technical gate:
   - architecture and stack alignment confirmed
5. planning gate:
   - extracted context supports phase/wave cardinality contract

## Planning Contract Linkage
Generated plans that use this source context must satisfy:
- phases >= 7
- waves per phase >= 5
- 4 milestones per phase
- 15 tasks per milestone
- rolling integration and cumulative e2e after phase 1

## Consumption Checklist
- [ ] required sources loaded
- [ ] dependency graph extracted
- [ ] risk matrix extracted
- [ ] gate matrix extracted
- [ ] planning contract constraints mapped
