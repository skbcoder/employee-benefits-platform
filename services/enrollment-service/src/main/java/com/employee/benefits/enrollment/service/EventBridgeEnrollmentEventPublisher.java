package com.employee.benefits.enrollment.service;

import com.employee.benefits.shared.model.EnrollmentEvent;

public class EventBridgeEnrollmentEventPublisher implements EnrollmentEventPublisher {

    @Override
    public void publish(EnrollmentEvent enrollmentEvent) {
        throw new UnsupportedOperationException(
                "EventBridge transport is not implemented yet. Configure app.publisher.transport=http for local delivery."
        );
    }
}
