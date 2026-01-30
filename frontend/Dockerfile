# Multi-stage build for Vite React app – production stage uses Node only (no nginx)
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Exclude server.js from the build context affecting source (e.g. if in .dockerignore we'd skip it for builder; we need it only in runner)
RUN npm run build

# Production: serve static files and proxy /api, /health using Node (avoids pulling nginx when registry has issues)
FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production
ENV PORT=80
ENV BACKEND_URL=http://backend:8000

COPY --from=builder /app/dist ./dist
COPY server.js ./

EXPOSE 80
CMD ["node", "server.js"]
