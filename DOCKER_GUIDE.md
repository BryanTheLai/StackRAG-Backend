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
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/docs (via healthcheck)
- API Endpoints: http://localhost:8000/

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
- Ensure port 8000 is not in use by another application
- Verify your `.env` file exists and contains all required variables
- Check Docker Desktop is running
- Use `docker-compose logs` to view application logs
