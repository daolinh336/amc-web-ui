FROM node:14-bullseye AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.9-bullseye
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    auto-multiple-choice \
    texlive-fonts-recommended \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/ backend/
COPY --from=frontend-builder /app/frontend/build /app/backend/static

RUN pip install --no-cache-dir -r backend/requirements.txt

WORKDIR /app/backend
CMD ["python", "entrypoint.py"]