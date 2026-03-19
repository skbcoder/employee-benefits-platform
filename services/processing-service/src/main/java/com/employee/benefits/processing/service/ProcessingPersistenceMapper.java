package com.employee.benefits.processing.service;

import com.employee.benefits.processing.persistence.ProcessingRecordEntity;
import com.employee.benefits.shared.model.EnrollmentStatus;
import com.employee.benefits.shared.model.EnrollmentSummary;
import org.springframework.stereotype.Component;

@Component
public class ProcessingPersistenceMapper {

    public EnrollmentSummary toSummary(ProcessingRecordEntity entity) {
        return new EnrollmentSummary(
                entity.getEnrollmentId(),
                entity.getEmployeeId(),
                entity.getEmployeeName(),
                entity.getStatus(),
                entity.getUpdatedAt(),
                entity.getProcessingMessage()
        );
    }

    public void markProcessing(ProcessingRecordEntity entity, String message) {
        entity.setStatus(EnrollmentStatus.PROCESSING);
        entity.setProcessingMessage(message);
    }
}
