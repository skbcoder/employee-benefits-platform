package com.employee.benefits.enrollment.service;

import com.employee.benefits.enrollment.persistence.EnrollmentRecordEntity;
import com.employee.benefits.enrollment.persistence.EnrollmentRecordRepository;
import com.employee.benefits.enrollment.persistence.OutboxClaimRepository;
import com.employee.benefits.enrollment.persistence.OutboxDeliveryStatus;
import com.employee.benefits.enrollment.persistence.OutboxEventEntity;
import com.employee.benefits.enrollment.persistence.OutboxEventRepository;
import com.employee.benefits.shared.model.EnrollmentEvent;
import com.employee.benefits.shared.model.EnrollmentStatus;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;

@Service
public class OutboxDispatcherService {

    private final EnrollmentEventPublisher enrollmentEventPublisher;
    private final OutboxClaimRepository outboxClaimRepository;
    private final OutboxEventRepository outboxEventRepository;
    private final EnrollmentRecordRepository enrollmentRecordRepository;
    private final ObjectMapper objectMapper;
    private final EnrollmentDispatchProperties dispatchProperties;
    private final DispatcherInstanceIdProvider dispatcherInstanceIdProvider;

    public OutboxDispatcherService(
            EnrollmentEventPublisher enrollmentEventPublisher,
            OutboxClaimRepository outboxClaimRepository,
            OutboxEventRepository outboxEventRepository,
            EnrollmentRecordRepository enrollmentRecordRepository,
            ObjectMapper objectMapper,
            EnrollmentDispatchProperties dispatchProperties,
            DispatcherInstanceIdProvider dispatcherInstanceIdProvider
    ) {
        this.enrollmentEventPublisher = enrollmentEventPublisher;
        this.outboxClaimRepository = outboxClaimRepository;
        this.outboxEventRepository = outboxEventRepository;
        this.enrollmentRecordRepository = enrollmentRecordRepository;
        this.objectMapper = objectMapper;
        this.dispatchProperties = dispatchProperties;
        this.dispatcherInstanceIdProvider = dispatcherInstanceIdProvider;
    }

    @Transactional
    @Scheduled(fixedDelayString = "${app.outbox.fixed-delay-ms:2000}")
    public void dispatchPendingEvents() {
        Instant now = Instant.now();
        List<String> claimedEventIds = outboxClaimRepository.claimBatch(
                dispatcherInstanceIdProvider.getInstanceId(),
                now,
                now.minusMillis(dispatchProperties.getClaimTtlMs()),
                dispatchProperties.getBatchSize()
        );
        if (claimedEventIds.isEmpty()) {
            return;
        }

        List<OutboxEventEntity> pendingEvents = outboxEventRepository.findByEventIdInOrderByCreatedAtAsc(claimedEventIds);
        pendingEvents.forEach(this::dispatchSingleEvent);
    }

    private void dispatchSingleEvent(OutboxEventEntity outboxEvent) {
        EnrollmentRecordEntity enrollment = enrollmentRecordRepository.findById(outboxEvent.getAggregateId())
                .orElseThrow();

        try {
            enrollmentEventPublisher.publish(readPayload(outboxEvent.getPayload()));

            outboxEvent.setDeliveryStatus(OutboxDeliveryStatus.PUBLISHED);
            outboxEvent.setAttemptCount(outboxEvent.getAttemptCount() + 1);
            outboxEvent.setLastError(null);
            outboxEvent.setClaimedAt(null);
            outboxEvent.setClaimedBy(null);
            outboxEvent.setUpdatedAt(Instant.now());

            enrollment.setStatus(EnrollmentStatus.PROCESSING);
            enrollment.setStatusMessage("Enrollment event forwarded to processing service");
            enrollment.setUpdatedAt(Instant.now());
        } catch (RuntimeException exception) {
            outboxEvent.setDeliveryStatus(OutboxDeliveryStatus.FAILED);
            outboxEvent.setAttemptCount(outboxEvent.getAttemptCount() + 1);
            outboxEvent.setLastError(compactError(exception));
            outboxEvent.setAvailableAt(Instant.now().plusMillis(dispatchProperties.getRetryDelayMs()));
            outboxEvent.setClaimedAt(null);
            outboxEvent.setClaimedBy(null);
            outboxEvent.setUpdatedAt(Instant.now());

            enrollment.setStatus(EnrollmentStatus.DISPATCH_FAILED);
            enrollment.setStatusMessage("Enrollment saved but dispatch to processing service failed");
            enrollment.setUpdatedAt(Instant.now());
        }
    }

    private String compactError(RuntimeException exception) {
        String message = exception.getClass().getSimpleName() + ": " + exception.getMessage();
        return message.length() <= 500 ? message : message.substring(0, 500);
    }

    private EnrollmentEvent readPayload(String payload) {
        try {
            return objectMapper.readValue(payload, EnrollmentEvent.class);
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("Unable to deserialize outbox payload", exception);
        }
    }
}
