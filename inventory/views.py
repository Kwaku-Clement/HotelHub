import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, Product, Supplier, Purchase, SupplierProduct
from .forms import  SupplierForm, PurchaseForm, CategoryForm, ProductForm, SupplierProductForm
from django.db import transaction
import logging
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

@login_required(login_url="/authentication/login/")
def categories_list_view(request):
    context = {
        "active_icon": "products_categories",
        "categories": Category.objects.all()
    }
    return render(request, "category_list.html", context=context)

@login_required(login_url="/authentication/login/")
def categories_add_view(request):
    context = {
        "active_icon": "products_categories",
        "category_status": Category.STATUS_CHOICES,
    }

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            try:
                attributes = {
                    "name": form.cleaned_data['name'],
                    "status": request.POST.get('state', 'ACTIVE'),
                    "description": form.cleaned_data['description'],
                }

                if Category.objects.filter(**attributes).exists():
                    messages.error(request, 'Category already exists!', extra_tags="warning")
                    return redirect('inventory:category_create')

                new_category = Category.objects.create(**attributes)
                messages.success(
                    request,
                    f"Category '{attributes['name']}' created successfully!",
                    extra_tags="success"
                )
                return redirect('inventory:category_list')

            except Exception as e:
                messages.error(request, 'There was an error during the creation!', extra_tags="danger")
                logger.error(e)
                return redirect('inventory:category_create')
        else:
            messages.error(request, 'Invalid form submission!', extra_tags="danger")

    else:
        form = CategoryForm()

    context["form"] = form
    return render(request, "category_create.html", context=context)

