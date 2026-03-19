package com.employee.benefits.enrollment.controller;

import com.employee.benefits.enrollment.service.EnrollmentApplicationService;
import com.employee.benefits.shared.model.EnrollmentRequest;
import com.employee.benefits.shared.model.EnrollmentStatus;
import com.employee.benefits.shared.model.EnrollmentSummary;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/enrollments")
public class EnrollmentController {

    private final EnrollmentApplicationService enrollmentApplicationService;

    public EnrollmentController(EnrollmentApplicationService enrollmentApplicationService) {
        this.enrollmentApplicationService = enrollmentApplicationService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.ACCEPTED)
    public EnrollmentSummary submitEnrollment(@Valid @RequestBody EnrollmentRequest request) {
        return enrollmentApplicationService.submit(request);
    }

    @GetMapping("/{enrollmentId}")
    public EnrollmentSummary getEnrollment(@PathVariable("enrollmentId") String enrollmentId) {
        return enrollmentApplicationService.getEnrollment(enrollmentId);
    }

    @GetMapping("/by-employee/{employeeId}")
    public EnrollmentSummary getEnrollmentByEmployeeId(@PathVariable("employeeId") String employeeId) {
        return enrollmentApplicationService.getLatestEnrollmentForEmployee(employeeId);
    }

    @GetMapping("/by-name/{employeeName}")
    public EnrollmentSummary getEnrollmentByEmployeeName(@PathVariable("employeeName") String employeeName) {
        return enrollmentApplicationService.getLatestEnrollmentForEmployeeName(employeeName);
    }

    @GetMapping("/by-status")
    public List<EnrollmentSummary> getEnrollmentsByStatus(@RequestParam("status") EnrollmentStatus status) {
        return enrollmentApplicationService.getEnrollmentsByStatus(status);
    }
}
