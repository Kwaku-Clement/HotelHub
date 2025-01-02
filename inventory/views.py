from datetime import datetime, timezone
from django.http import HttpRequest, HttpResponse, JsonResponse
from .models import Category, InventoryMiscellaneous, Product, Supplier,  Purchase, SupplierProduct
from .forms import InventoryMiscellaneousForm, SupplierForm, PurchaseForm, CategoryForm, ProductForm, SupplierProductForm
from .utils import save_form_with_transaction, handle_error, handle_success, delete_instance_with_error_handling
import logging
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, Product, Supplier, Purchase
from .forms import SupplierForm, PurchaseForm, CategoryForm, ProductForm, SupplierProductForm
from django.forms import ValidationError, modelformset_factory
from django.db import transaction
from django.contrib import messages


logger = logging.getLogger(__name__)

@login_required(login_url="/authentication/login/")
def home_view(request):
    return render(request, 'home.html')

@login_required(login_url="/authentication/login/")
def categories_list_view(request):
    try:
        categories = Category.objects.all()
        return render(request, "category_list.html", {"categories": categories})
    except Exception as e:
        handle_error(request, f"Error loading categories: {str(e)}")
        return redirect('inventory:category_create_update')

@login_required(login_url="/authentication/login/")
def category_create_update(request, category_id=None):
    if category_id:
        category = get_object_or_404(Category, id=category_id)
        title = "Update Category"
    else:
        category = None
        title = "Create Category"

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category, error = save_form_with_transaction(form)
            if error:
                handle_error(request, error)
                return redirect('inventory:category_create_update', category_id=category.id if category else None)
            
            handle_success(request, f"Category '{category.name}' saved successfully!")
            return redirect('inventory:category_list')
        else:
            handle_error(request, 'Invalid form submission!')

    else:
        form = CategoryForm(instance=category)

    context = {
        "active_icon": "products_categories",
        "category_status": Category.STATUS_CHOICES,
        "form": form,
        "title": title
    }
    return render(request, "category_create_update.html", context=context)

@login_required(login_url="/authentication/login/")
def categories_delete_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    delete_instance_with_error_handling(
        request, 
        category, 
        success_message=f'Category: {category.name} deleted!', 
        failure_message='Error deleting category'
    )
    return redirect('inventory:category_list')

@login_required(login_url="/authentication/login/")
def products_list_view(request):
    try:
        products = Product.objects.all()
        return render(request, "product_list.html", {"products": products})
    except Exception as e:
        handle_error(request, f"Error loading products: {str(e)}")
        return redirect('inventory:product_create_update')

@login_required(login_url="/authentication/login/")
def product_create_update(request, product_id=None):
    if product_id:
        product = get_object_or_404(Product, id=product_id)
        title = "Update Product"
    else:
        product = None
        title = "Create Product"

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product, error = save_form_with_transaction(form)
            if error:
                handle_error(request, error)
                return redirect('inventory:product_create_update', product_id=product.id if product else None)

            handle_success(request, f'Product: {product.product_name} saved successfully!')
            return redirect('inventory:product_list')
        else:
            handle_error(request, 'Invalid form submission!')

    else:
        form = ProductForm(instance=product)

    context = {
        "active_icon": "products",
        "product_status": Product.STATUS_CHOICES,
        "categories": Category.objects.filter(status="ACTIVE"),
        "form": form,
        "title": title
    }
    return render(request, "product_create_update.html", context=context)

@login_required(login_url="/authentication/login/")
def products_delete_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    delete_instance_with_error_handling(
        request, 
        product, 
        success_message=f'Product: {product.product_name} deleted!', 
        failure_message='Error deleting product'
    )
    return redirect('inventory:product_list')

@login_required(login_url="/authentication/login/")
def supplier_list(request):
    try:
        suppliers = Supplier.objects.all()
        return render(request, "supplier_list.html", {"suppliers": suppliers})
    except Exception as e:
        handle_error(request, f"Error loading suppliers: {str(e)}")
        return redirect('inventory:supplier_create_update')

from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.forms import modelformset_factory
from .models import Supplier, SupplierProduct
from .forms import SupplierForm, SupplierProductForm
from .utils import handle_success, handle_error

