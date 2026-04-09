FROM node:14-bullseye AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-bookworm
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    auto-multiple-choice \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-lang-other \
    dvipdfmx \
    libdbd-sqlite3-perl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/ backend/
COPY --from=frontend-builder /app/frontend/build /app/backend/static

RUN pip install --no-cache-dir -r backend/requirements.txt

WORKDIR /app/backend

RUN mkdir -p /app/backend/data && chmod -R 777 /app/backend/data
RUN mkdir -p /tmp && chmod -R 777 /tmp

RUN sed -i 's/rights="none"/rights="read|write"/g' /etc/ImageMagick-6/policy.xml
RUN sed -i "s/my \$code_digit_pattern = \$layout->code_digit_pattern();/my \$code_digit_pattern = '[\\\\.\\\\[]([0-9]+)\\\\]?';/" /usr/libexec/AMC/perl/AMC-note.pl


CMD ["python", "-u", "entrypoint.py"]