"""Database seeding script — 15 customer profiles with realistic order/refund data."""

import uuid
import json
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer, CustomerTier, AccountStatus
from app.models.product import Product, ProductCategory
from app.models.order import Order, OrderStatus
from app.models.refund import Refund, RefundStatus


def _id() -> str:
    return str(uuid.uuid4())


# ── Fixed IDs for referenceability ───────────────────────────────────────────

NOW = datetime.utcnow()


def _days_ago(days: int) -> datetime:
    return NOW - timedelta(days=days)


# ── Product Catalog ──────────────────────────────────────────────────────────

PRODUCTS = [
    Product(id=_id(), name="ProBook X1 Laptop", category=ProductCategory.LAPTOP, price=1299.99, is_digital=False, is_refundable=True, description="15-inch professional laptop with 16GB RAM"),
    Product(id=_id(), name="SoundWave Pro Headphones", category=ProductCategory.HEADPHONES, price=249.99, is_digital=False, is_refundable=True, description="Noise-cancelling wireless headphones"),
    Product(id=_id(), name="FitTrack Ultra Smartwatch", category=ProductCategory.SMARTWATCH, price=399.99, is_digital=False, is_refundable=True, description="Premium fitness smartwatch with GPS"),
    Product(id=_id(), name="USB-C Fast Charge Cable 6ft", category=ProductCategory.CABLE, price=19.99, is_digital=False, is_refundable=True, description="Braided USB-C to USB-C cable"),
    Product(id=_id(), name="DevStudio Pro License", category=ProductCategory.SOFTWARE, price=149.99, is_digital=True, is_refundable=False, description="Professional IDE software license — digital download"),
    Product(id=_id(), name="SlateView 11 Tablet", category=ProductCategory.TABLET, price=599.99, is_digital=False, is_refundable=True, description="11-inch tablet with stylus support"),
    Product(id=_id(), name="BassCore Bluetooth Speaker", category=ProductCategory.SPEAKER, price=89.99, is_digital=False, is_refundable=True, description="Portable waterproof Bluetooth speaker"),
    Product(id=_id(), name="PowerDock 65W Charger", category=ProductCategory.CHARGER, price=49.99, is_digital=False, is_refundable=True, description="65W GaN USB-C wall charger"),
    Product(id=_id(), name="ClearView 27\" Monitor", category=ProductCategory.MONITOR, price=449.99, is_digital=False, is_refundable=True, description="27-inch 4K IPS monitor"),
    Product(id=_id(), name="MechType Wireless Keyboard", category=ProductCategory.KEYBOARD, price=129.99, is_digital=False, is_refundable=True, description="Mechanical wireless keyboard with RGB"),
    Product(id=_id(), name="CloudSync Backup Software", category=ProductCategory.SOFTWARE, price=59.99, is_digital=True, is_refundable=False, description="Cloud backup software — annual license"),
    Product(id=_id(), name="EcoBuds Wireless Earbuds", category=ProductCategory.HEADPHONES, price=79.99, is_digital=False, is_refundable=True, description="Eco-friendly wireless earbuds"),
]


