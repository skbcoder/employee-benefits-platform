package com.employee.benefits.enrollment.persistence;

import com.employee.benefits.shared.model.EnrollmentStatus;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface EnrollmentRecordRepository extends JpaRepository<EnrollmentRecordEntity, String> {

    @EntityGraph(attributePaths = "selections")
    Optional<EnrollmentRecordEntity> findByEnrollmentId(String enrollmentId);

    @EntityGraph(attributePaths = "selections")
    Optional<EnrollmentRecordEntity> findTopByEmployeeIdOrderByUpdatedAtDesc(String employeeId);

    @EntityGraph(attributePaths = "selections")
    Optional<EnrollmentRecordEntity> findTopByEmployeeNameIgnoreCaseOrderByUpdatedAtDesc(String employeeName);

    List<EnrollmentRecordEntity> findByStatusOrderByUpdatedAtDesc(EnrollmentStatus status);
}
