package com.employee.benefits.enrollment.controller;

import com.employee.benefits.enrollment.service.EnrollmentApplicationService;
import com.employee.benefits.shared.model.EnrollmentStatus;
import com.employee.benefits.shared.model.EnrollmentSummary;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class EnrollmentInternalController {

    private final EnrollmentApplicationService enrollmentApplicationService;

    public EnrollmentInternalController(EnrollmentApplicationService enrollmentApplicationService) {
        this.enrollmentApplicationService = enrollmentApplicationService;
    }

    public record StatusUpdateRequest(String enrollmentId, EnrollmentStatus status, String message) {}

    @PostMapping("/internal/enrollment-status")
    public EnrollmentSummary updateEnrollmentStatus(@RequestBody StatusUpdateRequest request) {
        return enrollmentApplicationService.updateStatus(request.enrollmentId(), request.status(), request.message());
    }
}
