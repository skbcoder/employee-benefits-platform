package com.employee.benefits.shared.model;

import java.time.Instant;
import java.util.List;

public record EnrollmentEvent(
        String eventId,
        String correlationId,
        String enrollmentId,
        String employeeId,
        String employeeName,
        String employeeEmail,
        List<BenefitSelection> selections,
        Instant submittedAt,
        Instant occurredAt
) {
}
