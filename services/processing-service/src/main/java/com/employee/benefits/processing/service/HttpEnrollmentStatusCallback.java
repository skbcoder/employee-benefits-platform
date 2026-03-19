package com.employee.benefits.processing.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.client.RestClient;

import java.util.Map;

public class HttpEnrollmentStatusCallback implements EnrollmentStatusCallback {

    private static final Logger log = LoggerFactory.getLogger(HttpEnrollmentStatusCallback.class);

    private final RestClient enrollmentServiceRestClient;

    public HttpEnrollmentStatusCallback(RestClient enrollmentServiceRestClient) {
        this.enrollmentServiceRestClient = enrollmentServiceRestClient;
    }

    @Override
    public void notifyCompleted(String enrollmentId) {
        try {
            enrollmentServiceRestClient.post()
                    .uri("/internal/enrollment-status")
                    .body(Map.of(
                            "enrollmentId", enrollmentId,
                            "status", "COMPLETED",
                            "message", "Enrollment processed successfully"
                    ))
                    .retrieve()
                    .toBodilessEntity();
        } catch (RuntimeException exception) {
            log.warn("Failed to notify enrollment service of completion for {}: {}",
                    enrollmentId, exception.getMessage());
        }
    }
}
