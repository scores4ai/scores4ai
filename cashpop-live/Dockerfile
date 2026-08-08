FROM mcr.microsoft.com/playwright:v1.54.2-noble
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
ENV PORT=3000
EXPOSE 3000
CMD ["npm","start"]
