package com.employee.benefits.enrollment.service;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app.publisher")
public class EnrollmentPublisherProperties {

    private String transport = "http";
    private final Http http = new Http();

    public String getTransport() {
        return transport;
    }

    public void setTransport(String transport) {
        this.transport = transport;
    }

    public Http getHttp() {
        return http;
    }

    public static class Http {
        private String processingServiceUrl = "http://localhost:8081";

        public String getProcessingServiceUrl() {
            return processingServiceUrl;
        }

        public void setProcessingServiceUrl(String processingServiceUrl) {
            this.processingServiceUrl = processingServiceUrl;
        }
    }
}
