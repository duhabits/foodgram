# Этап сборки
FROM node:18-alpine as build

WORKDIR /app

# Копируем файлы зависимостей
COPY package*.json ./

# Устанавливаем зависимости с флагом legacy-peer-deps
RUN npm install --legacy-peer-deps

# Копируем исходный код
COPY . .

# Собираем проект
RUN npm run build

# Финальный этап - используем alpine, но только для копирования
FROM alpine:latest as static

# Копируем собранные файлы из этапа сборки
COPY --from=build /app/build /build

# Не нужно запускать никакой процесс, просто храним статику