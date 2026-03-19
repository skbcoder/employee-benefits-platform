package com.employee.benefits.enrollment.service;

import com.employee.benefits.enrollment.persistence.EnrollmentRecordEntity;
import com.employee.benefits.enrollment.persistence.EnrollmentSelectionEntity;
import com.employee.benefits.shared.model.BenefitSelection;
import com.employee.benefits.shared.model.EnrollmentRequest;
import com.employee.benefits.shared.model.EnrollmentStatus;
import com.employee.benefits.shared.model.EnrollmentSummary;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.UUID;

@Component
public class EnrollmentPersistenceMapper {

    public EnrollmentRecordEntity toNewEnrollmentRecord(
            String enrollmentId,
            EnrollmentRequest request,
            EnrollmentStatus status,
            String statusMessage,
            Instant now
    ) {
        EnrollmentRecordEntity entity = new EnrollmentRecordEntity();
        entity.setEnrollmentId(enrollmentId);
        entity.setEmployeeId(request.employeeId());
        entity.setEmployeeName(request.employeeName());
        entity.setEmployeeEmail(request.employeeEmail());
        entity.setStatus(status);
        entity.setStatusMessage(statusMessage);
        entity.setSubmittedAt(now);
        entity.setUpdatedAt(now);

        for (BenefitSelection selection : request.selections()) {
            EnrollmentSelectionEntity selectionEntity = new EnrollmentSelectionEntity();
            selectionEntity.setSelectionId(UUID.randomUUID().toString());
            selectionEntity.setBenefitType(selection.type());
            selectionEntity.setBenefitPlan(selection.plan());
            entity.addSelection(selectionEntity);
        }
        return entity;
    }

    public EnrollmentSummary toSummary(EnrollmentRecordEntity entity) {
        return new EnrollmentSummary(
                entity.getEnrollmentId(),
                entity.getEmployeeId(),
                entity.getEmployeeName(),
                entity.getStatus(),
                entity.getUpdatedAt(),
                entity.getStatusMessage()
        );
    }
}
