import json
from datetime import date, datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import render
from inventory.models import Product, Purchase
from reservations.models import Reservation, ReservationDetail
from rooms.models import Room, RoomType
from django.utils import timezone
from miscellaneous.models import Miscellaneous
from sales.models import Sales, SalesItems
from django.db.models import Count, Sum, F, Q, Avg, Value, DecimalField, IntegerField
from decimal import Decimal


@login_required(login_url="authentication/login/")
def index(request):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    # Calculate earnings for the current week
    earnings_data = []
    current_date = start_of_week

    while current_date <= end_of_week:
        earning = Reservation.objects.filter(
            reservation_date=current_date
        ).aggregate(
            total=Coalesce(Sum('grand_total'), 0.0, output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total']

        earnings_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'earning': float(earning)
        })
        current_date += timedelta(days=1)

    # Calculate total earnings and average for the week
    earnings_values = [item['earning'] for item in earnings_data]
    total_earnings = sum(earnings_values)
    avg_earning = total_earnings / len(earnings_data) if earnings_data else 0

    # Get top rooms with booking days within the selected date range
    top_rooms = Room.objects.annotate(
        days=Coalesce(Sum('reservationdetail__days', filter=Q(reservationdetail__reservation__reservation_date__range=(start_of_week, end_of_week))), 0)
    ).filter(days__gt=0).order_by('-days')

    top_rooms_data = [{'name': room.name, 'days': room.days} for room in top_rooms]
    top_rooms_names_list = [room.name for room in top_rooms]

    context = {
        'start_date': start_of_week,
        'end_date': end_of_week,
        'avg_earning': avg_earning,
        'total_earnings': total_earnings,
        'rooms': Room.objects.count(),
        'room_types': RoomType.objects.count(),
        'earnings_data': json.dumps(earnings_data),
        'top_rooms_data': json.dumps(top_rooms_data),
        'top_rooms_names_list': top_rooms_names_list,
        'active_icon': 'index'
    }

    return render(request, 'index.html', context)

@login_required(login_url="authentication/login/")
def dashboard(request):
    # Get comparison periods from request
    period_1_start = request.GET.get('period_1_start')
    period_1_end = request.GET.get('period_1_end')
    period_2_start = request.GET.get('period_2_start')
    period_2_end = request.GET.get('period_2_end')

    # Set default dates if not provided
    today = date.today()
    if not all([period_1_start, period_1_end, period_2_start, period_2_end]):
        # Default: Compare current month with previous month
        period_2_end = today
        period_2_start = date(today.year, today.month, 1)
        period_1_end = period_2_start - timedelta(days=1)
        period_1_start = date(period_1_end.year, period_1_end.month, 1)
    else:
        # Parse provided dates
        period_1_start = datetime.strptime(period_1_start, '%Y-%m-%d').date()
        period_1_end = datetime.strptime(period_1_end, '%Y-%m-%d').date()
        period_2_start = datetime.strptime(period_2_start, '%Y-%m-%d').date()
        period_2_end = datetime.strptime(period_2_end, '%Y-%m-%d').date()

    # Analysis for Period 1
    period_1_metrics = get_period_metrics(period_1_start, period_1_end)

    # Analysis for Period 2
    period_2_metrics = get_period_metrics(period_2_start, period_2_end)

    # Calculate percentage changes
    comparison_metrics = calculate_comparison_metrics(period_1_metrics, period_2_metrics)

    # Get daily earnings data for both periods
    period_1_earnings = get_daily_earnings(period_1_start, period_1_end)
    period_2_earnings = get_daily_earnings(period_2_start, period_2_end)

    # Room occupancy comparison
    room_occupancy_comparison = get_room_occupancy_comparison(
        period_1_start, period_1_end,
        period_2_start, period_2_end
    )

    context = {
        'period_1_start': period_1_start,
        'period_1_end': period_1_end,
        'period_2_start': period_2_start,
        'period_2_end': period_2_end,
        'period_1_metrics': period_1_metrics,
        'period_2_metrics': period_2_metrics,
        'comparison_metrics': comparison_metrics,
        'period_1_earnings': json.dumps(period_1_earnings),
        'period_2_earnings': json.dumps(period_2_earnings),
        'room_occupancy': json.dumps(room_occupancy_comparison),
        'rooms_count': Room.objects.count(),
        'room_types_count': RoomType.objects.count(),
        'active_icon': 'dashboard'
    }

    return render(request, 'dashboard.html', context)

