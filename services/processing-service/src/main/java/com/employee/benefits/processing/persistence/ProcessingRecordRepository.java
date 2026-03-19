package com.employee.benefits.processing.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface ProcessingRecordRepository extends JpaRepository<ProcessingRecordEntity, String> {

    Optional<ProcessingRecordEntity> findTopByEmployeeIdOrderByUpdatedAtDesc(String employeeId);

    Optional<ProcessingRecordEntity> findTopByEmployeeNameIgnoreCaseOrderByUpdatedAtDesc(String employeeName);
}
