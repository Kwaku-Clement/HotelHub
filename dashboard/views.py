import json
from datetime import date, datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Coalesce, TruncDate
from django.shortcuts import render
from miscellaneous.models import Miscellaneous
from reservations.models import Reservation, ReservationDetail
from rooms.models import Room, RoomType
from django.utils import timezone
from sales.models import Sales, SalesItems
from django.db.models import Count, Sum, F, Q, Avg, Value, DecimalField, IntegerField
from decimal import Decimal


@login_required(login_url="/authentication/login/")
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

    # Query miscellaneous expenses for the current period
    period_1_miscellaneous = Miscellaneous.objects.filter(
        date__range=(start_of_week, end_of_week)
    ).values('type').annotate(total_amount=Sum('amount'))

    period_2_miscellaneous = Miscellaneous.objects.filter(
        date__range=(start_of_week - timedelta(days=7), start_of_week)
    ).values('type').annotate(total_amount=Sum('amount'))

    # Convert Decimal to float for JSON serialization
    period_1_miscellaneous = [{'type': item['type'], 'total_amount': float(item['total_amount'])} for item in period_1_miscellaneous]
    period_2_miscellaneous = [{'type': item['type'], 'total_amount': float(item['total_amount'])} for item in period_2_miscellaneous]

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
        'period_1_miscellaneous': json.dumps(period_1_miscellaneous),
        'period_2_miscellaneous': json.dumps(period_2_miscellaneous),
        'active_icon': 'index'
    }
    return render(request, 'index.html', context)

