from datetime import datetime
from decimal import Decimal
import logging
from time import timezone
from typing import Dict, Any, Optional, Tuple

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from reports.report_service import ReservationReportService, StoreReportService
from reservations.models import Reservation, ReservationDetail
from .forms import ReportSelectionForm
from inventory.models import InventoryMiscellaneous
import logging

logger = logging.getLogger(__name__)

# Constants
ITEMS_PER_PAGE = 20
DEFAULT_REPORT_TYPE = 'store'

class DateRangeError(ValidationError):
    """Custom exception for date range validation errors."""
    pass

def validate_date_range(start_date: str, end_date: str) -> Tuple[datetime, datetime]:
    """
    Validate and convert date strings to datetime objects.
    
    Args:
        start_date: Start date string in YYYY-MM-DD format
        end_date: End date string in YYYY-MM-DD format
        
    Returns:
        Tuple of datetime objects (start_datetime, end_datetime)
        
    Raises:
        DateRangeError: If dates are invalid or end_date is before start_date
    """
    try:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        
        if end_datetime < start_datetime:
            raise DateRangeError("End date must be after start date")
            
        return start_datetime, end_datetime
    except ValueError as e:
        raise DateRangeError(f"Invalid date format: {str(e)}")

def get_default_date_range() -> Tuple[str, str]:
    """
    Get default date range (current month).
    
    Returns:
        Tuple of strings (start_date, end_date) in YYYY-MM-DD format
    """
    today = datetime.now()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    return start_date, end_date

def generate_store_explanation(
    total_revenue: float,
    total_expenses: float,
    profit_loss: float,
    report_data: Dict[str, Any]
) -> str:
    """
    Generate a detailed explanation of the store's financial performance.
    """
    margin = (profit_loss / total_revenue * 100) if total_revenue > 0 else 0
    expense_ratio = (total_expenses / total_revenue * 100) if total_revenue > 0 else 0

    category_sales = sorted(
        report_data.get('category_sales', []),
        key=lambda x: x['total_sales'],
        reverse=True
    )[:5]
    
    product_sales = sorted(
        report_data.get('product_sales', []),
        key=lambda x: x['total_sales'],
        reverse=True
    )[:5]
    
    supplier_expenses = sorted(
        report_data.get('supplier_expenses', []),
        key=lambda x: x['total_purchases'],
        reverse=True
    )[:3]

    explanation_parts = []

    # Overall Performance
    if profit_loss >= 0:
        explanation_parts.append(
            f"The financial report shows a positive performance with a profit of ${profit_loss:,.2f}, "
            f"representing a profit margin of {margin:.1f}%. "
            f"Total revenue of ${total_revenue:,.2f} exceeded total expenses of ${total_expenses:,.2f}."
        )
    else:
        explanation_parts.append(
            f"The financial report indicates challenges with a loss of ${abs(profit_loss):,.2f}, "
            f"representing a negative margin of {abs(margin):.1f}%. "
            f"Total expenses of ${total_expenses:,.2f} exceeded revenue of ${total_revenue:,.2f}."
        )

    # Category Analysis
    if category_sales:
        explanation_parts.append("\nTop Performing Categories:")
        for category in category_sales:
            explanation_parts.append(f"- {category['category']}: ${category['total_sales']:,.2f}")

    # Product Analysis
    if product_sales:
        explanation_parts.append("\nTop Performing Products:")
        for product in product_sales:
            explanation_parts.append(f"- {product['product']}: ${product['total_sales']:,.2f}")

    # Supplier Analysis
    if supplier_expenses:
        explanation_parts.append("\nTop Suppliers by Expense:")
        for supplier in supplier_expenses:
            explanation_parts.append(f"- {supplier['supplier']}: ${supplier['total_purchases']:,.2f}")

    return "\n".join(explanation_parts)

def generate_reservation_explanation(
    total_reservation_revenue: Decimal,
    total_miscellaneous: Decimal,
    net_reservation_revenue: Decimal,
    report_data: Dict[str, Any]
) -> str:
    """
    Generate a detailed explanation of the reservation report.
    """
    margin = (net_reservation_revenue / total_reservation_revenue * 100) if total_reservation_revenue > 0 else 0
    expense_ratio = (total_miscellaneous / total_reservation_revenue * 100) if total_reservation_revenue > 0 else 0

    top_reservations = report_data.get('top_reservations', [])
    top_guests = report_data.get('top_guests', [])

    explanation_parts = []

    # Overall Performance
    if net_reservation_revenue >= 0:
        explanation_parts.append(
            f"The reservation report shows a positive performance with a net revenue of ${net_reservation_revenue:,.2f}, "
            f"representing a margin of {margin:.1f}%. "
            f"Total reservation revenue of ${total_reservation_revenue:,.2f} exceeded total miscellaneous expenses of ${total_miscellaneous:,.2f}, "
            f"with an expense ratio of {expense_ratio:.1f}%."
        )
    else:
        explanation_parts.append(
            f"The reservation report indicates challenges with a net loss of ${abs(net_reservation_revenue):,.2f}, "
            f"representing a negative margin of {abs(margin):.1f}%. "
            f"Total miscellaneous expenses of ${total_miscellaneous:,.2f} exceeded reservation revenue of ${total_reservation_revenue:,.2f}, "
            f"with an expense ratio of {expense_ratio:.1f}%."
        )

    # Top Reservations
    if top_reservations:
        explanation_parts.append("\nTop Reservations:")
        for reservation in top_reservations:
            explanation_parts.append(f"- Reservation ID: {reservation['reservation_id']}, Guest: {reservation['guest_name']}, Total: ${reservation['grand_total']:,.2f}")

    # Top Guests
    if top_guests:
        explanation_parts.append("\nTop guests by Reservation Amount:")
        for guest in top_guests:
            explanation_parts.append(f"- Guest: {guest['guest_name']}, Total Reservations: ${guest['total_reservations']:,.2f}")

    return "\n".join(explanation_parts)

