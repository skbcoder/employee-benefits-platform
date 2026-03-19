package com.employee.benefits.shared.model;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.util.List;

public record EnrollmentRequest(
        @NotBlank String employeeId,
        @NotBlank String employeeName,
        @Email @NotBlank String employeeEmail,
        @NotEmpty List<@Valid BenefitSelection> selections
) {
}
