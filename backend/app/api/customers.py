"""Customer API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.crm_service import CRMService

router = APIRouter()


@router.get("")
async def list_customers(db: AsyncSession = Depends(get_db)):
    """List all customers for the sidebar picker."""
    crm = CRMService(db)
    return await crm.get_all_customers()


@router.get("/{customer_id}")
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single customer with their orders."""
    crm = CRMService(db)
    customer = await crm.get_customer_by_id(customer_id)
    if not customer:
        return {"error": "Customer not found"}

    orders = await crm.get_customer_orders(customer_id)
    refund_history = await crm.get_all_refund_history(customer_id)

    return {
        **customer,
        "orders": orders,
        "refund_history": refund_history,
    }


@router.get("/{customer_id}/orders")
async def get_customer_orders(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Get all orders for a customer."""
    crm = CRMService(db)
    return await crm.get_customer_orders(customer_id)
