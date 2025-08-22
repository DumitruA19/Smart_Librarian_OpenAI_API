# frontend/Dockerfile
FROM mcr.microsoft.com/devcontainers/javascript-node:18

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# API-ul va fi prin Ingress: http://smartlib.localtest.me/api
ARG VITE_API_BASE_URL=http://smartlib.localtest.me/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build && npm i -g serve
EXPOSE 80
CMD ["serve","-s","dist","-l","80"]
