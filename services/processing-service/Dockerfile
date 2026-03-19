FROM maven:3.9.11-eclipse-temurin-17 AS build
WORKDIR /workspace

COPY pom.xml pom.xml
COPY services/shared-model/pom.xml services/shared-model/pom.xml
COPY services/processing-service/pom.xml services/processing-service/pom.xml
COPY services/shared-model/src services/shared-model/src
COPY services/processing-service/src services/processing-service/src

RUN mvn -N install \
    && mvn -f services/shared-model/pom.xml install -DskipTests \
    && mvn -f services/processing-service/pom.xml package -DskipTests

FROM eclipse-temurin:17-jre
WORKDIR /app

COPY --from=build /workspace/services/processing-service/target/processing-service-0.0.1-SNAPSHOT.jar app.jar

EXPOSE 8081

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
