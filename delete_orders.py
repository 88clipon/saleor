#!/usr/bin/env python
"""
Script to delete all orders and related data from Saleor database.
Run this with: python manage.py shell < delete_orders.py
"""
from saleor.order.models import Order
from saleor.payment.models import Payment, Transaction

# Count before deletion
order_count = Order.objects.count()
payment_count = Payment.objects.count()
transaction_count = Transaction.objects.count()

print(f"Found {order_count} orders, {payment_count} payments, and {transaction_count} transactions")
print("Deleting all orders and related data...")

# Delete in reverse dependency order:
# 1. Transactions (reference Payments)
# 2. Payments (reference Orders)
# 3. Orders

if transaction_count > 0:
    Transaction.objects.all().delete()
    print(f"✓ Deleted {transaction_count} transactions")

if payment_count > 0:
    Payment.objects.all().delete()
    print(f"✓ Deleted {payment_count} payments")

if order_count > 0:
    Order.objects.all().delete()
    print(f"✓ Deleted {order_count} orders")

print("\n✅ All orders and related data have been deleted!")
