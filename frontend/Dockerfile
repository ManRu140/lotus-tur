# Dockerfile для frontend (статика через nginx)
FROM nginx:alpine

# Копируем статические файлы
COPY . /usr/share/nginx/html/

# Копируем nginx конфиг
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Railway передаёт $PORT через переменную окружения
# nginx:alpine поддерживает envsubst через /docker-entrypoint.d/
# шаблон default.conf.template автоматически обработается при старте

EXPOSE $PORT

CMD ["nginx", "-g", "daemon off;"]
