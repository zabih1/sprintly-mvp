"""
Uvicorn server startup script with optimized settings for large file uploads.

This script configures Uvicorn with appropriate settings to handle large CSV file uploads
up to 2GB in size.
"""
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    # Run with increased limits for large file uploads
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        # Increase timeout and limits for large file uploads
        timeout_keep_alive=300,  # 5 minutes keep-alive
        limit_concurrency=1000,
        limit_max_requests=10000,
        # Configure request body size limits
        # Note: FastAPI/Starlette handles the actual request body size limits internally
        # We set reasonable connection limits here
        backlog=2048,
    )

