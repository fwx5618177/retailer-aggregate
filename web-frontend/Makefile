.PHONY: dev build preview lint type-check install clean docker-build docker-run

# Development server
dev:
	npm run dev

# Production build
build:
	npm run build

# Preview production build
preview:
	npm run preview

# Lint
lint:
	npm run lint

# Type check
type-check:
	npm run type-check

# Install dependencies
install:
	npm ci

# Clean build output
clean:
	rm -rf dist node_modules/.vite

# Docker build
docker-build:
	docker build -t sea-retailer-web .

# Docker run
docker-run:
	docker run --rm -p 3000:80 --name sea-retailer-web sea-retailer-web
