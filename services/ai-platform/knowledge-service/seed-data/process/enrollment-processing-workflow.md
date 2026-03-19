# Enrollment Processing Workflow

## Overview

This document describes the internal workflow for processing employee benefit enrollment requests from submission through completion. It covers the system workflow, validation rules, exception handling, and escalation procedures.

## System Workflow

### Step 1: Enrollment Submission
- Employee submits enrollment through the benefits portal or API
- System validates required fields: employee ID, name, email, at least one benefit selection
- Each benefit selection must include a valid benefit type (medical, dental, vision, life) and plan tier
- System generates a unique enrollment ID and assigns SUBMITTED status
- Enrollment record and benefit selections are persisted in a single database transaction
- An outbox event is created in the same transaction for downstream processing

### Step 2: Event Dispatch
- The outbox dispatcher picks up pending events every 2 seconds
- Events are claimed using database row-level locking (FOR UPDATE SKIP LOCKED) to support multiple dispatcher instances
- The event is forwarded to the processing service via the publisher adapter (currently HTTP, planned EventBridge)
- On successful delivery, the enrollment status is updated to PROCESSING
- On failure, the event is marked as DISPATCH_FAILED and retried after a 5-second backoff
- Events are retried up to 10 times before requiring manual intervention

### Step 3: Processing
- The processing service receives the enrollment event
- An inbox message is recorded for idempotency (duplicate events are silently ignored)
- A processing record is created with PROCESSING status
- The enrollment undergoes validation and processing
- Upon successful processing, status is updated to COMPLETED

### Step 4: Completion
- The enrollment is marked as COMPLETED in the processing record
- The enrollment is now active and the employee's benefits are in effect
- Confirmation can be retrieved through the enrollment status API

## Validation Rules

### Employee Validation
- Employee ID must be in the format E followed by 5 digits (e.g., E12345)
- Employee name must not be blank
- Employee email must be a valid email address
- Employee must be in the HR system (future validation)

### Benefit Selection Validation
- At least one benefit selection is required
- No duplicate benefit types (cannot select medical twice)
- Valid benefit types: medical, dental, vision, life
- Valid plan tiers per benefit type:
  - Medical: basic, silver, gold, platinum
  - Dental: basic, premium
  - Vision: basic, premium
  - Life: basic (employer-paid, auto-enrolled), supplemental_1x through supplemental_5x

### Eligibility Validation (Future Enhancement)
When the AI validation agent is active, the following additional checks will be performed:
- Employee eligibility status (full-time, part-time, temporary)
- Waiting period completion
- Open enrollment window or qualifying life event verification
- Dependent eligibility if dependents are included
- Plan availability in employee's service area

## Exception Handling

### DISPATCH_FAILED Status
- Indicates the outbox dispatcher failed to deliver the event to the processing service
- Most common cause: processing service is temporarily unavailable
- Automatic retry with exponential backoff (5s, 10s, 20s, ...)
- After 10 failed attempts, the event requires manual review
- HR Benefits team is notified via alert when events exceed 5 retry attempts

### Processing Errors
- If the processing service encounters an error after receiving the event, the processing record captures the error
- Idempotency ensures re-delivery of the same event is safe
- Processing errors are logged and may trigger manual review

### Duplicate Submissions
- The system allows multiple enrollments per employee (each gets a unique enrollment ID)
- The most recent enrollment is considered the active election
- Previous enrollments remain in the system for audit purposes
- During open enrollment, the last enrollment submitted before the deadline takes effect

## Escalation Procedures

### Level 1: Automated Resolution
- DISPATCH_FAILED events are automatically retried
- Duplicate events are automatically deduplicated via inbox idempotency
- Standard validations are enforced at submission time

### Level 2: HR Benefits Team
- Enrollments stuck in PROCESSING for more than 24 hours
- Events exceeding 5 retry attempts
- Enrollments flagged by the AI validation agent as NEEDS_REVIEW
- Employee-reported issues with enrollment status

### Level 3: Benefits Manager
- Enrollments rejected by the AI compliance agent
- Policy exceptions requiring manager approval
- Late enrollment requests requiring authorization
- Complex eligibility determinations

### Level 4: HR Director
- HIPAA-related concerns
- Regulatory compliance issues
- Systematic processing failures affecting multiple employees
- Policy changes or exceptions affecting the broader employee population

## Processing SLAs

| Metric | Target | Escalation Threshold |
|--------|--------|---------------------|
| Enrollment submission to PROCESSING | < 5 minutes | > 15 minutes |
| PROCESSING to COMPLETED | < 1 hour | > 4 hours |
| End-to-end (submission to completion) | < 2 hours | > 24 hours |
| DISPATCH_FAILED resolution | < 30 minutes | > 2 hours |
| Manual review turnaround | < 2 business days | > 5 business days |

## Audit Trail

The system maintains a complete audit trail for every enrollment:
- Enrollment record with timestamps (submitted, updated)
- Outbox event record with delivery status and attempt history
- Inbox message record with receipt timestamp
- Processing record with status transitions and timestamps
- All records are immutable (updates create new state, history is preserved)
