package com.employee.benefits.processing.controller;

import com.employee.benefits.processing.service.ProcessingApplicationService;
import com.employee.benefits.shared.model.EnrollmentEvent;
import com.employee.benefits.shared.model.EnrollmentSummary;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ProcessingController {

    private final ProcessingApplicationService processingApplicationService;

    public ProcessingController(ProcessingApplicationService processingApplicationService) {
        this.processingApplicationService = processingApplicationService;
    }

    @PostMapping("/internal/enrollment-events")
    @ResponseStatus(HttpStatus.ACCEPTED)
    public void processEnrollment(@RequestBody EnrollmentEvent enrollmentEvent) {
        processingApplicationService.accept(enrollmentEvent);
    }

    @GetMapping("/api/processed-enrollments/{enrollmentId}")
    public EnrollmentSummary getProcessedEnrollment(@PathVariable("enrollmentId") String enrollmentId) {
        return processingApplicationService.getProcessedEnrollment(enrollmentId);
    }

    @GetMapping("/api/processed-enrollments/by-employee/{employeeId}")
    public EnrollmentSummary getProcessedEnrollmentByEmployeeId(@PathVariable("employeeId") String employeeId) {
        return processingApplicationService.getLatestProcessedEnrollmentForEmployee(employeeId);
    }

    @GetMapping("/api/processed-enrollments/by-name/{employeeName}")
    public EnrollmentSummary getProcessedEnrollmentByEmployeeName(@PathVariable("employeeName") String employeeName) {
        return processingApplicationService.getLatestProcessedEnrollmentForEmployeeName(employeeName);
    }
}
