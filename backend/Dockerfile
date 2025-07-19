FROM maven:3.9-amazoncorretto-21 AS build

WORKDIR /app

RUN yum install -y curl && yum clean all

COPY settings.xml /root/.m2/settings.xml

COPY pom.xml .

RUN mvn dependency:go-offline -B --settings /root/.m2/settings.xml

COPY src src

RUN mvn package -DskipTests --settings /root/.m2/settings.xml

FROM amazoncorretto:21-alpine

WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8000

ENTRYPOINT ["java", "-jar", "app.jar"]