from decimal import Decimal
import json
from django.shortcuts import render
from django.db.models import Sum
from inventory.models import Category, Product, Purchase, Supplier
from sales.models import Sales, SalesItems
from .forms import ReportSelectionForm
from django.core.serializers.json import DjangoJSONEncoder


def generate_report(request):
    if request.method == "POST":
        form = ReportSelectionForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            start_date2 = form.cleaned_data['start_date2']
            end_date2 = form.cleaned_data['end_date2']

            if report_type == 'financial':
                return render(request, 'financial_report.html', {
                    'form': form,
                    'report_data': generate_financial_report(start_date, end_date),
                    'report_type': report_type,
                    'start_date': start_date,
                    'end_date': end_date,
                    'start_date2': start_date2,
                    'end_date2': end_date2
                })
            elif report_type == 'performance':
                return render(request, 'performance_report.html', {
                    'form': form,
                    'report_data': generate_performance_report(start_date, end_date),
                    'report_type': report_type,
                    'start_date': start_date,
                    'end_date': end_date,
                    'start_date2': start_date2,
                    'end_date2': end_date2
                })
      
    else:
        form = ReportSelectionForm()

    return render(request, 'select_report.html', {'form': form})


def generate_financial_report(start_date, end_date):
    sales_data = Sales.objects.filter(date_added__range=[start_date, end_date])
    total_sales = sales_data.aggregate(total_sales=Sum('grand_total'))['total_sales'] or 0

    purchases_data = Purchase.objects.filter(date_added__range=[start_date, end_date])
    total_purchases = purchases_data.aggregate(total_purchases=Sum('total'))['total_purchases'] or 0

    suppliers_data = Supplier.objects.all()
    supplier_expenses = []
    for supplier in suppliers_data:
        supplier_purchases = Purchase.objects.filter(supplier=supplier, date_added__range=[start_date, end_date])
        total_supplier_purchases = supplier_purchases.aggregate(total_purchases=Sum('total'))['total_purchases'] or 0
        supplier_expenses.append({'supplier': supplier.supplier_name, 'total_purchases': total_supplier_purchases})

    categories_data = Category.objects.all()
    category_sales = []
    for category in categories_data:
        category_products = Product.objects.filter(category=category)
        total_category_sales = sum(
            [
                SalesItems.objects.filter(product=product, sale__date_added__range=[start_date, end_date]).aggregate(total_sales=Sum('total'))['total_sales'] or 0
                for product in category_products
            ]
        )
        category_sales.append({'category': category.name, 'total_sales': total_category_sales})

    products_data = Product.objects.all()
    product_sales = []
    for product in products_data:
        total_product_sales = SalesItems.objects.filter(product=product, sale__date_added__range=[start_date, end_date]).aggregate(total_sales=Sum('total'))['total_sales'] or 0
        product_sales.append({'product': product.product_name, 'total_sales': total_product_sales})

    profit_loss = total_sales - total_purchases

    return {
        'total_sales': total_sales,
        'total_purchases': total_purchases,
        'supplier_expenses': supplier_expenses,
        'category_sales': category_sales,
        'product_sales': product_sales,
        'profit_loss': profit_loss
    }

def generate_performance_report(start_date, end_date):
    products = Product.objects.all()
    performance_data = []
    for product in products:
        total_sales_for_product = SalesItems.objects.filter(product=product, sale__date_added__range=[start_date, end_date]).aggregate(total_sales=Sum('total'))['total_sales'] or 0
        performance_data.append({'product': product.product_name, 'total_sales': total_sales_for_product})
    return performance_data