@login_required(login_url="/authentication/login/")
def categories_update_view(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
    except Exception as e:
        messages.error(
            request, 'There was an error trying to get the category!', extra_tags="danger")
        logger.error(e)
        return redirect('inventory:category_list')

    context = {
        "active_icon": "products_categories",
        "category_status": Category.STATUS_CHOICES,
        "category": category
    }

    if request.method == 'POST':
        try:
            data = request.POST

            attributes = {
                "name": data['name'],
                "status": data['state'],
                "description": data['description']
            }

            if Category.objects.filter(**attributes).exists():
                messages.error(request, 'Category already exists!',
                               extra_tags="warning")
                return redirect('inventory:category_create')

            category = Category.objects.filter(
                id=category_id).update(**attributes)

            category = Category.objects.get(id=category_id)

            messages.success(request, 'Category: ' + category.name +
                             ' updated successfully!', extra_tags="success")
            return redirect('inventory:category_list')
        except Exception as e:
            messages.error(
                request, 'There was an error during the update!', extra_tags="danger")
            logger.error(e)
            return redirect('inventory:category_list')

    return render(request, "category_update.html", context=context)

@login_required(login_url="/authentication/login/")
def categories_delete_view(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        category.delete()
        messages.success(request, 'Category: ' + category.name +
                         ' deleted!', extra_tags="success")
        return redirect('inventory:category_list')
    except Exception as e:
        messages.error(
            request, 'There was an error during the deletion!', extra_tags="danger")
        logger.error(e)
        return redirect('inventory:category_list')

@login_required(login_url="/authentication/login/")
def products_list_view(request):
    context = {
        "active_icon": "products",
        "products": Product.objects.all()
    }
    return render(request, "product_list.html", context=context)

@login_required(login_url="/authentication/login/")
def products_add_view(request):
    context = {
        "active_icon": "products_categories",
        "product_status": Product.STATUS_CHOICES,
        "categories": Category.objects.filter(status="ACTIVE"),
        "form": ProductForm()  # Add empty form to context for GET requests
    }

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)

            # Check for duplicate products
            if Product.objects.filter(
                product_name=product.product_name,
                category=product.category,
                status=product.status,
                price=product.price
            ).exists():
                messages.error(request, 'Product already exists!', extra_tags="warning")
                context['form'] = form  # Add form back to context with data
                return render(request, "product_create.html", context)

            try:
                product.save()
                messages.success(request, f'Product: {product.product_name} created successfully!', extra_tags="success")
                return redirect('inventory:product_list')
            except Exception as e:
                messages.error(request, f'Database error: {str(e)}', extra_tags="danger")
                context['form'] = form
                return render(request, "product_create.html", context)
        else:
            messages.error(request, 'Please correct the errors below.', extra_tags="danger")
            context['form'] = form
            return render(request, "product_create.html", context)

    return render(request, "product_create.html", context=context)


@login_required(login_url="/authentication/login/")
def products_update_view(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.error(request, 'There was an error trying to get the product!', extra_tags="danger")
        return redirect('inventory:product_list')

    context = {
        "active_icon": "products",
        "product_status": Product.STATUS_CHOICES,
        "product": product,
        "categories": Category.objects.all()
    }

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            if Product.objects.filter(
                product_name=product.product_name,
                category=product.category,
                status=product.status,
                price=product.price
            ).exclude(id=product_id).exists():
                messages.error(request, 'Product already exists!', extra_tags="warning")
                return redirect('inventory:product_update', product_id=product_id)

            product.save()
            messages.success(request, f'Product: {product.product_name} updated successfully!', extra_tags="success")
            return redirect('inventory:product_list')
        else:
            messages.error(request, 'There was an error during the update!', extra_tags="danger")
            return redirect('inventory:product_update', product_id=product_id)

    return render(request, "product_update.html", context=context)

@login_required(login_url="/authentication/login/")
def products_delete_view(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product.delete()
        messages.success(request, f'Product: {product.product_name} deleted!', extra_tags="success")
        return redirect('inventory:product_list')
    except Product.DoesNotExist:
        messages.error(request, 'There was an error during the deletion!', extra_tags="danger")
        return redirect('inventory:product_list')


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

@login_required(login_url="/authentication/login/")
def get_products_ajax_view(request):
    if request.method == 'POST':
        if is_ajax(request=request):
            data = []

            products = Product.objects.filter(
                product_name__icontains=request.POST['term'])
            for product in products[0:10]:
                item = product.to_json()
                data.append(item)

            return JsonResponse(data, safe=False)

@login_required(login_url="/authentication/login/")
def home_view(request):
    return render(request, 'home.html')


@login_required(login_url="/authentication/login/")
def supplier_list(request):
    # Get all suppliers and their associated products
    suppliers = Supplier.objects.prefetch_related('products')

    return render(request, 'supplier_list.html', {'suppliers': suppliers})


@login_required(login_url="/authentication/login/")
def supplier_create(request):
    supplier_form = SupplierForm(request.POST or None)
    product_form = SupplierProductForm(request.POST or None)
    
    if request.method == 'POST':
        if supplier_form.is_valid() and product_form.is_valid():
            try:
                with transaction.atomic():
                    # Save the supplier first
                    supplier = supplier_form.save()
                    
                    # Assign the supplier to the product and save
                    product = product_form.save(commit=False)
                    product.supplier = supplier
                    product.save()
                    
                    messages.success(request, 'Supplier and product created successfully.')
                    return redirect('inventory:supplier_list')
            except Exception as e:
                messages.error(request, f'Error creating supplier: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    
    context = {
        'supplier_form': supplier_form,
        'product_form': product_form,
    }
    
    return render(request, 'supplier_create.html', context)

@login_required(login_url="/authentication/login/")
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    form = SupplierForm(request.POST or None, instance=supplier)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Supplier updated successfully.')
        return redirect('inventory:supplier_list')
    return render(request, 'supplier_update.html', {'form': form})

@login_required(login_url="/authentication/login/")
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Supplier deleted successfully.')
        return redirect('inventory:supplier_list')
    return render(request, 'supplier_delete.html', {'supplier': supplier})


@login_required(login_url="/authentication/login/")
def purchase_list(request):
    purchases = Purchase.objects.select_related('supplier', 'product').all()
    return render(request, 'purchase_list.html', {'purchases': purchases})  # Fixed typo in 'purchures'

@login_required(login_url="/authentication/login/")
def purchase_update(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    form = PurchaseForm(request.POST or None, instance=purchase)
    if request.method == 'POST' and form.is_valid():
        purchase = form.save(commit=False)
        purchase.total = purchase.quantity * purchase.price  # Updated to use 'price'
        purchase.save()
        messages.success(request, 'Purchase updated successfully.')
        return redirect('inventory:purchase_list')
    return render(request, 'purchase_update.html', {'form': form})

@login_required(login_url="/authentication/login/")
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        purchase.delete()
        messages.success(request, 'Purchase deleted successfully.')
        return redirect('inventory:purchase_list')
    return render(request, 'purchase_delete.html', {'purchase': purchase})

login_required(login_url="/authentication/login/")
def purchase_create(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save()
            messages.success(request, 'Purchase created successfully.')
            return redirect('inventory:purchase_list')
    else:
        form = PurchaseForm()
    
    return render(request, 'purchase_create.html', {
        'form': form,
        'title': 'Create Purchase'
    })


@login_required(login_url="/authentication/login/")
@require_http_methods(["GET"])
def get_supplier_products(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        supplier_id = request.GET.get('supplier')
        if supplier_id:
            try:
                supplier_products = SupplierProduct.objects.filter(supplier_id=supplier_id)
                products_data = [
                    {
                        'id': product.id,
                        'product_name': product.product_name,
                        'price': product.price,
                        'quantity': product.quantity
                    }
                    for product in supplier_products
                ]
                return JsonResponse({'products': products_data})
            except SupplierProduct.DoesNotExist:
                return JsonResponse({'error': 'No products found for the selected supplier.'})
        else:
            return JsonResponse({'error': 'Supplier ID is missing.'})
    else:
        return JsonResponse({'error': 'Invalid request.'})