@login_required
@require_http_methods(["GET", "POST"])
def generate_report(request: HttpRequest) -> HttpResponse:
    """
    View for selecting and generating reports.
    """
    if request.method == "POST":
        form = ReportSelectionForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            return redirect(
                f'reports:{report_type}_report_with_date',
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
    else:
        form = ReportSelectionForm(initial={'report_type': DEFAULT_REPORT_TYPE})
    
    return render(
        request,
        'select_report.html',
        {'form': form}
    )

# Updated methods to convert Decimal values to float
def generate_store_report(
    request: HttpRequest,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> HttpResponse:
    """
    Generate and display store financial report with floats.
    """
    try:
        if start_date is None or end_date is None:
            start_date, end_date = get_default_date_range()

        start_datetime, end_datetime = validate_date_range(start_date, end_date)

        # Generate report data
        service = StoreReportService(start_datetime, end_datetime)
        report_data = service.generate_report()

        # Convert Decimal values to float
        total_revenue = float(report_data['total_sales'])
        total_expenses = float(report_data['total_purchases']) + float(report_data['total_miscellaneous'])
        profit_loss = total_revenue - total_expenses

        # Get miscellaneous expenses
        misc_expenses = InventoryMiscellaneous.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('-date')

        # Paginate miscellaneous expenses
        paginator = Paginator(misc_expenses, ITEMS_PER_PAGE)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'report_data': report_data,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'profit_loss': profit_loss,
            'store_name': 'Store Report',
            'selected_date_range': f"{start_date} to {end_date}",
            'total_miscellaneous': float(report_data['total_miscellaneous']),
            'misc_expenses_page': page_obj,
            'explanation': generate_store_explanation(
                total_revenue,
                total_expenses,
                profit_loss,
                report_data
            ),
            'category_sales': sorted(
                report_data['category_sales'],
                key=lambda x: x['total_sales'],
                reverse=True
            )[:5],
            'product_sales': sorted(
                report_data['product_sales'],
                key=lambda x: x['total_sales'],
                reverse=True
            )[:5],
            'supplier_expenses': sorted(
                report_data['supplier_expenses'],
                key=lambda x: x['total_purchases'],
                reverse=True
            )[:3]
        }

        return render(request, 'store_report.html', context)

    except DateRangeError as e:
        messages.error(request, str(e))
        return redirect('reports:select_report')
    except Exception as e:
        messages.error(request, f"An error occurred while generating the report: {str(e)}")
        return redirect('reports:select_report')
    
@login_required
def generate_reservation_report(
    request: HttpRequest,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> HttpResponse:
    """
    Generate and display reservation report.
    """
    try:
        if start_date is None or end_date is None:
            start_date, end_date = get_default_date_range()

        start_datetime, end_datetime = validate_date_range(start_date, end_date)
        
        logger.info(f"Fetching reservation report for: {start_date} - {end_date}")

        # Generate report data
        service = ReservationReportService(start_datetime, end_datetime)
        report_data = service.generate_report()

        # Calculate financial metrics
        total_reservation_revenue = Decimal(report_data['total_reservation_revenue'])
        total_miscellaneous = Decimal(report_data['total_miscellaneous'])
        net_reservation_revenue = Decimal(report_data['net_reservation_revenue'])

        # Calculate average revenue per reservation
        total_reservations = report_data['reservations'].count()
        average_revenue_per_reservation = (
            total_reservation_revenue / total_reservations if total_reservations > 0 else Decimal('0.00')
        )

        # Paginate reservations
        reservations = report_data['reservations'].order_by('-reservation_date')  # Use the correct field name
        paginator = Paginator(reservations, ITEMS_PER_PAGE)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context = {
            'reservations_page': page_obj,
            'total_reservation_revenue': total_reservation_revenue,
            'total_miscellaneous': total_miscellaneous,
            'net_reservation_revenue': net_reservation_revenue,
            'selected_date_range': f"{start_date} to {end_date}",
            'explanation': generate_reservation_explanation(
                total_reservation_revenue,
                total_miscellaneous,
                net_reservation_revenue,
                report_data
            ),
            'top_reservations': report_data['top_reservations'],
            'top_guests': report_data['top_guests'],
            'average_revenue_per_reservation': average_revenue_per_reservation
        }
        logger.info("Report data successfully generated.")

        return render(request, 'reservation_report.html', context)

    except DateRangeError as e:
        messages.error(request, str(e))
        logger.error(f"Error rendering reservation report view: {e}")

        return redirect('reports:select_report')
    except Exception as e:
        messages.error(request, f"An error occurred while generating the report: {str(e)}")
        return redirect('reports:select_report')
