# Case 5: BMKG Weather Dashboard (Microservices)

## Overview
This case demonstrates a robust Cloud-Native Microservices architecture using Docker Compose. It separates concerns into two distinct containers:
1.  **Backend**: A Python Flask application that proxies requests to the BMKG Public API and serves a location search endpoint using a local CSV dataset (`kodewilayah.csv`).
2.  **Frontend**: An Nginx server hosting a modern HTML/JS interface that consumes the backend API.

## Architecture
![Architecture](architecture.mermaid)

- **Frontend**: Exposed on Port 8080. Serves UI and reverse-proxies API calls.
- **Backend**: Hidden inside the Docker network (Port 5000). Handles data fetching and processing.
- **Data Source**: BMKG Public API (Real-time weather) and `kodewilayah.csv` (Location metadata).

## Why this scenario is important?
Unlike "Fat Containers" (Cases 1-4) which bundle everything into one OS, this approach:
- **Decouples** services: You can scale the backend independently of the frontend.
- **Improves Security**: The backend is not directly exposed to the public internet (except via the controlled Nginx proxy).
- **Simulates Production**: Real-world apps use orchestrators like Kubernetes or Compose, not single scripts.

## How to Run

1.  Ensure you have `docker` and `docker-compose` installed.
2.  Navigate to this directory:
    ```bash
    cd case5
    ```
3.  Start the services:
    ```bash
    docker-compose up -d --build
    ```
4.  Open your browser at: [http://localhost:8080](http://localhost:8080).
5.  Search for a location (e.g., "Surabaya", "Gubeng") and select it to view the forecast.

## API Endpoints
- `GET /api/locations?q={query}`: Search for location codes.
- `GET /api/weather?code={code}`: Get weather for a specific location.
