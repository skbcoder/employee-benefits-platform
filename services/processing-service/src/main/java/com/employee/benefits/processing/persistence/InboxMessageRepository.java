package com.employee.benefits.processing.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

public interface InboxMessageRepository extends JpaRepository<InboxMessageEntity, String> {
}
