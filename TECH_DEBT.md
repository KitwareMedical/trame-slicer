# Technical Debt Log

This document tracks known technical debt in the project, including areas that
require refactoring, optimization, or future improvements.

## Debt Item Template

### Issue: Brief Issue Title

- **Description**: Describe the problem and its implications.
- **Impact**: How does this affect performance, scalability, or maintainability?
- **Potential Solution**: Proposed fix or approach to mitigate the issue.
- **Priority**: High / Medium / Low
- **Created By**: [Developer Name]
- **Date Logged**: [YYYY-MM-DD]
- **Status**: Open / In Progress

## Resolution Process

### Adding a New Issue

1. Identify an area of technical debt and define the problem clearly.
2. Log the issue using the format above, ensuring it is detailed and actionable.
3. Assign a priority level based on its impact.
4. When possible add in the technical debt issue when its associated commit is
   created.

### Updating an Existing Issue

1. Mark the issue as `In Progress` when work begins.
2. Document any new insights, challenges, or partial fixes discovered.
3. Update the status once resolved and add a summary of the changes made.

### Resolving an Issue

1. Implement the necessary changes and ensure code quality.
2. Run tests and confirm the fix does not introduce new issues.
3. Remove the issue from the technical debt log and record any follow-up issues.
4. If necessary, create documentation to prevent similar issues in the future.
5. Create the merge request and link to the resolved issue in the MR title.

---

## Debt Items

---

### Issue: Segment editor effects code duplication from Slicer codebase

- **Description**: Part of the current code base duplicate the Slicer Segment
  Editor Effect logic.
  - Duplication comes from implementation of the current segment editor effects
    which is Qt based and don't use the existing displayable manager pattern.
- **Impact**: Increased maintainability problems when making changes to the
  segment editor effects.
- **Potential Solution**:
  - Refactor the core logic of the segment editor effects into displayable
    manager pipelines.
  - Contribute the effect logic to Slicer main.
- **Priority**: Medium
- **Created By**: [Thibault Pelletier]
- **Date Logged**: [2025-06-18]
- **Status**: In Progress
  - Part of the segment editor logic was extracted into a dedicated logic class
    in the main Slicer branch.
  - The Layer Displayable Manager extension was contributed as an external
    extension to simplify creating and managing new segment editor effects.
  - Existing segment editor effects have been refactored to implement the new
    logic.
  - REMAINING: Dev meeting to decide if/how these effects should be brought back
    to the main Slicer branch.

---

### Issue: IOManager code reimplementation from Slicer codebase

- **Description**: Current IOManager class reimplements loading logic
  - Duplication comes from implementation of the current IO module mechanism
    being Qt based.
- **Impact**: Increased implementation and maintainability problems.
- **Potential Solution**: Existing IO logic should be split into VTK and Qt
  components in the Slicer main codebase. Trame-slicer should depend on the
  Slicer VTK logic for handling IO.
- **Priority**: Medium
- **Created By**: [Thibault Pelletier]
- **Date Logged**: [2025-06-18]
- **Status**: Open
