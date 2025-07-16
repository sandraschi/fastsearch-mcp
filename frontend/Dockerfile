# Frontend Dockerfile
# Use Node.js 18 with Alpine for smaller image size
FROM node:18.16.0-alpine AS build

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache python3 make g++

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies with legacy peer deps and verbose output
RUN npm config set loglevel verbose && \
    npm install --legacy-peer-deps --no-audit --prefer-offline --build-from-source

# Copy the rest of the application
COPY . .

# Create a basic tsconfig.json if it doesn't exist
RUN if [ ! -f tsconfig.json ]; then \
      echo '{"compilerOptions": {"target": "es5", "lib": ["dom", "dom.iterable", "esnext"], "allowJs": true, "skipLibCheck": true, "esModuleInterop": true, "allowSyntheticDefaultImports": true, "strict": true, "forceConsistentCasingInFileNames": true, "noFallthroughCasesInSwitch": true, "module": "esnext", "moduleResolution": "node", "resolveJsonModule": true, "isolatedModules": true, "noEmit": true, "jsx": "react-jsx"}, "include": ["src"]}' > tsconfig.json; \
    fi

# Build the application with production settings
ENV NODE_OPTIONS=--openssl-legacy-provider
ENV GENERATE_SOURCEMAP=true
ENV INLINE_RUNTIME_CHUNK=false
RUN npm run build -- --verbose

# Production stage
FROM nginx:1.23.4-alpine

# Copy built assets from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy healthcheck script
COPY healthcheck.sh /usr/share/nginx/html/

# Set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid && \
    # Add healthcheck
    chmod +x /usr/share/nginx/html/healthcheck.sh

# Use nginx user
USER nginx

# Expose port 3000 to match nginx.conf
EXPOSE 3000

# Simple healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
