package com.employee.benefits.shared.model;

import jakarta.validation.constraints.NotBlank;

public record BenefitSelection(
        @NotBlank String type,
        @NotBlank String plan
) {
}