@login_required(login_url="/authentication/login/")
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

    # Get miscellaneous expenses for both periods
    period_1_miscellaneous = get_miscellaneous_expenses(period_1_start, period_1_end)
    period_2_miscellaneous = get_miscellaneous_expenses(period_2_start, period_2_end)

    context = {
        'period_1_start': period_1_start,
        'period_1_end': period_1_end,
        'period_2_start': period_2_start,
        'period_2_end': period_2_end,
        'period_1_metrics': period_1_metrics,
        'period_2_metrics': period_2_metrics,
        'comparison_metrics': comparison_metrics,
        'period_1_earnings': json.dumps(period_1_earnings, default=float),
        'period_2_earnings': json.dumps(period_2_earnings, default=float),
        'room_occupancy': json.dumps(room_occupancy_comparison, default=float),
        'rooms_count': Room.objects.count(),
        'room_types_count': RoomType.objects.count(),
        'period_1_miscellaneous': json.dumps(period_1_miscellaneous, default=float),
        'period_2_miscellaneous': json.dumps(period_2_miscellaneous, default=float),
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

def get_miscellaneous_expenses(start_date, end_date):
    """Get miscellaneous expenses for the period"""
    miscellaneous_expenses = Miscellaneous.objects.filter(
        date__range=(start_date, end_date)
    ).values('type').annotate(
        total_amount=Coalesce(Sum('amount'), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
    ).order_by('-total_amount')

    return list(miscellaneous_expenses)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

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
        # Get sales data for the period
        sales_data = Sales.objects.filter(
            date_added__range=[start_date, end_date]
        )
        sales_items = SalesItems.objects.filter(sale__in=sales_data)

        # Calculate total sales
        total_sales = sales_data.aggregate(
            total=Coalesce(
                Sum('grand_total'),
                Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )['total']

        # Calculate total profit
        total_profit = sales_items.aggregate(
            total_profit=Coalesce(
                Sum(
                    (F('price') - F('product__price')) * F('qty'),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                ),
                Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )['total_profit']

        # Get top products with float conversion
        top_products = list(
            sales_items
            .values('product__product_name')
            .annotate(
                total_sales=Sum(F('price') * F('qty')),
                quantity_sold=Sum('qty')
            )
            .order_by('-total_sales')[:5]
        )
        # Convert Decimal to float in top_products
        for product in top_products:
            product['total_sales'] = float(product['total_sales'])
            product['quantity_sold'] = float(product['quantity_sold'])

        # Get top sellers with float conversion
        top_sellers = list(
            sales_data
            .values('user__first_name', 'user__last_name')
            .annotate(
                total_sales=Sum('grand_total'),
                transactions=Count('id')
            )
            .order_by('-total_sales')[:5]
        )
        # Convert Decimal to float in top_sellers
        for seller in top_sellers:
            seller['total_sales'] = float(seller['total_sales'])

        # Get misc expenses with float conversion
        misc_expenses = list(
            Miscellaneous.objects.filter(date__range=[start_date, end_date])
            .values('type')
            .annotate(
                total_amount=Coalesce(
                    Sum('amount'),
                    Value(0),
                    output_field=DecimalField(max_digits=10, decimal_places=2)
                )
            )
            .order_by('-total_amount')
        )
        # Convert Decimal to float in misc_expenses
        for expense in misc_expenses:
            expense['total_amount'] = float(expense['total_amount'])

        # Calculate total expenses
        total_misc_expenses = sum(expense['total_amount'] for expense in misc_expenses)

        # Get daily sales trend with float conversion
        sales_trend = list(
            sales_data
            .annotate(date=TruncDate('date_added'))
            .values('date')
            .annotate(
                total_sales=Sum('grand_total')
            )
            .order_by('date')
        )
        # Convert Decimal to float in sales_trend
        for trend in sales_trend:
            trend['total_sales'] = float(trend['total_sales'])
            trend['date'] = trend['date'].strftime('%Y-%m-%d')  # Convert date to string

        # Calculate total products sold
        total_products_sold = sales_items.aggregate(
            total=Coalesce(
                Sum('qty'),
                Value(0),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )['total']

        return {
            'total_sales': float(total_sales),
            'total_profit': float(total_profit),
            'total_products_sold': float(total_products_sold),
            'total_misc_expenses': float(total_misc_expenses),
            'top_products': top_products,
            'top_sellers': top_sellers,
            'misc_expenses': misc_expenses,
            'sales_trend': sales_trend
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
        'sales_change': calculate_change(
            period1_data['total_sales'],
            period2_data['total_sales']
        ),
        'profit_change': calculate_change(
            period1_data['total_profit'],
            period2_data['total_profit']
        ),
        'products_change': calculate_change(
            period1_data['total_products_sold'],
            period2_data['total_products_sold']
        ),
        'expenses_change': calculate_change(
            period1_data['total_misc_expenses'],
            period2_data['total_misc_expenses']
        )
    }

    # Calculate trend analysis
    def calculate_trend(data):
        if len(data) < 2:
            return 0
        start_value = data[0]['total_sales']
        end_value = data[-1]['total_sales']
        return calculate_change(end_value, start_value)

    trend_analysis = {
        'period1_trend': calculate_trend(period1_data['sales_trend']),
        'period2_trend': calculate_trend(period2_data['sales_trend'])
    }

    context = {
        'period1_start': period1_start.strftime('%Y-%m-%d'),
        'period1_end': period1_end.strftime('%Y-%m-%d'),
        'period2_start': period2_start.strftime('%Y-%m-%d'),
        'period2_end': period2_end.strftime('%Y-%m-%d'),
        'period1': period1_data,
        'period2': period2_data,
        'comparison': comparison_data,
        'trend_analysis': trend_analysis,
        # Convert data for charts using json.dumps with decimal_default
        'period1_top_products': json.dumps(period1_data['top_products'], default=decimal_default),
        'period2_top_products': json.dumps(period2_data['top_products'], default=decimal_default),
        'period1_top_sellers': json.dumps(period1_data['top_sellers'], default=decimal_default),
        'period2_top_sellers': json.dumps(period2_data['top_sellers'], default=decimal_default),
        'period1_expenses': json.dumps(period1_data['misc_expenses'], default=decimal_default),
        'period2_expenses': json.dumps(period2_data['misc_expenses'], default=decimal_default),
        'salesTrend1': json.dumps(period1_data['sales_trend'], default=decimal_default),
        'salesTrend2': json.dumps(period2_data['sales_trend'], default=decimal_default)
    }

    return render(request, 'analysis_report.html', context)
