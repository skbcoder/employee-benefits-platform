package com.employee.benefits.enrollment.service;

import com.employee.benefits.shared.model.EnrollmentEvent;

public interface EnrollmentEventPublisher {

    void publish(EnrollmentEvent enrollmentEvent);
}
