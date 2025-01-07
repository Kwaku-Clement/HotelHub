from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from activitylog.models import ActivityLog
from activitylog.views import get_mac_address
from sales.forms import SalesForm
from sales.models import Sales, SalesItems
from .models import Product
from django.db import transaction
from django.contrib import messages
import json
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta


def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"

@login_required(login_url="/authentication/login/")
def sales_list_view(request):
    today = datetime.now().date()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Filter sales based on user role
    if request.user.groups.filter(name__in=['admin', 'manager']).exists():
        base_queryset = Sales.objects.all()
    else:
        base_queryset = Sales.objects.filter(user=request.user)

    # Apply date filters if provided
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        sales = base_queryset.filter(date_added__range=(start_date, end_date))
    else:
        sales = base_queryset.filter(date_added__date=today)

    sale_data = []
    for sale in sales:
        sale_info = {
            'id': sale.id,
            'code': sale.code,
            'seller': sale.user.get_full_name() or sale.user.username,
            'date_added': sale.date_added,
            'grand_total': sale.grand_total,
            'total_items_sold': sum(item.qty for item in sale.salesitems_set.all()),
            'products_list': {item.product.product_name: item.qty for item in sale.salesitems_set.all()}
        }
        sale_data.append(sale_info)

    context = {
        'sale_data': sale_data,
        'is_admin_or_manager': request.user.groups.filter(name__in=['admin', 'manager']).exists()
    }

    # Log activity
    if request.user.is_authenticated:
        action = f"Viewed sales list"
        details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        ip_address = request.META.get('REMOTE_ADDR')
        mac_address = get_mac_address()
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=ip_address,
            mac_address=mac_address
        )

    return render(request, "sales_list.html", context)

@login_required(login_url="/authentication/login/")
def create_update_sales_view(request, sale_id=None):
    """Combined view for creating and updating sales"""
    sale = None if sale_id is None else get_object_or_404(Sales, id=sale_id)

    # Check if user has permission to edit this sale
    if sale and not request.user.groups.filter(name__in=['admin', 'manager']).exists():
        if sale.user != request.user:
            messages.error(request, "You don't have permission to edit this sale.", extra_tags="danger")
            return redirect('sales:sales_list')

    products = Product.objects.filter(status="ACTIVE").only("id", "product_name", "price")
    products_list = [p.to_select2() for p in products]

    # If this is an update, prepare the existing items data
    existing_items = []
    if sale:
        existing_items = [
            {
                'product_id': item.product.id,
                'product_name': item.product.product_name,
                'price': str(item.price),
                'qty': item.qty,
                'total': str(item.total)
            }
            for item in sale.salesitems_set.all()
        ]

    context = {
        "active_icon": "sales",
        "products": products_list,
        "sale": sale,
        "existing_items": json.dumps(existing_items) if existing_items else "[]"
    }

    if request.method == "POST" and request.content_type == "application/json":
        try:
            with transaction.atomic():
                data = json.loads(request.body)

                # Convert string values to Decimal
                sub_total = Decimal(str(data["sub_total"]))
                tax_percent = Decimal(str(data["tax"]))
                tax_amount = Decimal(str(data["tax_amount"]))
                grand_total = sub_total + tax_amount
                amount_payed = Decimal(str(data["amount_payed"]))
                amount_change = Decimal(str(data["amount_change"]))

                # Update or create sale
                if sale:
                    # Restore previous quantities before updating
                    for item in sale.salesitems_set.all():
                        item.product.quantity += item.qty
                        item.product.save()
                    sale.salesitems_set.all().delete()

                    # Update sale
                    sale.sub_total = sub_total
                    sale.grand_total = grand_total
                    sale.tax_amount = tax_amount
                    sale.tax = tax_percent
                    sale.amount_payed = amount_payed
                    sale.amount_change = amount_change
                    sale.client = data.get("client", "")
                    sale.save()
                else:
                    # Create new sale
                    sale = Sales.objects.create(
                        sub_total=sub_total,
                        grand_total=grand_total,
                        tax_amount=tax_amount,
                        tax=tax_percent,
                        amount_payed=amount_payed,
                        amount_change=amount_change,
                        user=request.user,
                        client=data.get("client", "")
                    )

                # Process items and update inventory
                for item_data in data["items"]:
                    product = Product.objects.select_for_update().get(id=int(item_data["product_id"]))
                    qty = int(item_data["qty"])

                    if product.quantity < qty:
                        raise ValueError(f"Insufficient stock for {product.product_name}")

                    SalesItems.objects.create(
                        sale=sale,
                        product=product,
                        price=Decimal(str(item_data["price"])),
                        qty=qty,
                        total=Decimal(str(item_data["total"]))
                    )

                    product.quantity -= qty
                    product.save()

                # Log activity
                action = f"{'Updated' if sale_id else 'Created'} sale: {sale.id}"
                details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
                ip_address = request.META.get('REMOTE_ADDR')
                mac_address = get_mac_address()
                ActivityLog.objects.create(
                    user=request.user,
                    action=action,
                    details=details,
                    ip_address=ip_address,
                    mac_address=mac_address
                )

                return JsonResponse({
                    "status": "success",
                    "sale_id": sale.id,
                    "message": f"Sale {'updated' if sale_id else 'created'} successfully"
                })

        except ValueError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"An error occurred: {str(e)}"}, status=500)

    return render(request, "create_update_sales.html", context=context)

