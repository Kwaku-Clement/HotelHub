from decimal import Decimal
from django.db.models import Sum, QuerySet, Q
from inventory.models import Category, Product, Purchase, Supplier, InventoryMiscellaneous
from sales.models import Sales, SalesItems
from reservations.models import Reservation
from datetime import datetime
from typing import Dict, List, Any


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
    def get_reservations_in_period(start_date: datetime, end_date: datetime) -> QuerySet[Reservation]:
        """Get all reservations within the specified period."""
        return Reservation.objects.filter(reservation_date__range=[start_date, end_date])

    @staticmethod
    def calculate_total_amount(queryset: QuerySet, field_name: str) -> float:
        """Calculate total amount from a queryset for a specific field."""
        total = queryset.aggregate(total=Sum(field_name))['total']
        return float(total) if total else 0.0

    @staticmethod
    def get_miscellaneous_expenses(start_date: datetime, end_date: datetime) -> float:
        """Calculate total miscellaneous expenses within the period."""
        expenses = InventoryMiscellaneous.objects.filter(date__range=[start_date, end_date])
        total = expenses.aggregate(total=Sum('amount'))['total']
        return float(total) if total else 0.0

import logging

logger = logging.getLogger(__name__)

class ReservationReportService:
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
        self.report_service = ReportService()
        logger.info(f"Initializing ReservationReportService for period: {start_date} - {end_date}")

    def get_top_reservations(self) -> List[Dict[str, Any]]:
        """Get top reservations within the period."""
        try:
            reservations = self.report_service.get_reservations_in_period(self.start_date, self.end_date)
            top_reservations = reservations.order_by('-grand_total')[:5]
            logger.info(f"Top reservations fetched: {top_reservations.count()} records")
            return [
                {
                    'reservation_id': reservation.id,
                    'guest_name': reservation.guest.get_full_name,
                    'grand_total': float(reservation.grand_total)
                }
                for reservation in top_reservations
            ]
        except Exception as e:
            logger.error(f"Error fetching top reservations: {e}")
            return []

    def get_top_guests(self) -> List[Dict[str, Any]]:
        """Get top guests by total reservation amount within the period."""
        from reservations.models import Guest
        try:
            top_guests = Guest.objects.annotate(
                total_reservations=Sum(
                    'reservation__grand_total',
                    filter=Q(reservation__reservation_date__range=[self.start_date, self.end_date])
                )
            ).order_by('-total_reservations')[:5]
            logger.info(f"Top guests fetched: {top_guests.count()} records")
            return [
                {
                    'guest_name': guest.get_full_name,
                    'total_reservations': float(guest.total_reservations or 0.0)
                }
                for guest in top_guests
            ]
        except Exception as e:
            logger.error(f"Error fetching top guests: {e}")
            return []

    def generate_report(self) -> Dict[str, Any]:
        """Generate reservation report."""
        try:
            reservations = self.report_service.get_reservations_in_period(self.start_date, self.end_date)
            total_reservation_revenue = self.report_service.calculate_total_amount(reservations, 'grand_total')
            total_miscellaneous = self.report_service.get_miscellaneous_expenses(self.start_date, self.end_date)

            logger.info(f"Report generated with total revenue: {total_reservation_revenue}, "
                        f"total miscellaneous: {total_miscellaneous}")

            return {
                'total_reservation_revenue': total_reservation_revenue,
                'total_miscellaneous': total_miscellaneous,
                'net_reservation_revenue': total_reservation_revenue - total_miscellaneous,
                'reservations': reservations,
                'top_reservations': self.get_top_reservations(),
                'top_guests': self.get_top_guests()
            }
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {}

class StoreReportService:
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
        self.report_service = ReportService()

    def get_supplier_expenses(self) -> List[Dict[str, Any]]:
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

    def get_category_sales(self) -> List[Dict[str, Any]]:
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

    def get_product_sales(self) -> List[Dict[str, Any]]:
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

    def generate_report(self) -> Dict[str, Any]:
        """Generate complete financial report."""
        sales_data = self.report_service.get_sales_in_period(self.start_date, self.end_date)
        purchases_data = self.report_service.get_purchases_in_period(self.start_date, self.end_date)

        total_sales = self.report_service.calculate_total_amount(sales_data, 'grand_total')
        total_purchases = self.report_service.calculate_total_amount(purchases_data, 'total_amount')
        total_miscellaneous = self.report_service.get_miscellaneous_expenses(self.start_date, self.end_date)

        return {
            'total_sales': total_sales,
            'total_purchases': total_purchases,
            'total_miscellaneous': total_miscellaneous,
            'supplier_expenses': self.get_supplier_expenses(),
            'category_sales': self.get_category_sales(),
            'product_sales': self.get_product_sales(),
            'profit_loss': total_sales - (total_purchases + total_miscellaneous)
        }
