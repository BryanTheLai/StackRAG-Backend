# AI CFO Docker Setup and Usage Guide

## Files Created
- `Dockerfile` - Development Docker configuration
- `Dockerfile.prod` - Production-optimized multi-stage build
- `docker-compose.yml` - Docker Compose configuration
- `.dockerignore` - Files to exclude from Docker build context

## Prerequisites
1. Install Docker Desktop for Windows
2. Ensure you have a `.env` file with your environment variables

## Development Usage

### Build and Run with Docker
```powershell
# Build the Docker image
docker build -t ai-cfo-fyp .

# Run the container
docker run --env-file .env -p 8000:8000 ai-cfo-fyp
```

### Using Docker Compose (Recommended)
```powershell
# Start the application
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

## Production Usage

### Build Production Image
```powershell
# Build production image
docker build -f Dockerfile.prod -t ai-cfo-fyp:prod .

# Run production container
docker run --env-file .env -p 8000:8000 ai-cfo-fyp:prod
```

## Environment Variables
Make sure your `.env` file contains:
```
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
TEST_EMAIL=your_test_email@gmail.com
TEST_PASSWORD=your_test_password
```

## Access the Application
- API Root: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- API Endpoints: Generally accessed via `http://127.0.0.1:8000/` followed by the specific endpoint path.

**Note on `localhost` vs. `127.0.0.1` on Windows:**
If `http://localhost:8000` gives you an "empty response" or connection error in your browser, **try `http://127.0.0.1:8000` instead**. This is often more reliable for Docker port mappings on Windows.

## Docker Commands Reference
```powershell
# View running containers
docker ps

# View logs
docker logs <container_id>

# Stop a container
docker stop <container_id>

# Remove containers and images
docker-compose down --rmi all

# Build without cache
docker build --no-cache -t ai-cfo-fyp .
```

## Troubleshooting
- **`ERR_EMPTY_RESPONSE` or Connection Issues in Browser (on Windows):**
    - **Try `127.0.0.1` instead of `localhost`**: Access `http://127.0.0.1:8000/...` in your browser.
- Ensure port 8000 is not in use by another application on your host machine.
- Verify your `.env` file exists in the project root and contains all required variables with correct values.
- Check Docker Desktop is running.
- Use `docker-compose logs -f` (or `docker logs <container_id>`) to view application logs for errors.
- **Healthcheck Fails:** The healthcheck in `Dockerfile` and `docker-compose.yml` uses `curl http://localhost:8000/health`. This `localhost` is *inside* the container. If it fails, it means the app inside the container isn't responding correctly at its `/health` endpoint. Check application logs (`docker-compose logs -f ai-cfo-api`).
