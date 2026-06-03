FROM node:20-alpine

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
COPY THIRD_PARTY_NOTICES.txt /usr/share/jpilot/THIRD_PARTY_NOTICES.txt

EXPOSE 5173

CMD ["npm", "run", "dev"]
