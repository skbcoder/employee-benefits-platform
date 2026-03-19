FROM maven:3.9.11-eclipse-temurin-17 AS build
WORKDIR /workspace

COPY pom.xml pom.xml
COPY services/shared-model/pom.xml services/shared-model/pom.xml
COPY services/enrollment-service/pom.xml services/enrollment-service/pom.xml
COPY services/shared-model/src services/shared-model/src
COPY services/enrollment-service/src services/enrollment-service/src

RUN mvn -N install \
    && mvn -f services/shared-model/pom.xml install -DskipTests \
    && mvn -f services/enrollment-service/pom.xml package -DskipTests

FROM eclipse-temurin:17-jre
WORKDIR /app

COPY --from=build /workspace/services/enrollment-service/target/enrollment-service-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
