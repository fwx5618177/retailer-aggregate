# SEA Retailer Web Frontend

React 19 + TypeScript + Vite application for the SEA Retailer Top Selling Intelligence platform.

## Quick Start

```bash
# Install dependencies
npm ci

# Start dev server (port 3000, proxies /api to localhost:8080)
npm run dev

# Type check
npm run type-check

# Production build
npm run build

# Preview production build
npm run preview
```

## Docker

```bash
docker build -t sea-retailer-web .
docker run --rm -p 3000:80 sea-retailer-web
```

## Tech Stack

- React 19, TypeScript 5.7, Vite 6
- TanStack React Query for data fetching
- Zustand for filter state management
- Recharts for charts
- Tailwind CSS 4 for styling
- React Router v7
- Axios HTTP client
