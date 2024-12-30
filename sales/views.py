from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from sales.forms import SalesForm
from sales.models import Sales, SalesItems
from .models import Product
from django.db import transaction
from django.contrib import messages
import json
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt

def is_ajax(request):
    return request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest"


@login_required(login_url="authentication/login/")
def sales_list_view(request):
    sales = Sales.objects.all()
    sale_data = []

    for sale in sales:
        sale_info = {
            'id': sale.id,
            'code': sale.code,
            'client': sale.client,
            'date_added': sale.date_added,
            'grand_total': sale.grand_total,
            'total_items_sold': sum(item.qty for item in sale.salesitems_set.all()),
            'products_list': {item.product.product_name: item.qty for item in sale.salesitems_set.all()}
        }
        sale_data.append(sale_info)

    context = {
        'sale_data': sale_data,
    }
    return render(request, "sales_list.html", context)

@login_required(login_url="authentication/login/")
def receipt_view(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    return render(request, "receipt.html", {'sale': sale})

@login_required(login_url="authentication/login/")
def delete_sales_view(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    sale.delete()
    messages.success(request, 'Sale deleted successfully!', extra_tags="success")
    return redirect('sales_list')

@login_required(login_url="authentication/login/")
def update_sales_view(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    if request.method == 'POST':
        form = SalesForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sale updated successfully!', extra_tags="success")
            return redirect('sales_details', sale_id=sale.id)
        else:
            messages.error(request, 'There was an error during the sale update!', extra_tags="danger")
    else:
        form = SalesForm(instance=sale)
    return render(request, "update_sales.html", {'form': form, 'sale': sale})

@login_required(login_url="authentication/login/")
def sales_details_view(request, sale_id):
    sale = get_object_or_404(Sales, id=sale_id)
    sales_items = SalesItems.objects.filter(sale=sale)
    return render(request, "sales_details.html", {'sale': sale, 'sales_items': sales_items})

@login_required(login_url="/authentication/login/")
def checkout_modal(request):
    grand_total = 0
    if 'grand_total' in request.GET:
        grand_total = request.GET['grand_total']
    context = {
        'grand_total': grand_total,
    }
    return render(request, 'checkout.html', context)

@login_required(login_url="authentication/login/")
def create_sales_view(request):
    products = Product.objects.filter(status="ACTIVE").only("id", "product_name", "price")
    products_list = [p.to_select2() for p in products]

    context = {
        "active_icon": "sales",
        "products": products_list,
    }

    if request.method == "POST" and request.content_type == "application/json":
        try:
            with transaction.atomic():  # Start database transaction
                data = json.loads(request.body)

                # Convert string values to Decimal for precise calculation
                sub_total = Decimal(str(data["sub_total"]))
                tax_percent = Decimal(str(data["tax"]))
                tax_amount = Decimal(str(data["tax_amount"]))
                grand_total = sub_total + tax_amount  # Recalculate grand total with tax
                amount_payed = Decimal(str(data["amount_payed"]))
                amount_change = Decimal(str(data["amount_change"]))

                # Create sale
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

                    # Check if enough stock is available
                    if product.quantity < qty:
                        raise ValueError(f"Insufficient stock for {product.product_name}")

                    # Create sale item
                    SalesItems.objects.create(
                        sale=sale,
                        product=product,
                        price=Decimal(str(item_data["price"])),
                        qty=qty,
                        total=Decimal(str(item_data["total"]))
                    )

                    # Update product quantity
                    product.quantity -= qty
                    product.save()

            return JsonResponse({
                "status": "success",
                "sale_id": sale.id,
                "message": "Sale completed successfully"
            })

        except ValueError as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }, status=500)

    return render(request, "create_sales.html", context=context)

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

    return JsonResponse({
        "status": "error",
        "message": "Invalid request method"
    }, status=405)
