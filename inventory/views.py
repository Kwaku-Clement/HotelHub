import json
import unicodedata
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, Product, Supplier, Purchase
from .forms import SupplierForm, PurchaseForm, CategoryForm, ProductForm
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

@login_required(login_url="/authentication/login/")
def home_view(request):
    return render(request, 'home.html')

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

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category: ' + category.name +
                             ' updated successfully!', extra_tags="success")
            return redirect('inventory:category_list')
        else:
            messages.error(request, 'There was an error during the update!', extra_tags="danger")
    else:
        form = CategoryForm(instance=category)

    context = {
        "active_icon": "products_categories",
        "category_status": Category.STATUS_CHOICES,
        "category": category,
        "form": form
    }

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
        "form": ProductForm()
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
    product = get_object_or_404(Product, id=product_id)

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
    else:
        form = ProductForm(instance=product)

    context = {
        "active_icon": "products",
        "product_status": Product.STATUS_CHOICES,
        "product": product,
        "categories": Category.objects.all(),
        "form": form
    }

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

@login_required(login_url="/authentication/login/")
def supplier_list(request):
    # Get all suppliers and their associated products
    suppliers = Supplier.objects.prefetch_related('products')

    return render(request, 'supplier_list.html', {'suppliers': suppliers})

@login_required(login_url="/authentication/login/")
def supplier_create(request):
    if request.method == 'POST':
        supplier_form = SupplierForm(request.POST)
        
        if supplier_form.is_valid():
            try:
                with transaction.atomic():
                    # Check for existing supplier with a similar name
                    supplier_name = supplier_form.cleaned_data['supplier_name']
                    normalized_name = "".join(
                        c for c in unicodedata.normalize("NFD", supplier_name)
                        if unicodedata.category(c) != "Mn"
                    ).lower().replace(" ", "")

                    existing_supplier = None
                    for supplier in Supplier.objects.all():
                        supplier_normalized = "".join(
                            c for c in unicodedata.normalize("NFD", supplier.supplier_name)
                            if unicodedata.category(c) != "Mn"
                        ).lower().replace(" ", "")
                        if supplier_normalized == normalized_name:
                            existing_supplier = supplier
                            break

                    if existing_supplier:
                        # Update existing supplier
                        for field, value in supplier_form.cleaned_data.items():
                            setattr(existing_supplier, field, value)
                        existing_supplier.save()
                        messages.info(request, f"Supplier '{existing_supplier.supplier_name}' updated.")
                    else:
                        # Create new supplier
                        supplier_form.save()
                        messages.success(request, 'Supplier created successfully.')
                    
                    return redirect('inventory:supplier_list')
                    
            except Exception as e:
                messages.error(request, f'Error creating/updating supplier: {str(e)}')
        else:
            # Handle form errors
            for field, errors in supplier_form.errors.items():
                for error in errors:
                    messages.error(request, f"Supplier form error - {field}: {error}")
    else:
        supplier_form = SupplierForm()
    
    return render(request, 'supplier_create.html', {
        'supplier_form': supplier_form,
        'title': 'Create Supplier'
    })

@login_required(login_url="/authentication/login/")
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier_form = SupplierForm(request.POST or None, instance=supplier)
    
    if request.method == 'POST':
        if supplier_form.is_valid():
            try:
                supplier = supplier_form.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Supplier updated successfully.',
                        'data': {
                            'supplier_name': supplier.supplier_name,
                            'product': supplier.product,
                            'category': supplier.category,
                            'price': float(supplier.price),
                            'quantity': supplier.quantity,
                            'status': supplier.status
                        }
                    })
                
                messages.success(request, 'Supplier updated successfully.')
                return redirect('inventory:supplier_list')
                
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': str(e)
                    })
                messages.error(request, f'Error updating supplier: {str(e)}')
                return render(request, 'supplier_update.html', {
                    'supplier_form': supplier_form,
                    'supplier': supplier
                })
        
        # Handle invalid form
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            for field, error_list in supplier_form.errors.items():
                errors[field] = error_list[0]
            return JsonResponse({
                'success': False,
                'errors': errors
            })
        
        # If not AJAX and form is invalid, render the form with errors
        return render(request, 'supplier_update.html', {
            'supplier_form': supplier_form,
            'supplier': supplier
        })
    
    # GET request
    return render(request, 'supplier_update.html', {
        'supplier_form': supplier_form,
        'supplier': supplier
    })

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
def purchase_create(request):
    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    purchase = form.save(commit=False)
                    
                    # Get the supplier
                    supplier = purchase.supplier
                    
                    # Validate and set supplier-specific fields
                    if purchase.supplier_product != supplier.product:
                        raise ValueError("Selected product does not match supplier's product")
                    if purchase.supplier_category != supplier.category:
                        raise ValueError("Selected category does not match supplier's category")
                    
                    # Set price from supplier
                    purchase.price_per_unit = supplier.price
                    
                    # Validate quantity
                    if purchase.quantity > supplier.quantity:
                        raise ValueError("Requested quantity exceeds supplier's available quantity")
                    
                    # Get or create corresponding Product and Category
                    category, _ = Category.objects.get_or_create(
                        name=supplier.category,
                        defaults={
                            'description': f'Category for {supplier.category}',
                            'status': 'ACTIVE'
                        }
                    )
                    
                    product, _ = Product.objects.get_or_create(
                        product_name=supplier.product,
                        category=category,
                        defaults={
                            'description': f'Product from {supplier.supplier_name}',
                            'status': 'ACTIVE',
                            'price': supplier.price,
                            'quantity': 0
                        }
                    )
                    
                    # Set the relationships
                    purchase.category = category
                    purchase.product = product
                    
                    # Calculate total amount
                    purchase.total_amount = purchase.quantity * purchase.price_per_unit
                    
                    # Save the purchase
                    purchase.save()
                    
                    messages.success(request, 'Purchase created successfully.')
                    return redirect('inventory:purchase_list')
                    
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error creating purchase: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PurchaseForm()

    return render(request, 'purchase_create.html', {
        'form': form,
        'title': 'Create Purchase'
    })

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

    context = {
        'form': form,
    }

    return render(request, 'purchase_update.html', context)

@login_required(login_url="/authentication/login/")
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        purchase.delete()
        messages.success(request, 'Purchase deleted successfully.')
        return redirect('inventory:purchase_list')
    return render(request, 'purchase_delete.html', {'purchase': purchase})

@login_required(login_url="/authentication/login/")
def get_supplier_products(request):
    supplier_id = request.GET.get('supplier')
    if not supplier_id:
        return JsonResponse({'products': []})
    
    try:
        supplier = Supplier.objects.filter(
            id=supplier_id,
            status=Supplier.ACTIVE
        ).values('id', 'product', 'category', 'price', 'quantity').first()
        
        if supplier:
            # Format the response to match the expected structure
            product_data = {
                'id': supplier['id'],
                'product_name': supplier['product'],
                'category': supplier['category'],
                'price': float(supplier['price']),
                'quantity': supplier['quantity']
            }
            return JsonResponse({'products': [product_data]})
        return JsonResponse({'products': []})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)