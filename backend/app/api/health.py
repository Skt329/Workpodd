"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Application health check."""
    return {"status": "healthy", "service": "ReturnShield AI Agent"}
