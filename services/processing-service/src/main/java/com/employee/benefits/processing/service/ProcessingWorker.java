package com.employee.benefits.processing.service;

import com.employee.benefits.processing.persistence.InboxMessageEntity;
import com.employee.benefits.processing.persistence.InboxMessageRepository;
import com.employee.benefits.processing.persistence.ProcessingRecordEntity;
import com.employee.benefits.processing.persistence.ProcessingRecordRepository;
import com.employee.benefits.shared.model.EnrollmentEvent;
import com.employee.benefits.shared.model.EnrollmentStatus;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionTemplate;

import java.time.Instant;

@Component
public class ProcessingWorker {

    private final ProcessingRecordRepository processingRecordRepository;
    private final InboxMessageRepository inboxMessageRepository;
    private final EnrollmentStatusCallback enrollmentStatusCallback;
    private final TransactionTemplate transactionTemplate;

    public ProcessingWorker(
            ProcessingRecordRepository processingRecordRepository,
            InboxMessageRepository inboxMessageRepository,
            EnrollmentStatusCallback enrollmentStatusCallback,
            TransactionTemplate transactionTemplate
    ) {
        this.processingRecordRepository = processingRecordRepository;
        this.inboxMessageRepository = inboxMessageRepository;
        this.enrollmentStatusCallback = enrollmentStatusCallback;
        this.transactionTemplate = transactionTemplate;
    }

    @Async
    public void processAsync(EnrollmentEvent enrollmentEvent) {
        try {
            Thread.sleep(500);
        } catch (InterruptedException interruptedException) {
            Thread.currentThread().interrupt();
        }

        transactionTemplate.executeWithoutResult(status -> {
            ProcessingRecordEntity processingRecord = processingRecordRepository.findById(enrollmentEvent.enrollmentId())
                    .orElseThrow();
            processingRecord.setStatus(EnrollmentStatus.COMPLETED);
            processingRecord.setProcessingMessage("Enrollment processed successfully");
            processingRecord.setCompletedAt(Instant.now());
            processingRecord.setUpdatedAt(Instant.now());

            InboxMessageEntity inboxMessage = inboxMessageRepository.findById(enrollmentEvent.eventId())
                    .orElseThrow();
            inboxMessage.setProcessingStatus("PROCESSED");
            inboxMessage.setProcessedAt(Instant.now());
            inboxMessage.setUpdatedAt(Instant.now());
        });

        enrollmentStatusCallback.notifyCompleted(enrollmentEvent.enrollmentId());
    }
}