@login_required(login_url="/authentication/login/")
def supplier_create_update(request, pk=None):
    SupplierProductFormSet = modelformset_factory(
        SupplierProduct, 
        form=SupplierProductForm, 
        extra=1, 
        can_delete=True
    )

    if pk:
        supplier = get_object_or_404(Supplier, pk=pk)
        supplier_products = supplier.supplier_products.all()
        title = "Update Supplier"
    else:
        supplier = None
        supplier_products = SupplierProduct.objects.none()
        title = "Create Supplier"

    if request.method == 'POST':
        supplier_form = SupplierForm(request.POST, instance=supplier)
        product_formset = SupplierProductFormSet(request.POST)

        if supplier_form.is_valid() and product_formset.is_valid():
            try:
                with transaction.atomic():
                    supplier_name = supplier_form.cleaned_data['supplier_name']
                    contact_info = supplier_form.cleaned_data['contact_info']

                    # Look for existing supplier
                    existing_supplier = Supplier.objects.filter(
                        supplier_name=supplier_name,
                        contact_info=contact_info
                    ).first()

                    if existing_supplier and not pk:
                        supplier = existing_supplier
                    else:
                        supplier = supplier_form.save()

                    for product_form in product_formset:
                        if product_form.cleaned_data:
                            product_name = product_form.cleaned_data.get('product_name')
                            price = product_form.cleaned_data.get('price')
                            quantity = product_form.cleaned_data.get('quantity')
                            category_name = product_form.cleaned_data.get('category_name')
                            delete = product_form.cleaned_data.get('DELETE', False)

                            existing_product = SupplierProduct.objects.filter(
                                supplier=supplier,
                                product_name=product_name,
                                category_name=category_name
                            ).first()

                            if delete and existing_product:
                                existing_product.delete()
                            elif existing_product:
                                # Update existing product details and stock
                                existing_product.quantity += quantity
                                existing_product.price = price
                                existing_product.save()
                            elif not delete:
                                # Create new product
                                product = product_form.save(commit=False)
                                product.supplier = supplier
                                product.save()

                handle_success(request, f'Supplier {supplier.supplier_name} and products updated successfully.')
                return redirect('inventory:supplier_list')

            except Exception as e:
                handle_error(request, f'Error saving supplier: {str(e)}')
                return redirect('inventory:supplier_create_update', pk=pk)
        else:
            handle_error(request, 'Please correct the form errors.')
            print(supplier_form.errors)
            print(product_formset.errors)
    else:
        supplier_form = SupplierForm(instance=supplier)
        product_formset = SupplierProductFormSet(queryset=supplier_products)

    return render(request, 'supplier_create_update.html', {
        'supplier_form': supplier_form,
        'product_formset': product_formset,
        'title': title
    })
    
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if supplier.supplier_products.exists() or supplier.purchases.exists():
        handle_error(request, "Cannot delete supplier because it has associated products or purchases.")
        return redirect('inventory:supplier_list')

    supplier.delete()
    return redirect('inventory:supplier_list')

@login_required(login_url="/authentication/login/")
def purchase_list(request):
    try:
        purchases = Purchase.objects.all()
        return render(request, "purchase_list.html", {"purchases": purchases})
    except Exception as e:
        handle_error(request, f"Error loading purchases: {str(e)}")
        return redirect('inventory:purchase_create_update')


@login_required(login_url="/authentication/login/")
def purchase_create_update(request, pk=None):
    if pk:
        purchase = get_object_or_404(Purchase, pk=pk)
        title = "Update Purchase"
    else:
        purchase = None
        title = "Create Purchase"

    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            try:
                purchase = form.save()
                messages.success(request, 'Purchase saved successfully.')
                return redirect('inventory:purchase_list')
            except ValidationError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Please correct the form errors.')
    else:
        form = PurchaseForm(instance=purchase)

    return render(request, 'purchase_create_update.html', {
        'form': form,
        'title': title
    })

@login_required(login_url="/authentication/login/")
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    delete_instance_with_error_handling(
        request, 
        purchase, 
        success_message='Purchase deleted successfully.',
        failure_message='Error deleting purchase'
    )
    return redirect('inventory:purchase_list')


@login_required(login_url="/authentication/login/")
def get_supplier_products(request, supplier_id):
    # Check if request is AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    products = SupplierProduct.objects.filter(supplier_id=supplier_id)
    data = [{
        'id': product.id,
        'product_name': product.product_name,
        'price': str(product.price),
        'quantity': product.quantity
    } for product in products]
    
    return JsonResponse(data, safe=False)

@login_required(login_url="/authentication/login/")
def get_supplier_product_details(request, product_id):
    # Check if request is AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        product = SupplierProduct.objects.get(id=product_id)
        data = {
            'id': product.id,
            'product_name': product.product_name,
            'category_name': product.category_name,
            'price': str(product.price),
            'quantity': product.quantity
        }
        return JsonResponse(data)
    except SupplierProduct.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    
    
@login_required(login_url="/authentication/login/")
def miscellaneous_create_update(request: HttpRequest, misc_id=None) -> HttpResponse:
    if misc_id:
        miscellaneous = get_object_or_404(InventoryMiscellaneous, id=misc_id)
        title = "Update Miscellaneous"
    else:
        miscellaneous = None
        title = "Add Miscellaneous"

    if request.method == "POST":
        form = InventoryMiscellaneousForm(request.POST, instance=miscellaneous)
        if form.is_valid():
            miscellaneous, error = save_form_with_transaction(form)
            if error:
                handle_error(request, error)
                return redirect('inventory:miscellaneous_create_update', misc_id=miscellaneous.id if miscellaneous else None)
            handle_success(request, f"Miscellaneous '{miscellaneous.title}' saved successfully!")
            return redirect('inventory:inventory_miscellaneous_list')
        else:
            handle_error(request, "Invalid form submission!")
    else:
        form = InventoryMiscellaneousForm(instance=miscellaneous)

    context = {
        "active_icon": "miscellaneous",
        "miscellaneous_status": InventoryMiscellaneous.TYPE_CHOICES,
        "form": form,
        "title": title
    }

    return render(request, 'miscellaneous_create_update.html', context)


@login_required(login_url="/authentication/login/")
def inventory_miscellaneous_list(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    try:
        miscellaneous = InventoryMiscellaneous.objects.all()
        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            miscellaneous = miscellaneous.filter(date__range=(start_date, end_date))
        return render(request, "inventory_miscellaneous_list.html", {"miscellaneous": miscellaneous})
    
    except Exception as e:
        handle_error(request, f"Error loading miscellaneous: {str(e)}")
        return redirect('inventory:miscellaneous_create_update')


@login_required(login_url="/authentication/login/")
def miscellaneous_delete_view(request, misc_id):
    miscellaneous = get_object_or_404(InventoryMiscellaneous, id=misc_id)
    delete_instance_with_error_handling(
        request, miscellaneous, success_message=f"Miscellaneous: {miscellaneous.type} deleted!",
        failure_message='Error occurred while deleting Miscellaneous'
    )
    return redirect('inventory:inventory_miscellaneous_list')
