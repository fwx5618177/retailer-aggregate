.PHONY: build test run clean docker-build docker-run

build:
	./mvnw clean package -DskipTests

test:
	./mvnw test

run:
	./mvnw spring-boot:run -Dspring-boot.run.profiles=local

clean:
	./mvnw clean

docker-build:
	docker build -t sea-retailer-api:latest .

docker-run:
	docker run --rm -p 8080:8080 \
		-e POSTGRES_USER=sea_retailer \
		-e POSTGRES_PASSWORD=changeme \
		-e CH_URL=jdbc:ch://host.docker.internal:8123/sea_retailer \
		sea-retailer-api:latest
