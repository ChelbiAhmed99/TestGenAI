FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Use development server for local testing with hot-reload, 
# or build for production in a real deployment
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
