# Use Node image for building
FROM node:20-slim

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

# Expose Vite port
EXPOSE 5173

# Run dev server with --host to allow Docker networking
CMD ["npm", "run", "dev", "--", "--host"]