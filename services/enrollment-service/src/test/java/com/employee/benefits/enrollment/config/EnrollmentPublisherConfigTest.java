package com.employee.benefits.enrollment.config;

import com.employee.benefits.enrollment.service.EnrollmentEventPublisher;
import com.employee.benefits.enrollment.service.EnrollmentPublisherProperties;
import com.employee.benefits.enrollment.service.EventBridgeEnrollmentEventPublisher;
import com.employee.benefits.enrollment.service.HttpEnrollmentEventPublisher;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.runner.ApplicationContextRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

import static org.assertj.core.api.Assertions.assertThat;

class EnrollmentPublisherConfigTest {

    private final ApplicationContextRunner contextRunner = new ApplicationContextRunner()
            .withUserConfiguration(EnrollmentPublisherConfig.class, RestClientBuilderTestConfig.class);

    @Test
    void defaultsToHttpPublisher() {
        contextRunner.run(context -> {
            assertThat(context).hasSingleBean(EnrollmentEventPublisher.class);
            assertThat(context.getBean(EnrollmentEventPublisher.class)).isInstanceOf(HttpEnrollmentEventPublisher.class);
        });
    }

    @Test
    void switchesToEventBridgePublisherWhenConfigured() {
        contextRunner
                .withPropertyValues("app.publisher.transport=eventbridge")
                .run(context -> {
                    assertThat(context).hasSingleBean(EnrollmentEventPublisher.class);
                    assertThat(context.getBean(EnrollmentEventPublisher.class))
                            .isInstanceOf(EventBridgeEnrollmentEventPublisher.class);
                    assertThat(context.getBean(EnrollmentPublisherProperties.class).getTransport()).isEqualTo("eventbridge");
                });
    }

    @Configuration(proxyBeanMethods = false)
    static class RestClientBuilderTestConfig {

        @Bean
        RestClient.Builder restClientBuilder() {
            return RestClient.builder();
        }
    }
}
