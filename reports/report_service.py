# services/report_service.py
from decimal import Decimal
from django.db.models import Sum, QuerySet
from inventory.models import Category, Product, Purchase, Supplier
from sales.models import Sales, SalesItems
from datetime import datetime
from typing import Dict, List, Optional

class ReportService:
    @staticmethod
    def get_sales_in_period(start_date: datetime, end_date: datetime) -> QuerySet[Sales]:
        """Get all sales within the specified period."""
        return Sales.objects.filter(date_added__range=[start_date, end_date])

    @staticmethod
    def get_purchases_in_period(start_date: datetime, end_date: datetime) -> QuerySet[Purchase]:
        """Get all purchases within the specified period."""
        return Purchase.objects.filter(purchase_at__range=[start_date, end_date])

    @staticmethod
    def calculate_total_amount(queryset: QuerySet, field_name: str) -> Decimal:
        """Calculate total amount from a queryset for a specific field."""
        return queryset.aggregate(total=Sum(field_name))['total'] or Decimal('0.00')

class FinancialReportService:
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
        self.report_service = ReportService()

    def get_supplier_expenses(self) -> List[Dict[str, Decimal | str]]:
        """Calculate expenses per supplier within the period."""
        supplier_expenses = []
        for supplier in Supplier.objects.all():
            supplier_purchases = Purchase.objects.filter(
                supplier=supplier,
                purchase_at__range=[self.start_date, self.end_date]
            )
            total_purchases = self.report_service.calculate_total_amount(supplier_purchases, 'total_amount')
            if total_purchases > 0:
                supplier_expenses.append({
                    'supplier': supplier.supplier_name,
                    'total_purchases': total_purchases
                })
        return supplier_expenses

    def get_category_sales(self) -> List[Dict[str, Decimal | str]]:
        """Calculate sales per category within the period."""
        category_sales = []
        for category in Category.objects.all():
            sales_items = SalesItems.objects.filter(
                product__category=category,
                sale__date_added__range=[self.start_date, self.end_date]
            )
            total_sales = self.report_service.calculate_total_amount(sales_items, 'total')
            if total_sales > 0:
                category_sales.append({
                    'category': category.name,
                    'total_sales': total_sales
                })
        return category_sales

    def get_product_sales(self) -> List[Dict[str, Decimal | str]]:
        """Calculate sales per product within the period."""
        product_sales = []
        for product in Product.objects.all():
            sales_items = SalesItems.objects.filter(
                product=product,
                sale__date_added__range=[self.start_date, self.end_date]
            )
            total_sales = self.report_service.calculate_total_amount(sales_items, 'total')
            if total_sales > 0:
                product_sales.append({
                    'product': product.product_name,
                    'total_sales': total_sales
                })
        return product_sales

    def generate_report(self) -> Dict[str, Decimal | List[Dict[str, Decimal | str]]]:
        """Generate complete financial report."""
        sales_data = self.report_service.get_sales_in_period(self.start_date, self.end_date)
        purchases_data = self.report_service.get_purchases_in_period(self.start_date, self.end_date)

        total_sales = self.report_service.calculate_total_amount(sales_data, 'grand_total')
        total_purchases = self.report_service.calculate_total_amount(purchases_data, 'total_amount')

        return {
            'total_sales': total_sales,
            'total_purchases': total_purchases,
            'supplier_expenses': self.get_supplier_expenses(),
            'category_sales': self.get_category_sales(),
            'product_sales': self.get_product_sales(),
            'profit_loss': total_sales - total_purchases
        }

class PerformanceReportService:
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
        self.report_service = ReportService()

    def generate_report(self) -> List[Dict[str, Decimal | str]]:
        """Generate product performance report."""
        performance_data = []
        for product in Product.objects.all():
            sales_items = SalesItems.objects.filter(
                product=product,
                sale__date_added__range=[self.start_date, self.end_date]
            )
            total_sales = self.report_service.calculate_total_amount(sales_items, 'total')
            if total_sales > 0:
                performance_data.append({
                    'product': product.product_name,
                    'total_sales': total_sales
                })
        return sorted(performance_data, key=lambda x: x['total_sales'], reverse=True)

