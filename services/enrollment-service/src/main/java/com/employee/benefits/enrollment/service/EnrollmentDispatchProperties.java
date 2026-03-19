package com.employee.benefits.enrollment.service;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "app.outbox")
public class EnrollmentDispatchProperties {

    private long fixedDelayMs = 2000L;
    private long retryDelayMs = 5000L;
    private long claimTtlMs = 15000L;
    private int batchSize = 10;

    public long getFixedDelayMs() {
        return fixedDelayMs;
    }

    public void setFixedDelayMs(long fixedDelayMs) {
        this.fixedDelayMs = fixedDelayMs;
    }

    public long getRetryDelayMs() {
        return retryDelayMs;
    }

    public void setRetryDelayMs(long retryDelayMs) {
        this.retryDelayMs = retryDelayMs;
    }

    public long getClaimTtlMs() {
        return claimTtlMs;
    }

    public void setClaimTtlMs(long claimTtlMs) {
        this.claimTtlMs = claimTtlMs;
    }

    public int getBatchSize() {
        return batchSize;
    }

    public void setBatchSize(int batchSize) {
        this.batchSize = batchSize;
    }
}