@login_required(login_url="/authentication/login/")
def delete_sales_view(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    sale.delete()
    messages.success(request, 'Sale deleted successfully!', extra_tags="success")

    # Log activity
    action = f"Deleted sale: {sale.id}"
    details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
    ip_address = request.META.get('REMOTE_ADDR')
    mac_address = get_mac_address()
    ActivityLog.objects.create(
        user=request.user,
        action=action,
        details=details,
        ip_address=ip_address,
        mac_address=mac_address
    )

    return redirect('sales_list')

@login_required(login_url="/authentication/login/")
def sales_details_view(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    sales_items = SalesItems.objects.filter(sale=sale)

    # Log activity
    if request.user.is_authenticated:
        action = f"Viewed sales details: {sale.id}"
        details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        ip_address = request.META.get('REMOTE_ADDR')
        mac_address = get_mac_address()
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=ip_address,
            mac_address=mac_address
        )

    return render(request, "sales_details.html", {'sale': sale, 'sales_items': sales_items})

@login_required(login_url="/authentication/login/")
def checkout_modal(request):
    grand_total = 0
    if 'grand_total' in request.GET:
        grand_total = request.GET['grand_total']
    context = {
        'grand_total': grand_total,
    }

    # Log activity
    if request.user.is_authenticated:
        action = f"Viewed checkout modal"
        details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        ip_address = request.META.get('REMOTE_ADDR')
        mac_address = get_mac_address()
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=ip_address,
            mac_address=mac_address
        )

    return render(request, 'checkout.html', context)


@csrf_exempt
def process_payment(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                data = json.loads(request.body)

                # Validate payment data
                if not all(key in data for key in ['amount_paid', 'grand_total']):
                    raise ValueError("Missing required payment information")

                amount_paid = Decimal(str(data['amount_paid']))
                grand_total = Decimal(str(data['grand_total']))

                if amount_paid < grand_total:
                    raise ValueError("Insufficient payment amount")

                # Process successful payment
                return JsonResponse({
                    "status": "success",
                    "message": "Payment processed successfully",
                    "change": str(amount_paid - grand_total)
                })

        except ValueError as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Payment processing error: {str(e)}"
            }, status=500)

    # Log activity
    if request.user.is_authenticated:
        action = f"Processed payment"
        details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        ip_address = request.META.get('REMOTE_ADDR')
        mac_address = get_mac_address()
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=ip_address,
            mac_address=mac_address
        )

    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=405)

@login_required(login_url="/authentication/login/")
def revert_sales_view(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)

    try:
        with transaction.atomic():
            # Revert each sale item
            for item in sale.salesitems_set.all():
                product = item.product
                product.quantity += item.qty
                product.save()

            # Delete the sale
            sale.delete()

            messages.success(request, 'Sale reverted successfully!', extra_tags="success")

            # Log activity
            action = f"Reverted sale: {sale.id}"
            details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
            ip_address = request.META.get('REMOTE_ADDR')
            mac_address = get_mac_address()
            ActivityLog.objects.create(
                user=request.user,
                action=action,
                details=details,
                ip_address=ip_address,
                mac_address=mac_address
            )

    except Exception as e:
        messages.error(request, f'Error reverting sale: {str(e)}', extra_tags="danger")

    return redirect('sales:sales_list')

@login_required(login_url="/authentication/login/")
def receipt_view(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)

    # Log activity
    if request.user.is_authenticated:
        action = f"Viewed receipt for sale: {sale.id}"
        details = f"User: {request.user.username}, IP: {request.META.get('REMOTE_ADDR')}, User-Agent: {request.META.get('HTTP_USER_AGENT')}"
        ip_address = request.META.get('REMOTE_ADDR')
        mac_address = get_mac_address()
        ActivityLog.objects.create(
            user=request.user,
            action=action,
            details=details,
            ip_address=ip_address,
            mac_address=mac_address
        )

    return render(request, "receipt.html", {'sale': sale})
