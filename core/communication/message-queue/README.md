# SAGE Message Queue

This directory contains asynchronous messages between SAGE agents following the SAGE Agent Communication Protocol (SACP).

## Message Format

All messages in this queue must follow the standard format defined in the communication protocol:

### Required Structure

Messages are markdown files with YAML frontmatter containing:

```yaml
---
agent_id: [unique-identifier]
agent_type: [development|support]
wave: [1|2|3|4]
timestamp: [ISO-8601]
status: [initializing|working|blocked|completed|failed]
branch: [git-branch-name]
message_type: [status|request|response|alert|decision]
priority: [low|medium|high|critical]
---
```

### Message Body Structure

After the frontmatter, the message body should be structured as:

```markdown
## Message Content

[Main message content in markdown format]

### Working On
- [List of files/components currently being modified]

### Dependencies
- [Required inputs from other agents]

### Blockers
- [Any blocking issues preventing progress]

### Next Steps
- [Planned actions]
```

## Message Types

### 1. Status Update
- Regular progress updates sent every 15 minutes or on significant progress
- Must include progress percentage

### 2. Dependency Request
- Request artifacts from another agent
- Must specify target agent, required artifacts, deadline, and priority

### 3. Conflict Alert
- Notify of resource conflicts
- Include conflict type, affected resources, and proposed resolution

### 4. Completion Notice
- Signal task completion
- Include completed artifacts, output locations, test results, and next agent handoff

## File Naming Convention

Message files should follow this naming pattern:
```
[timestamp]-[agent_id]-[message_type].md
```

Example: `2024-12-31T10-30-00Z-backend-api-specialist-001-status.md`

## Message Processing

Messages are processed by the Communication/Historian agent who:
- Routes messages to appropriate recipients
- Tracks message delivery
- Maintains the agent registry
- Resolves conflicts
- Archives processed messages

## Important Notes

1. All timestamps must be in ISO-8601 format with UTC timezone
2. Agent IDs must match those in the agent registry
3. Branch names should follow the naming convention: `feat/wave[N]-[component]-[date]`
4. Messages are processed in priority order: critical > high > medium > low
5. Status updates should include a progress percentage when applicable