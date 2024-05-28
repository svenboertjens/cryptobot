# Use the nginx image
FROM nginx:latest

RUN mkdir -p /etc/nginx/keys

WORKDIR /etc/nginx/keys

# Generate ssl certificate and key
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt -subj "/CN=localhost"

# Copy config file
COPY nginx.conf /etc/nginx/nginx.conf