def get_period_metrics(start_date, end_date):
    """Calculate key metrics for a given period"""
    reservations = Reservation.objects.filter(
        reservation_date__range=(start_date, end_date)
    )

    total_earnings = reservations.aggregate(
        total=Coalesce(Sum('grand_total'), 0.0, output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total']

    total_costs = reservations.aggregate(
        total=Coalesce(Sum('tax_amount'), 0.0, output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total']

    guest_count = reservations.values('guest').distinct().count()

    avg_stay_duration = ReservationDetail.objects.filter(
        reservation__reservation_date__range=(start_date, end_date)
    ).aggregate(
        avg_days=Coalesce(Avg('days'), 0.0, output_field=DecimalField(max_digits=10, decimal_places=2))
    )['avg_days']

    occupancy_rate = calculate_occupancy_rate(start_date, end_date)

    return {
        'total_earnings': float(total_earnings),
        'total_costs': float(total_costs),
        'profit': float(total_earnings - total_costs),
        'guest_count': guest_count,
        'avg_stay_duration': float(avg_stay_duration),
        'occupancy_rate': occupancy_rate,
        'period_days': (end_date - start_date).days + 1
    }

def calculate_occupancy_rate(start_date, end_date):
    """Calculate room occupancy rate for a given period"""
    total_rooms = Room.objects.count()
    period_days = (end_date - start_date).days + 1
    total_room_days = total_rooms * period_days

    occupied_room_days = ReservationDetail.objects.filter(
        reservation__reservation_date__range=(start_date, end_date)
    ).aggregate(
        total_days=Coalesce(Sum('days'), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
    )['total_days']

    return (occupied_room_days / total_room_days * 100) if total_room_days > 0 else 0

def calculate_comparison_metrics(period_1, period_2):
    """Calculate percentage changes between two periods"""
    def calculate_change(old_value, new_value):
        if old_value == 0:
            return 100 if new_value > 0 else 0
        return ((new_value - old_value) / abs(old_value)) * 100

    return {
        'earnings_change': calculate_change(period_1['total_earnings'], period_2['total_earnings']),
        'profit_change': calculate_change(period_1['profit'], period_2['profit']),
        'guest_change': calculate_change(period_1['guest_count'], period_2['guest_count']),
        'stay_duration_change': calculate_change(period_1['avg_stay_duration'], period_2['avg_stay_duration']),
        'occupancy_change': calculate_change(period_1['occupancy_rate'], period_2['occupancy_rate'])
    }

def get_daily_earnings(start_date, end_date):
    """Get daily earnings data for the period"""
    earnings_data = []
    current_date = start_date

    while current_date <= end_date:
        earning = Reservation.objects.filter(
            reservation_date=current_date
        ).aggregate(
            total=Coalesce(Sum('grand_total'), 0.0, output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total']

        earnings_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'earning': float(earning)
        })
        current_date += timedelta(days=1)

    return earnings_data

def get_room_occupancy_comparison(p1_start, p1_end, p2_start, p2_end):
    """Compare room occupancy between two periods"""
    def get_period_occupancy(start_date, end_date):
        return Room.objects.annotate(
            days=Coalesce(
                Sum('reservationdetail__days',
                    filter=Q(reservationdetail__reservation__reservation_date__range=(start_date, end_date))),
                0
            )
        ).values('name', 'days')

    period_1_occupancy = {room['name']: room['days'] for room in get_period_occupancy(p1_start, p1_end)}
    period_2_occupancy = {room['name']: room['days'] for room in get_period_occupancy(p2_start, p2_end)}

    all_rooms = set(list(period_1_occupancy.keys()) + list(period_2_occupancy.keys()))

    return [{
        'name': room,
        'period_1_days': period_1_occupancy.get(room, 0),
        'period_2_days': period_2_occupancy.get(room, 0)
    } for room in all_rooms]


def inventory_analysis_report(request):
    # Get date ranges for both periods
    period1_start = request.GET.get('period1_start')
    period1_end = request.GET.get('period1_end')
    period2_start = request.GET.get('period2_start')
    period2_end = request.GET.get('period2_end')
    
    # Set default dates if not provided
    if not all([period1_start, period1_end, period2_start, period2_end]):
        period1_end = timezone.now()
        period1_start = period1_end - timedelta(days=30)
        period2_end = period1_start - timedelta(days=1)
        period2_start = period2_end - timedelta(days=30)
    else:
        period1_start = datetime.strptime(period1_start, '%Y-%m-%d')
        period1_end = datetime.strptime(period1_end, '%Y-%m-%d')
        period2_start = datetime.strptime(period2_start, '%Y-%m-%d')
        period2_end = datetime.strptime(period2_end, '%Y-%m-%d')

    def get_period_data(start_date, end_date):
        # Get purchase data for the period
        purchase_data = Purchase.objects.filter(
            date_added__range=[start_date, end_date]
        )

        # Calculate total purchases
        total_purchases = purchase_data.aggregate(
            total=Coalesce(
                Sum('total_amount'),
                Value(0),
                output_field=DecimalField(max_digits=18, decimal_places=2)
            )
        )['total']

        # Get top products purchased
        top_products = list(
            purchase_data
            .values('product__product_name')
            .annotate(
                total_purchases=Sum('total_amount'),
                quantity_purchased=Sum('quantity')
            )
            .order_by('-total_purchases')[:5]
        )
        
        # Convert Decimal to float for JSON serialization
        for product in top_products:
            product['total_purchases'] = float(product['total_purchases'])
            product['quantity_purchased'] = float(product['quantity_purchased'])

        # Get top suppliers
        top_suppliers = list(
            purchase_data
            .values('supplier__supplier_name')
            .annotate(
                total_purchases=Sum('total_amount'),
                transactions=Count('id')
            )
            .order_by('-total_purchases')[:5]
        )
        
        # Convert Decimal to float
        for supplier in top_suppliers:
            supplier['total_purchases'] = float(supplier['total_purchases'])

        # Get category distribution
        category_distribution = list(
            purchase_data
            .values('category__name')
            .annotate(
                total_amount=Coalesce(
                    Sum('total_amount'),
                    Value(0),
                    output_field=DecimalField(max_digits=18, decimal_places=2)
                )
            )
            .order_by('-total_amount')
        )
        
        # Convert Decimal to float
        for category in category_distribution:
            category['total_amount'] = float(category['total_amount'])

        # Get daily purchase trend
        purchase_trend = list(
            purchase_data
            .annotate(date=TruncDate('date_added'))
            .values('date')
            .annotate(
                total_purchases=Sum('total_amount')
            )
            .order_by('date')
        )
        
        # Convert Decimal to float and date to string
        for trend in purchase_trend:
            trend['total_purchases'] = float(trend['total_purchases'])
            trend['date'] = trend['date'].strftime('%Y-%m-%d')

        # Calculate total products purchased
        total_products_purchased = purchase_data.aggregate(
            total=Coalesce(
                Sum('quantity'),
                Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )['total']

        # Get current inventory value
        current_inventory_value = Product.objects.aggregate(
            total=Coalesce(
                Sum(F('price') * F('quantity')),
                Value(0),
                output_field=DecimalField(max_digits=18, decimal_places=2)
            )
        )['total']

        return {
            'total_purchases': float(total_purchases),
            'total_products_purchased': float(total_products_purchased),
            'current_inventory_value': float(current_inventory_value),
            'top_products': top_products,
            'top_suppliers': top_suppliers,
            'category_distribution': category_distribution,
            'purchase_trend': purchase_trend
        }

    # Get data for both periods
    period1_data = get_period_data(period1_start, period1_end)
    period2_data = get_period_data(period2_start, period2_end)

    # Calculate percentage changes
    def calculate_change(current, previous):
        if previous == 0:
            return 0
        return ((current - previous) / previous) * 100

    comparison_data = {
        'purchases_change': calculate_change(
            period1_data['total_purchases'],
            period2_data['total_purchases']
        ),
        'products_change': calculate_change(
            period1_data['total_products_purchased'],
            period2_data['total_products_purchased']
        ),
        'inventory_value_change': calculate_change(
            period1_data['current_inventory_value'],
            period2_data['current_inventory_value']
        )
    }

    context = {
        'period1_start': period1_start.strftime('%Y-%m-%d'),
        'period1_end': period1_end.strftime('%Y-%m-%d'),
        'period2_start': period2_start.strftime('%Y-%m-%d'),
        'period2_end': period2_end.strftime('%Y-%m-%d'),
        'period1': period1_data,
        'period2': period2_data,
        'comparison': comparison_data,
        'period1_top_products': json.dumps(period1_data['top_products']),
        'period2_top_products': json.dumps(period2_data['top_products']),
        'period1_top_suppliers': json.dumps(period1_data['top_suppliers']),
        'period2_top_suppliers': json.dumps(period2_data['top_suppliers']),
        'period1_categories': json.dumps(period1_data['category_distribution']),
        'period2_categories': json.dumps(period2_data['category_distribution']),
        'purchaseTrend1': json.dumps(period1_data['purchase_trend']),
        'purchaseTrend2': json.dumps(period2_data['purchase_trend'])
    }

    return render(request, 'inventory_analysis.html', context)