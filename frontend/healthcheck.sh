#!/bin/sh
# Simple healthcheck for the frontend container
# Exit with 0 if the application is running, non-zero otherwise

# Check if nginx is running
if ! pgrep nginx > /dev/null; then
  echo "Nginx is not running"
  exit 1
fi

# Check if the application is serving content (use IPv4 explicitly)
if ! wget --spider --timeout=5 --tries=1 http://127.0.0.1:3000/health 2>/dev/null; then
  echo "Application is not responding"
  exit 1
fi

exit 0
