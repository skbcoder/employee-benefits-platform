package com.employee.benefits.enrollment.service;

import com.employee.benefits.shared.model.EnrollmentEvent;
import org.springframework.web.client.RestClient;

public class HttpEnrollmentEventPublisher implements EnrollmentEventPublisher {

    private final RestClient processingServiceRestClient;

    public HttpEnrollmentEventPublisher(RestClient processingServiceRestClient) {
        this.processingServiceRestClient = processingServiceRestClient;
    }

    @Override
    public void publish(EnrollmentEvent enrollmentEvent) {
        processingServiceRestClient.post()
                .uri("/internal/enrollment-events")
                .body(enrollmentEvent)
                .retrieve()
                .toBodilessEntity();
    }
}
