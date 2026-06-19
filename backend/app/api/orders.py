"""Order API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.crm_service import CRMService

router = APIRouter()


@router.get("/{order_id}")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """Get order details by ID or order number."""
    crm = CRMService(db)
    order = await crm.get_order_details(order_id)
    if not order:
        return {"error": "Order not found"}
    return order
