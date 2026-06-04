FROM node:20-alpine AS base

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
COPY THIRD_PARTY_NOTICES.txt /usr/share/jpilot/THIRD_PARTY_NOTICES.txt

EXPOSE 5173

FROM base AS dev
# package.json is bind-mounted in dev; install so new deps (e.g. qrcode) land in node_modules
CMD ["sh", "-c", "npm install && npm run dev"]
