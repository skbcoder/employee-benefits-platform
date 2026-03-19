package com.employee.benefits.processing.service;

import com.employee.benefits.processing.persistence.InboxMessageEntity;
import com.employee.benefits.processing.persistence.InboxMessageRepository;
import com.employee.benefits.processing.persistence.ProcessingRecordEntity;
import com.employee.benefits.processing.persistence.ProcessingRecordRepository;
import com.employee.benefits.shared.model.EnrollmentEvent;
import com.employee.benefits.shared.model.EnrollmentStatus;
import com.employee.benefits.shared.model.EnrollmentSummary;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;

@Service
public class ProcessingApplicationService {

    private final ProcessingWorker processingWorker;
    private final ProcessingRecordRepository processingRecordRepository;
    private final InboxMessageRepository inboxMessageRepository;
    private final ProcessingPersistenceMapper processingPersistenceMapper;
    private final ObjectMapper objectMapper;

    public ProcessingApplicationService(
            ProcessingWorker processingWorker,
            ProcessingRecordRepository processingRecordRepository,
            InboxMessageRepository inboxMessageRepository,
            ProcessingPersistenceMapper processingPersistenceMapper,
            ObjectMapper objectMapper
    ) {
        this.processingWorker = processingWorker;
        this.processingRecordRepository = processingRecordRepository;
        this.inboxMessageRepository = inboxMessageRepository;
        this.processingPersistenceMapper = processingPersistenceMapper;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public void accept(EnrollmentEvent enrollmentEvent) {
        if (inboxMessageRepository.existsById(enrollmentEvent.eventId())) {
            return;
        }

        Instant now = Instant.now();

        InboxMessageEntity inboxMessage = new InboxMessageEntity();
        inboxMessage.setMessageId(enrollmentEvent.eventId());
        inboxMessage.setSourceSystem("enrollment-service");
        inboxMessage.setMessageType("EnrollmentSubmitted");
        inboxMessage.setAggregateId(enrollmentEvent.enrollmentId());
        inboxMessage.setProcessingStatus("RECEIVED");
        inboxMessage.setPayload(writePayload(enrollmentEvent));
        inboxMessage.setReceivedAt(now);
        inboxMessage.setUpdatedAt(now);
        inboxMessageRepository.save(inboxMessage);

        ProcessingRecordEntity processingRecord = processingRecordRepository.findById(enrollmentEvent.enrollmentId())
                .orElseGet(ProcessingRecordEntity::new);
        processingRecord.setEnrollmentId(enrollmentEvent.enrollmentId());
        processingRecord.setEmployeeId(enrollmentEvent.employeeId());
        processingRecord.setEmployeeName(enrollmentEvent.employeeName());
        processingRecord.setStatus(EnrollmentStatus.PROCESSING);
        processingRecord.setProcessingMessage("Enrollment event accepted for background processing");
        processingRecord.setReceivedAt(now);
        processingRecord.setUpdatedAt(now);
        processingRecordRepository.save(processingRecord);

        processingWorker.processAsync(enrollmentEvent);
    }

    @Transactional(readOnly = true)
    public EnrollmentSummary getProcessedEnrollment(String enrollmentId) {
        return processingRecordRepository.findById(enrollmentId)
                .map(processingPersistenceMapper::toSummary)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Processed enrollment not found"));
    }

    @Transactional(readOnly = true)
    public EnrollmentSummary getLatestProcessedEnrollmentForEmployee(String employeeId) {
        return processingRecordRepository.findTopByEmployeeIdOrderByUpdatedAtDesc(employeeId)
                .map(processingPersistenceMapper::toSummary)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Processed enrollment not found for employee"));
    }

    @Transactional(readOnly = true)
    public EnrollmentSummary getLatestProcessedEnrollmentForEmployeeName(String employeeName) {
        return processingRecordRepository.findTopByEmployeeNameIgnoreCaseOrderByUpdatedAtDesc(employeeName)
                .map(processingPersistenceMapper::toSummary)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Processed enrollment not found for employee name"));
    }

    private String writePayload(EnrollmentEvent event) {
        try {
            return objectMapper.writeValueAsString(event);
        } catch (JsonProcessingException exception) {
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Unable to serialize inbox payload");
        }
    }
}
