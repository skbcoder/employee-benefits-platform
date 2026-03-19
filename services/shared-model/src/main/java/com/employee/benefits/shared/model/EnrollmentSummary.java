package com.employee.benefits.shared.model;

import java.time.Instant;

public record EnrollmentSummary(
        String enrollmentId,
        String employeeId,
        String employeeName,
        EnrollmentStatus status,
        Instant updatedAt,
        String message
) {
}
