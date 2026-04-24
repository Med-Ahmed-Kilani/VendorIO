#!/usr/bin/env python3
"""Load sample data into the database.

Usage:
    python scripts/load_sample_data.py                   # loads built-in synthetic data
    python scripts/load_sample_data.py --csv data/Online_Retail.csv  # loads Kaggle dataset
"""
import argparse
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db.database import SessionLocal
from backend.models import Product, Order, OrderItem, Customer
from backend.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger("load_sample_data")


PRODUCTS = [
    {"name": "Arabica Coffee Beans 1kg", "category": "Coffee", "unit_price": 24.99, "cost_per_unit": 9.50, "current_stock": 80, "lead_time_days": 7, "reorder_point": 20},
    {"name": "Green Tea 200g", "category": "Tea", "unit_price": 8.99, "cost_per_unit": 2.50, "current_stock": 5, "lead_time_days": 5, "reorder_point": 15},
    {"name": "Earl Grey 100 bags", "category": "Tea", "unit_price": 7.99, "cost_per_unit": 2.00, "current_stock": 40, "lead_time_days": 5, "reorder_point": 10},
    {"name": "Espresso Blend 500g", "category": "Coffee", "unit_price": 18.99, "cost_per_unit": 7.00, "current_stock": 60, "lead_time_days": 7, "reorder_point": 15},
    {"name": "Matcha Powder 50g", "category": "Tea", "unit_price": 14.99, "cost_per_unit": 5.00, "current_stock": 25, "lead_time_days": 7, "reorder_point": 10},
    {"name": "French Press 600ml", "category": "Equipment", "unit_price": 34.99, "cost_per_unit": 12.00, "current_stock": 15, "lead_time_days": 14, "reorder_point": 5},
    {"name": "Reusable Coffee Filter", "category": "Equipment", "unit_price": 9.99, "cost_per_unit": 3.00, "current_stock": 30, "lead_time_days": 7, "reorder_point": 10},
    {"name": "Cold Brew Bag Set (10pk)", "category": "Coffee", "unit_price": 12.99, "cost_per_unit": 4.50, "current_stock": 8, "lead_time_days": 7, "reorder_point": 10},
    {"name": "Herbal Chamomile 50 bags", "category": "Tea", "unit_price": 6.99, "cost_per_unit": 1.80, "current_stock": 200, "lead_time_days": 3, "reorder_point": 30},
    {"name": "Specialty Dark Roast 250g", "category": "Coffee", "unit_price": 16.99, "cost_per_unit": 6.50, "current_stock": 3, "lead_time_days": 7, "reorder_point": 10},
]

CUSTOMERS = [
    {"email": "alice@example.com", "total_spent": 450.00, "order_count": 8},
    {"email": "bob@example.com", "total_spent": 125.00, "order_count": 2},
    {"email": "charlie@example.com", "total_spent": 890.00, "order_count": 15},
    {"email": "diana@example.com", "total_spent": 55.00, "order_count": 1},
    {"email": "eve@example.com", "total_spent": 320.00, "order_count": 5},
]


def load_synthetic(db) -> None:
    logger.info("Loading synthetic sample data...")

    # Products
    products = []
    for p_data in PRODUCTS:
        existing = db.query(Product).filter(Product.name == p_data["name"]).first()
        if not existing:
            p = Product(**p_data)
            db.add(p)
            products.append(p)
        else:
            products.append(existing)
    db.flush()

    # Customers
    customers = []
    from datetime import date
    for idx, c_data in enumerate(CUSTOMERS):
        existing = db.query(Customer).filter(Customer.email == c_data["email"]).first()
        if not existing:
            c = Customer(
                **c_data,
                first_order_date=date(2023, 6 + idx, 1),
            )
            db.add(c)
            customers.append(c)
        else:
            customers.append(existing)
    db.flush()

    # Generate 180 days of orders
    order_count = 0
    for days_ago in range(180, 0, -1):
        order_date = datetime.utcnow() - timedelta(days=days_ago)
        # 2-5 orders per day
        daily_orders = random.randint(2, 5)
        for _ in range(daily_orders):
            customer = random.choice(customers)
            order = Order(
                order_date=order_date + timedelta(hours=random.randint(8, 20)),
                customer_id=customer.id,
                status="completed",
            )
            db.add(order)
            db.flush()

            # 1-3 items per order
            selected_products = random.sample(products, min(random.randint(1, 3), len(products)))
            total = 0.0
            for product in selected_products:
                qty = random.randint(1, 5)
                price = float(product.unit_price)
                line_total = qty * price
                total += line_total
                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=price,
                    line_total=round(line_total, 2),
                )
                db.add(item)
            order.total_amount = round(total, 2)
            order_count += 1

    db.commit()
    logger.info(f"✅ Loaded {len(products)} products, {len(customers)} customers, {order_count} orders")


def load_from_csv(db, csv_path: str) -> None:
    """Load from Kaggle Online Retail CSV."""
    from models.utils.data_loader import load_from_csv as load_csv
    logger.info(f"Loading from CSV: {csv_path}")
    df = load_csv(csv_path)

    # Map stock codes to products
    stock_codes = df["StockCode"].value_counts().head(20).index.tolist()
    description_map = df.groupby("StockCode")["Description"].first()
    price_map = df.groupby("StockCode")["UnitPrice"].mean()

    products = {}
    for code in stock_codes:
        name = str(description_map.get(code, code))[:255]
        price = float(price_map.get(code, 9.99))
        p = Product(
            name=name,
            category="Imported",
            unit_price=round(price, 2),
            cost_per_unit=round(price * 0.4, 2),
            current_stock=random.randint(10, 200),
            lead_time_days=7,
        )
        db.add(p)
        db.flush()
        products[code] = p

    # Load orders from CSV
    import pandas as pd
    df["date"] = df["InvoiceDate"].dt.date
    by_invoice = df.groupby("InvoiceNo")

    order_count = 0
    for invoice_no, group in list(by_invoice)[:500]:
        order_date = pd.to_datetime(group["InvoiceDate"].iloc[0])
        order = Order(order_date=order_date, status="completed")
        db.add(order)
        db.flush()
        total = 0.0
        for _, row in group.iterrows():
            code = row["StockCode"]
            if code not in products:
                continue
            qty = int(row["Quantity"])
            price = float(row["UnitPrice"])
            line = qty * price
            total += line
            item = OrderItem(
                order_id=order.id,
                product_id=products[code].id,
                quantity=qty,
                unit_price=round(price, 2),
                line_total=round(line, 2),
            )
            db.add(item)
        order.total_amount = round(total, 2)
        order_count += 1

    db.commit()
    logger.info(f"✅ Loaded {len(products)} products and {order_count} orders from CSV")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", help="Path to Online Retail CSV", default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.csv:
            load_from_csv(db, args.csv)
        else:
            load_synthetic(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
