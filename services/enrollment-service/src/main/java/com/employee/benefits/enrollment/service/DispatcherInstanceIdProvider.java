package com.employee.benefits.enrollment.service;

import org.springframework.stereotype.Component;

import java.net.InetAddress;
import java.net.UnknownHostException;
import java.util.UUID;

@Component
public class DispatcherInstanceIdProvider {

    private final String instanceId = resolveHostName() + "-" + UUID.randomUUID();

    public String getInstanceId() {
        return instanceId;
    }

    private static String resolveHostName() {
        try {
            return InetAddress.getLocalHost().getHostName();
        } catch (UnknownHostException exception) {
            return "enrollment-dispatcher";
        }
    }
}
