# Development-focused Dockerfile for Notarius Web (Next.js)
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Create non-root user first
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy package files
COPY --chown=nextjs:nodejs package*.json ./

# Install dependencies (skip optional dependencies for faster build)
RUN npm install --no-optional --ignore-scripts

# Copy source code
COPY --chown=nextjs:nodejs . .

# Create .next directory with proper permissions
RUN mkdir -p .next && chown -R nextjs:nodejs .next

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:3000 || exit 1

# Default command for development
CMD ["npm", "run", "dev"]

