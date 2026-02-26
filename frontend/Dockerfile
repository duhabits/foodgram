FROM node:21.7.1-alpine

# Добавьте DNS настройки
RUN echo 'nameserver 8.8.8.8' > /etc/resolv.conf && \
    echo 'nameserver 8.8.4.4' >> /etc/resolv.conf

WORKDIR /app

COPY package*.json ./

# Увеличьте таймаут и используйте зеркало
RUN npm config set registry https://registry.npmmirror.com && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm install --legacy-peer-deps --verbose

COPY . ./

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]