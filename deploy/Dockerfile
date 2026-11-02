# Bundeshaushaltstracker als statische Seite: Web-Build (Vite) plus die Daten aus data/build, ausgeliefert von nginx.
# Kontext ist das Repository-Wurzelverzeichnis (siehe docker-compose.yml). Keine Pipeline, keine Rohdaten im Image.

FROM node:22-alpine AS build
WORKDIR /src
COPY web/package.json web/package-lock.json ./web/
RUN cd web && npm ci --no-audit --no-fund
COPY web/ ./web/
COPY data/build/ ./data/build/
RUN cd web && npm run build

FROM nginx:1.27-alpine
COPY deploy/nginx.local.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/web/dist/ /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
