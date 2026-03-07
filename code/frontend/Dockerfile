# Dockerfile for Bingo Market Frontend (Multi-stage build)

# Build stage
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Set npm registry to mirror for faster builds
RUN npm config set registry https://registry.npmmirror.com

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Set working directory
WORKDIR /usr/share/nginx/html

# Copy built assets from builder stage
COPY --from=builder /app/dist .

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
