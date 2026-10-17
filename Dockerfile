# One public service: the Python API serves the built UI from the same origin (no CORS, one URL).
FROM node:22-slim AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY ui/ ./
# Demo mode (in-memory fictional data, no sign-in); empty engine URL = same origin.
RUN VITE_DEMO_MEMORY=1 VITE_ENGINE_URL= npx vite build

FROM python:3.12-slim
WORKDIR /app
COPY src ./src
COPY eval ./eval
COPY tests/fixtures ./tests/fixtures
COPY --from=ui /ui/dist ./ui/dist
ENV COACH_HOST=0.0.0.0 COACH_STATIC_DIR=/app/ui/dist
# No COACH_CLASSIFIER_DIR here on purpose: the public service has no weights and no local evaluation summary.
CMD ["python", "-m", "src.api"]
