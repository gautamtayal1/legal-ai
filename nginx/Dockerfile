FROM nginx:alpine

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy our nginx configuration
COPY nginx.conf /etc/nginx/conf.d/

# Create directory for static files
RUN mkdir -p /var/www/static

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]