def _build_customers_and_orders():
    """Build all customer, order, and refund seed data."""
    customers = []
    orders = []
    refunds = []

    # ── Customer 1: Alice Johnson — VIP, clean record, standard approval ─────
    c1_id = _id()
    c1 = Customer(id=c1_id, name="Alice Johnson", email="alice.johnson@email.com", phone="+1-555-0101", tier=CustomerTier.VIP, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(730))
    customers.append(c1)

    o1_id = _id()
    orders.append(Order(id=o1_id, order_number="ORD-2025-001", customer_id=c1_id, product_id=PRODUCTS[0].id, quantity=1, unit_price=1299.99, total_price=1299.99, shipping_cost=0.0, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(15), delivered_at=_days_ago(12)))
    orders.append(Order(id=_id(), order_number="ORD-2025-002", customer_id=c1_id, product_id=PRODUCTS[1].id, quantity=1, unit_price=249.99, total_price=249.99, shipping_cost=9.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(60), delivered_at=_days_ago(55)))

    # ── Customer 2: Bob Martinez — Standard, 2 refunds this quarter ──────────
    c2_id = _id()
    c2 = Customer(id=c2_id, name="Bob Martinez", email="bob.martinez@email.com", phone="+1-555-0102", tier=CustomerTier.STANDARD, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(365))
    customers.append(c2)

    o3_id = _id()
    o4_id = _id()
    o5_id = _id()
    orders.append(Order(id=o3_id, order_number="ORD-2025-003", customer_id=c2_id, product_id=PRODUCTS[6].id, quantity=1, unit_price=89.99, total_price=89.99, shipping_cost=5.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(20), delivered_at=_days_ago(17)))
    orders.append(Order(id=o4_id, order_number="ORD-2025-004", customer_id=c2_id, product_id=PRODUCTS[3].id, quantity=2, unit_price=19.99, total_price=39.98, shipping_cost=3.99, status=OrderStatus.RETURNED, is_sale_item=False, ordered_at=_days_ago(50), delivered_at=_days_ago(47)))
    orders.append(Order(id=o5_id, order_number="ORD-2025-005", customer_id=c2_id, product_id=PRODUCTS[7].id, quantity=1, unit_price=49.99, total_price=49.99, shipping_cost=5.99, status=OrderStatus.RETURNED, is_sale_item=False, ordered_at=_days_ago(70), delivered_at=_days_ago(67)))

    # Bob has 2 past refunds in last 90 days
    refunds.append(Refund(id=_id(), customer_id=c2_id, order_id=o4_id, amount=39.98, reason="Cables were wrong length", status=RefundStatus.APPROVED, policy_rules_applied=json.dumps(["RULE_1", "RULE_2"]), agent_reasoning="Within return window, unused item", processed_at=_days_ago(45), created_at=_days_ago(45)))
    refunds.append(Refund(id=_id(), customer_id=c2_id, order_id=o5_id, amount=49.99, reason="Charger not compatible with my laptop", status=RefundStatus.APPROVED, policy_rules_applied=json.dumps(["RULE_1", "RULE_2"]), agent_reasoning="Within return window, unused item", processed_at=_days_ago(65), created_at=_days_ago(65)))

    # ── Customer 3: Carol Chen — Premium, digital product edge case ──────────
    c3_id = _id()
    c3 = Customer(id=c3_id, name="Carol Chen", email="carol.chen@email.com", phone="+1-555-0103", tier=CustomerTier.PREMIUM, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(500))
    customers.append(c3)

    o6_id = _id()
    orders.append(Order(id=o6_id, order_number="ORD-2025-006", customer_id=c3_id, product_id=PRODUCTS[4].id, quantity=1, unit_price=149.99, total_price=149.99, shipping_cost=0.0, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(10), delivered_at=_days_ago(10)))
    orders.append(Order(id=_id(), order_number="ORD-2025-007", customer_id=c3_id, product_id=PRODUCTS[8].id, quantity=1, unit_price=449.99, total_price=449.99, shipping_cost=14.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(30), delivered_at=_days_ago(26)))

    # ── Customer 4: David Kim — Standard, FLAGGED account ────────────────────
    c4_id = _id()
    c4 = Customer(id=c4_id, name="David Kim", email="david.kim@email.com", phone="+1-555-0104", tier=CustomerTier.STANDARD, account_status=AccountStatus.FLAGGED, joined_at=_days_ago(200))
    customers.append(c4)

    orders.append(Order(id=_id(), order_number="ORD-2025-008", customer_id=c4_id, product_id=PRODUCTS[2].id, quantity=1, unit_price=399.99, total_price=399.99, shipping_cost=0.0, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(8), delivered_at=_days_ago(5)))

    # ── Customer 5: Eva Petrova — VIP, 45 days ago (within VIP 60-day window) ─
    c5_id = _id()
    c5 = Customer(id=c5_id, name="Eva Petrova", email="eva.petrova@email.com", phone="+1-555-0105", tier=CustomerTier.VIP, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(900))
    customers.append(c5)

    orders.append(Order(id=_id(), order_number="ORD-2025-009", customer_id=c5_id, product_id=PRODUCTS[5].id, quantity=1, unit_price=599.99, total_price=599.99, shipping_cost=0.0, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(50), delivered_at=_days_ago(45)))
    orders.append(Order(id=_id(), order_number="ORD-2025-010", customer_id=c5_id, product_id=PRODUCTS[9].id, quantity=1, unit_price=129.99, total_price=129.99, shipping_cost=7.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(90), delivered_at=_days_ago(85)))

    # ── Customer 6: Frank Osei — Standard, order 35 days ago (outside 30-day) ─
    c6_id = _id()
    c6 = Customer(id=c6_id, name="Frank Osei", email="frank.osei@email.com", phone="+1-555-0106", tier=CustomerTier.STANDARD, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(180))
    customers.append(c6)

    orders.append(Order(id=_id(), order_number="ORD-2025-011", customer_id=c6_id, product_id=PRODUCTS[1].id, quantity=1, unit_price=249.99, total_price=249.99, shipping_cost=9.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(40), delivered_at=_days_ago(35)))

    # ── Customer 7: Grace Liu — Premium, bought sale/clearance item ──────────
    c7_id = _id()
    c7 = Customer(id=c7_id, name="Grace Liu", email="grace.liu@email.com", phone="+1-555-0107", tier=CustomerTier.PREMIUM, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(400))
    customers.append(c7)

    orders.append(Order(id=_id(), order_number="ORD-2025-012", customer_id=c7_id, product_id=PRODUCTS[11].id, quantity=1, unit_price=39.99, total_price=39.99, shipping_cost=4.99, status=OrderStatus.DELIVERED, is_sale_item=True, ordered_at=_days_ago(14), delivered_at=_days_ago(11)))
    orders.append(Order(id=_id(), order_number="ORD-2025-013", customer_id=c7_id, product_id=PRODUCTS[0].id, quantity=1, unit_price=1299.99, total_price=1299.99, shipping_cost=0.0, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(25), delivered_at=_days_ago(20)))

    # ── Customer 8: Henry Brown — Standard, SUSPENDED account ────────────────
    c8_id = _id()
    c8 = Customer(id=c8_id, name="Henry Brown", email="henry.brown@email.com", phone="+1-555-0108", tier=CustomerTier.STANDARD, account_status=AccountStatus.SUSPENDED, joined_at=_days_ago(300))
    customers.append(c8)

    orders.append(Order(id=_id(), order_number="ORD-2025-014", customer_id=c8_id, product_id=PRODUCTS[6].id, quantity=1, unit_price=89.99, total_price=89.99, shipping_cost=5.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(12), delivered_at=_days_ago(9)))

    # ── Customer 9: Irene Nakamura — VIP, 3 refunds this quarter (at limit) ──
    c9_id = _id()
    c9 = Customer(id=c9_id, name="Irene Nakamura", email="irene.nakamura@email.com", phone="+1-555-0109", tier=CustomerTier.VIP, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(600))
    customers.append(c9)

    o_irene_1 = _id()
    o_irene_2 = _id()
    o_irene_3 = _id()
    o_irene_4 = _id()
    orders.append(Order(id=o_irene_1, order_number="ORD-2025-015", customer_id=c9_id, product_id=PRODUCTS[3].id, quantity=3, unit_price=19.99, total_price=59.97, shipping_cost=3.99, status=OrderStatus.RETURNED, is_sale_item=False, ordered_at=_days_ago(80), delivered_at=_days_ago(75)))
    orders.append(Order(id=o_irene_2, order_number="ORD-2025-016", customer_id=c9_id, product_id=PRODUCTS[7].id, quantity=1, unit_price=49.99, total_price=49.99, shipping_cost=5.99, status=OrderStatus.RETURNED, is_sale_item=False, ordered_at=_days_ago(60), delivered_at=_days_ago(55)))
    orders.append(Order(id=o_irene_3, order_number="ORD-2025-017", customer_id=c9_id, product_id=PRODUCTS[11].id, quantity=1, unit_price=79.99, total_price=79.99, shipping_cost=4.99, status=OrderStatus.RETURNED, is_sale_item=False, ordered_at=_days_ago(40), delivered_at=_days_ago(35)))
    orders.append(Order(id=o_irene_4, order_number="ORD-2025-018", customer_id=c9_id, product_id=PRODUCTS[2].id, quantity=1, unit_price=399.99, total_price=399.99, shipping_cost=0.0, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(10), delivered_at=_days_ago(7)))

    # 3 refunds in last 90 days
    refunds.append(Refund(id=_id(), customer_id=c9_id, order_id=o_irene_1, amount=59.97, reason="Wrong cables ordered", status=RefundStatus.APPROVED, policy_rules_applied=json.dumps(["RULE_1"]), processed_at=_days_ago(70), created_at=_days_ago(70)))
    refunds.append(Refund(id=_id(), customer_id=c9_id, order_id=o_irene_2, amount=49.99, reason="Charger defective", status=RefundStatus.APPROVED, policy_rules_applied=json.dumps(["RULE_1"]), processed_at=_days_ago(50), created_at=_days_ago(50)))
    refunds.append(Refund(id=_id(), customer_id=c9_id, order_id=o_irene_3, amount=79.99, reason="Earbuds uncomfortable", status=RefundStatus.APPROVED, policy_rules_applied=json.dumps(["RULE_1"]), processed_at=_days_ago(30), created_at=_days_ago(30)))

    # ── Customer 10: James Wilson — Standard, clean record ───────────────────
    c10_id = _id()
    c10 = Customer(id=c10_id, name="James Wilson", email="james.wilson@email.com", phone="+1-555-0110", tier=CustomerTier.STANDARD, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(150))
    customers.append(c10)

    orders.append(Order(id=_id(), order_number="ORD-2025-019", customer_id=c10_id, product_id=PRODUCTS[9].id, quantity=1, unit_price=129.99, total_price=129.99, shipping_cost=7.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(10), delivered_at=_days_ago(7)))

    # ── Customer 11: Karen Patel — Premium, opened electronics (partial) ─────
    c11_id = _id()
    c11 = Customer(id=c11_id, name="Karen Patel", email="karen.patel@email.com", phone="+1-555-0111", tier=CustomerTier.PREMIUM, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(450))
    customers.append(c11)

    orders.append(Order(id=_id(), order_number="ORD-2025-020", customer_id=c11_id, product_id=PRODUCTS[1].id, quantity=1, unit_price=249.99, total_price=249.99, shipping_cost=9.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(18), delivered_at=_days_ago(14)))

    # ── Customer 12: Leo Fernandez — Standard, multiple orders ───────────────
    c12_id = _id()
    c12 = Customer(id=c12_id, name="Leo Fernandez", email="leo.fernandez@email.com", phone="+1-555-0112", tier=CustomerTier.STANDARD, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(250))
    customers.append(c12)

    orders.append(Order(id=_id(), order_number="ORD-2025-021", customer_id=c12_id, product_id=PRODUCTS[8].id, quantity=1, unit_price=449.99, total_price=449.99, shipping_cost=14.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(5), delivered_at=_days_ago(2)))
    orders.append(Order(id=_id(), order_number="ORD-2025-022", customer_id=c12_id, product_id=PRODUCTS[3].id, quantity=1, unit_price=19.99, total_price=19.99, shipping_cost=3.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(5), delivered_at=_days_ago(2)))
    orders.append(Order(id=_id(), order_number="ORD-2025-023", customer_id=c12_id, product_id=PRODUCTS[10].id, quantity=1, unit_price=59.99, total_price=59.99, shipping_cost=0.0, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(5), delivered_at=_days_ago(5)))

    # ── Customer 13: Maria Santos — VIP, high-value laptop return ────────────
    c13_id = _id()
    c13 = Customer(id=c13_id, name="Maria Santos", email="maria.santos@email.com", phone="+1-555-0113", tier=CustomerTier.VIP, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(1000))
    customers.append(c13)

    orders.append(Order(id=_id(), order_number="ORD-2025-024", customer_id=c13_id, product_id=PRODUCTS[0].id, quantity=1, unit_price=1299.99, total_price=1299.99, shipping_cost=0.0, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(7), delivered_at=_days_ago(4)))

    # ── Customer 14: Nathan Clark — Standard, wants shipping refund ──────────
    c14_id = _id()
    c14 = Customer(id=c14_id, name="Nathan Clark", email="nathan.clark@email.com", phone="+1-555-0114", tier=CustomerTier.STANDARD, account_status=AccountStatus.ACTIVE, joined_at=_days_ago(120))
    customers.append(c14)

    orders.append(Order(id=_id(), order_number="ORD-2025-025", customer_id=c14_id, product_id=PRODUCTS[7].id, quantity=1, unit_price=49.99, total_price=49.99, shipping_cost=12.99, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(8), delivered_at=_days_ago(5)))

    # ── Customer 15: Olivia Wright — Premium, FLAGGED + sale item ────────────
    c15_id = _id()
    c15 = Customer(id=c15_id, name="Olivia Wright", email="olivia.wright@email.com", phone="+1-555-0115", tier=CustomerTier.PREMIUM, account_status=AccountStatus.FLAGGED, joined_at=_days_ago(350))
    customers.append(c15)

    orders.append(Order(id=_id(), order_number="ORD-2025-026", customer_id=c15_id, product_id=PRODUCTS[6].id, quantity=1, unit_price=44.99, total_price=44.99, shipping_cost=4.99, status=OrderStatus.DELIVERED, is_sale_item=True, ordered_at=_days_ago(10), delivered_at=_days_ago(7)))
    orders.append(Order(id=_id(), order_number="ORD-2025-027", customer_id=c15_id, product_id=PRODUCTS[5].id, quantity=1, unit_price=599.99, total_price=599.99, shipping_cost=0.0, status=OrderStatus.DELIVERED, is_sale_item=False, ordered_at=_days_ago(20), delivered_at=_days_ago(16)))

    return customers, orders, refunds


async def seed_database(session: AsyncSession) -> None:
    """Seed the database if no customers exist yet."""
    result = await session.execute(select(Customer).limit(1))
    if result.scalar_one_or_none() is not None:
        return  # Already seeded

    print("[SEED] Seeding database...")

    # Seed products first
    for product in PRODUCTS:
        session.add(product)
    await session.flush()

    # Seed customers, orders, refunds
    customers, orders, refunds = _build_customers_and_orders()

    for customer in customers:
        session.add(customer)
    await session.flush()

    for order in orders:
        session.add(order)
    await session.flush()

    for refund in refunds:
        session.add(refund)

    await session.commit()
    print(f"[SEED] Seeded {len(customers)} customers, {len(PRODUCTS)} products, {len(orders)} orders, {len(refunds)} refunds")
