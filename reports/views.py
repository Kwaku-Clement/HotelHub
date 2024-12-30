from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from inventory.models import Miscellaneous
from reports.report_service import FinancialReportService
from .forms import ReportSelectionForm

def generate_financial_explanation(total_revenue: float, total_expenses: float, profit_loss: float, report_data: dict) -> str:
    # Calculate key metrics
    margin = (profit_loss / total_revenue * 100) if total_revenue > 0 else 0
    expense_ratio = (total_expenses / total_revenue * 100) if total_revenue > 0 else 0

    # Get top performing categories and products
    category_sales = report_data.get('category_sales', [])
    product_sales = report_data.get('product_sales', [])

    top_categories = sorted(category_sales, key=lambda x: x['total_sales'], reverse=True)[:5]
    top_products = sorted(product_sales, key=lambda x: x['total_sales'], reverse=True)[:5]

    # Get top employers
    top_employers = report_data.get('top_employers', [])[:3]

    # Build explanation
    explanation_parts = []

    # Overall Performance
    if profit_loss >= 0:
        explanation_parts.append(
            f"The financial report shows a positive performance with a profit of ${profit_loss:,.2f}, "
            f"representing a profit margin of {margin:.1f}%. "
            f"Total revenue of ${total_revenue:,.2f} exceeded total expenses of ${total_expenses:,.2f}. "
            f"This indicates that the business is generating more income than it is spending, leading to a profit."
        )
    else:
        explanation_parts.append(
            f"The financial report indicates challenges with a loss of ${abs(profit_loss):,.2f}, "
            f"representing a negative margin of {abs(margin):.1f}%. "
            f"Total expenses of ${total_expenses:,.2f} exceeded revenue of ${total_revenue:,.2f}. "
            f"This suggests that the business is spending more than it is earning, resulting in a loss. "
            f"Possible reasons for the loss could include high operational costs, low sales volume, or inefficient inventory management."
        )

    # Expense Analysis
    explanation_parts.append(
        f"The expense-to-revenue ratio is {expense_ratio:.1f}%, "
        f"which means that for every dollar in revenue, ${expense_ratio/100:.2f} is spent on expenses."
    )

    # Top Performers
    explanation_parts.append(f"Top 5 Performing Categories:")
    for category in top_categories:
        explanation_parts.append(f"- {category['category']}: ${category['total_sales']:,.2f}")

    explanation_parts.append(f"Top 5 Performing Products:")
    for product in top_products:
        explanation_parts.append(f"- {product['product']}: ${product['total_sales']:,.2f}")

    explanation_parts.append(f"Top 3 Employers:")
    for employer in top_employers:
        explanation_parts.append(f"- {employer['employer']}: ${employer['total_sales']:,.2f}")

    # Recommendations
    if profit_loss < 0:
        explanation_parts.append(
            "Recommendations:\n"
            "1. Review pricing strategy to improve margins\n"
            "2. Analyze expense patterns to identify potential cost savings\n"
            "3. Focus marketing efforts on high-margin products and categories\n"
            "4. Consider inventory optimization to reduce carrying costs\n"
            "5. Evaluate if the goods in stock are moving as expected. High inventory levels without corresponding sales can lead to increased carrying costs and potential obsolescence."
        )
    else:
        explanation_parts.append(
            "Recommendations:\n"
            "1. Consider scaling successful product lines\n"
            "2. Explore opportunities to further optimize the product mix\n"
            "3. Monitor expense ratios to maintain profitability\n"
            "4. Investigate potential for expansion in top-performing categories"
        )

    return "\n\n".join(explanation_parts)

def generate_report(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ReportSelectionForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            context = {
                'form': form,
                'start_date': start_date,
                'end_date': end_date
            }

            service = FinancialReportService(start_date, end_date)
            report_data = service.generate_report()

            # Calculate financial metrics
            total_revenue = report_data.get('total_sales', 0)
            total_expenses = report_data.get('total_purchases', 0) + report_data.get('other_expenses', 0)
            profit_loss = total_revenue - total_expenses

            # Generate detailed explanation
            explanation = generate_financial_explanation(
                total_revenue,
                total_expenses,
                profit_loss,
                report_data
            )

            # Get miscellaneous expenditures
            miscellaneous_expenses = Miscellaneous.objects.filter(date__range=[start_date, end_date])
            total_miscellaneous = sum(expense.amount for expense in miscellaneous_expenses)

            context.update({
                'report_data': report_data,
                'total_revenue': total_revenue,
                'total_expenses': total_expenses,
                'profit_loss': profit_loss,
                'explanation': explanation,
                'store_name': report_data.get('store_name', 'Unknown Store'),
                'selected_date_range': f"{start_date} to {end_date}",
                'miscellaneous_expenses': miscellaneous_expenses,
                'total_miscellaneous': total_miscellaneous
            })

            return render(request, 'report_detail.html', context)

    else:
        form = ReportSelectionForm()

    return render(request, 'select_report.html', {'form': form})