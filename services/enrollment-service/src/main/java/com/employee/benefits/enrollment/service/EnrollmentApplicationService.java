package com.employee.benefits.enrollment.service;

import com.employee.benefits.enrollment.persistence.EnrollmentRecordEntity;
import com.employee.benefits.enrollment.persistence.EnrollmentRecordRepository;
import com.employee.benefits.enrollment.persistence.OutboxDeliveryStatus;
import com.employee.benefits.enrollment.persistence.OutboxEventEntity;
import com.employee.benefits.enrollment.persistence.OutboxEventRepository;
import com.employee.benefits.shared.model.EnrollmentEvent;
import com.employee.benefits.shared.model.EnrollmentRequest;
import com.employee.benefits.shared.model.EnrollmentSummary;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

@Service
public class EnrollmentApplicationService {

    private final EnrollmentRecordRepository enrollmentRecordRepository;
    private final OutboxEventRepository outboxEventRepository;
    private final EnrollmentPersistenceMapper enrollmentPersistenceMapper;
    private final ObjectMapper objectMapper;

    public EnrollmentApplicationService(
            EnrollmentRecordRepository enrollmentRecordRepository,
            OutboxEventRepository outboxEventRepository,
            EnrollmentPersistenceMapper enrollmentPersistenceMapper,
            ObjectMapper objectMapper
    ) {
        this.enrollmentRecordRepository = enrollmentRecordRepository;
        this.outboxEventRepository = outboxEventRepository;
        this.enrollmentPersistenceMapper = enrollmentPersistenceMapper;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public EnrollmentSummary submit(EnrollmentRequest request) {
        String enrollmentId = UUID.randomUUID().toString();
        String eventId = UUID.randomUUID().toString();
        String correlationId = enrollmentId;
        Instant now = Instant.now();

        EnrollmentRecordEntity enrollmentRecord = enrollmentPersistenceMapper.toNewEnrollmentRecord(
                enrollmentId,
                request,
                com.employee.benefits.shared.model.EnrollmentStatus.SUBMITTED,
                "Enrollment accepted and queued for processing",
                now
        );
        enrollmentRecord = enrollmentRecordRepository.save(enrollmentRecord);

        EnrollmentEvent event = new EnrollmentEvent(
                eventId,
                correlationId,
                enrollmentId,
                request.employeeId(),
                request.employeeName(),
                request.employeeEmail(),
                request.selections(),
                now,
                now
        );
        outboxEventRepository.save(newOutboxEvent(event, now));
        return enrollmentPersistenceMapper.toSummary(enrollmentRecord);
    }

    @Transactional(readOnly = true)
    public EnrollmentSummary getEnrollment(String enrollmentId) {
        return enrollmentRecordRepository.findByEnrollmentId(enrollmentId)
                .map(enrollmentPersistenceMapper::toSummary)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Enrollment not found"));
    }

    @Transactional(readOnly = true)
    public EnrollmentSummary getLatestEnrollmentForEmployee(String employeeId) {
        return enrollmentRecordRepository.findTopByEmployeeIdOrderByUpdatedAtDesc(employeeId)
                .map(enrollmentPersistenceMapper::toSummary)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Enrollment not found for employee"));
    }

    @Transactional(readOnly = true)
    public EnrollmentSummary getLatestEnrollmentForEmployeeName(String employeeName) {
        return enrollmentRecordRepository.findTopByEmployeeNameIgnoreCaseOrderByUpdatedAtDesc(employeeName)
                .map(enrollmentPersistenceMapper::toSummary)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Enrollment not found for employee name"));
    }

    @Transactional
    public EnrollmentSummary updateStatus(String enrollmentId, com.employee.benefits.shared.model.EnrollmentStatus status, String message) {
        EnrollmentRecordEntity enrollment = enrollmentRecordRepository.findByEnrollmentId(enrollmentId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Enrollment not found"));
        enrollment.setStatus(status);
        enrollment.setStatusMessage(message);
        enrollment.setUpdatedAt(Instant.now());
        return enrollmentPersistenceMapper.toSummary(enrollment);
    }

    @Transactional(readOnly = true)
    public List<EnrollmentSummary> getEnrollmentsByStatus(com.employee.benefits.shared.model.EnrollmentStatus status) {
        return enrollmentRecordRepository.findByStatusOrderByUpdatedAtDesc(status)
                .stream()
                .map(enrollmentPersistenceMapper::toSummary)
                .toList();
    }

    private OutboxEventEntity newOutboxEvent(EnrollmentEvent event, Instant now) {
        OutboxEventEntity entity = new OutboxEventEntity();
        entity.setEventId(event.eventId());
        entity.setAggregateType("ENROLLMENT");
        entity.setAggregateId(event.enrollmentId());
        entity.setEventType("EnrollmentSubmitted");
        entity.setDeliveryStatus(OutboxDeliveryStatus.PENDING);
        entity.setCorrelationId(event.correlationId());
        entity.setPayload(writePayload(event));
        entity.setAvailableAt(now);
        entity.setAttemptCount(0);
        entity.setLastError(null);
        entity.setClaimedAt(null);
        entity.setClaimedBy(null);
        entity.setCreatedAt(now);
        entity.setUpdatedAt(now);
        return entity;
    }

    private String writePayload(EnrollmentEvent event) {
        try {
            return objectMapper.writeValueAsString(event);
        } catch (JsonProcessingException exception) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Unable to serialize enrollment event");
        }
    }
}
