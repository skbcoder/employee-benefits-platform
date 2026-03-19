package com.employee.benefits.enrollment.config;

import com.employee.benefits.enrollment.service.EnrollmentEventPublisher;
import com.employee.benefits.enrollment.service.EnrollmentPublisherProperties;
import com.employee.benefits.enrollment.service.EventBridgeEnrollmentEventPublisher;
import com.employee.benefits.enrollment.service.HttpEnrollmentEventPublisher;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
@EnableConfigurationProperties(EnrollmentPublisherProperties.class)
public class EnrollmentPublisherConfig {

    @Bean
    @ConditionalOnProperty(prefix = "app.publisher", name = "transport", havingValue = "http", matchIfMissing = true)
    EnrollmentEventPublisher httpEnrollmentEventPublisher(
            RestClient.Builder builder,
            EnrollmentPublisherProperties publisherProperties
    ) {
        return new HttpEnrollmentEventPublisher(
                builder.baseUrl(publisherProperties.getHttp().getProcessingServiceUrl()).build()
        );
    }

    @Bean
    @ConditionalOnProperty(prefix = "app.publisher", name = "transport", havingValue = "eventbridge")
    EnrollmentEventPublisher eventBridgeEnrollmentEventPublisher() {
        return new EventBridgeEnrollmentEventPublisher();
    }
}
