package com.employee.benefits.processing.config;

import com.employee.benefits.processing.service.EnrollmentStatusCallback;
import com.employee.benefits.processing.service.HttpEnrollmentStatusCallback;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class CallbackConfig {

    @Bean
    EnrollmentStatusCallback enrollmentStatusCallback(
            RestClient.Builder builder,
            @Value("${app.callback.enrollment-service-url:http://localhost:8080}") String enrollmentServiceUrl
    ) {
        RestClient restClient = builder.baseUrl(enrollmentServiceUrl).build();
        return new HttpEnrollmentStatusCallback(restClient);
    }
}
