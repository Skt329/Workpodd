"""Product catalog ORM model."""

import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, Float, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProductCategory(str, enum.Enum):
    LAPTOP = "LAPTOP"
    HEADPHONES = "HEADPHONES"
    SMARTWATCH = "SMARTWATCH"
    CABLE = "CABLE"
    SOFTWARE = "SOFTWARE"
    TABLET = "TABLET"
    SPEAKER = "SPEAKER"
    CHARGER = "CHARGER"
    MONITOR = "MONITOR"
    KEYBOARD = "KEYBOARD"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory), nullable=False
    )
    price: Mapped[float] = mapped_column(Float, nullable=False)
    is_digital: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_refundable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
