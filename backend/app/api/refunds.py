"""Refund API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.refund_service import RefundService

router = APIRouter()


@router.get("")
async def list_refunds(db: AsyncSession = Depends(get_db)):
    """List all refund records."""
    svc = RefundService(db)
    return await svc.get_all_refunds()


@router.get("/stats")
async def refund_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate refund statistics for the admin dashboard."""
    svc = RefundService(db)
    return await svc.get_stats()
