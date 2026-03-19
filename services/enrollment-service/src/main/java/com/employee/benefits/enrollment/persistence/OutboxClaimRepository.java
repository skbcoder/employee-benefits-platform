package com.employee.benefits.enrollment.persistence;

import org.springframework.jdbc.core.namedparam.MapSqlParameterSource;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Repository;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;

@Repository
public class OutboxClaimRepository {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    public OutboxClaimRepository(NamedParameterJdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public List<String> claimBatch(
            String workerId,
            Instant now,
            Instant claimExpiryCutoff,
            int batchSize
    ) {
        String sql = """
                WITH claimable AS (
                    SELECT event_id
                    FROM messaging.outbox_event
                    WHERE delivery_status IN ('PENDING', 'FAILED')
                      AND available_at <= :now
                      AND (claimed_at IS NULL OR claimed_at <= :claimExpiryCutoff)
                    ORDER BY created_at
                    LIMIT :batchSize
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE messaging.outbox_event outbox
                SET claimed_at = :now,
                    claimed_by = :workerId,
                    updated_at = :now
                FROM claimable
                WHERE outbox.event_id = claimable.event_id
                RETURNING outbox.event_id
                """;

        MapSqlParameterSource parameters = new MapSqlParameterSource()
                .addValue("workerId", workerId)
                .addValue("now", Timestamp.from(now))
                .addValue("claimExpiryCutoff", Timestamp.from(claimExpiryCutoff))
                .addValue("batchSize", batchSize);

        return jdbcTemplate.query(sql, parameters, this::mapEventId);
    }

    private String mapEventId(ResultSet resultSet, int rowNum) throws SQLException {
        return resultSet.getString("event_id");
    }
}
