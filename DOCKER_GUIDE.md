# AI CFO Docker Guide

## 1. Prerequisites

1.  **Docker Desktop**: Installed and running.
2.  **`.env` file**: Create a `.env` file in the project root:
    ```
    GEMINI_API_KEY=your_gemini_key
    OPENAI_API_KEY=your_openai_key
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_ANON_KEY=your_supabase_anon_key
    TEST_EMAIL=your_test_email@example.com
    TEST_PASSWORD=your_test_password
    ```

## 2. Running the Application

**Option A: Development (Recommended)**
Uses `Dockerfile` and `docker-compose.yml`.

```powershell
# Build and Start
docker-compose up --build

# Stop
docker-compose down
```

**Option B: Production**
Uses `Dockerfile.prod` for an optimized build.

```powershell
# 1. Build Image
docker build -f Dockerfile.prod -t ai-cfo-prod .

# 2. Run Container
docker run -d --env-file .env -p 8000:8000 --name ai-cfo-prod-container ai-cfo-prod

# 3. Stop Container
docker stop ai-cfo-prod-container

# Optional: remove container after stopping
docker rm ai-cfo-prod-container
```

## 3. Accessing the App

- **API Docs**: `http://127.0.0.1:8000/docs`
- **Health Check**: `http://127.0.0.1:8000/health`
  _(Use `127.0.0.1` instead of `localhost` on Windows if you have issues)_

## 4. Other Useful Commands

**Docker Compose (Development):**

```powershell
# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f
# docker-compose logs -f ai-cfo-api # Specific service
```

**General Docker:**

```powershell
docker ps # List running containers
docker ps -a # List all containers
docker logs <container_name_or_id> # View logs
docker logs -f <container_name_or_id> # Follow logs
docker images # List images
docker rmi <image_name_or_id> # Remove image
```

## 5. Troubleshooting

- **Connection Issues (Windows):** Use `127.0.0.1` instead of `localhost`.
- **Port 8000 in use:** Ensure it's free on your host.
- **Errors?** Check logs: `docker-compose logs -f` (for dev) or `docker logs ai-cfo-prod-container` (for prod).
