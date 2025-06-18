FROM maven:3.9-amazoncorretto-21 AS build

WORKDIR /app

RUN yum install -y curl && yum clean all

COPY pom.xml .
COPY src src

RUN mvn dependency:go-offline -B
RUN mvn package -DskipTests

FROM amazoncorretto:21-alpine

WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8000

ENTRYPOINT ["java", "-jar", "app.jar"]