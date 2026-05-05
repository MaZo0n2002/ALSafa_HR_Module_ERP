import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from accounts.decorators import role_required
from .models import Payslip, Earning, Deduction
from .forms import EarningForm, DeductionForm

@login_required
@role_required(['Admin', 'HR'])
def payslip_list(request):
    payslips = Payslip.objects.select_related('employee').order_by('-year', '-month')
    return render(request, 'payroll/list.html', {'payslips': payslips})

@login_required
@role_required(['Admin', 'HR'])
def earning_list(request):
    earnings = Earning.objects.all().order_by('-date')
    return render(request, 'payroll/earning_list.html', {'earnings': earnings})

@login_required
@role_required(['Admin', 'HR'])
def earning_add(request):
    if request.method == 'POST':
        form = EarningForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Earning added successfully.")
            return redirect('payroll:earning_list')
    else:
        form = EarningForm()
    return render(request, 'payroll/component_form.html', {'form': form, 'title': 'Add Earning'})

@login_required
@role_required(['Admin', 'HR'])
def deduction_list(request):
    deductions = Deduction.objects.all().order_by('-date')
    return render(request, 'payroll/deduction_list.html', {'deductions': deductions})

@login_required
@role_required(['Admin', 'HR'])
def deduction_add(request):
    if request.method == 'POST':
        form = DeductionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Deduction added successfully.")
            return redirect('payroll:deduction_list')
    else:
        form = DeductionForm()
    return render(request, 'payroll/component_form.html', {'form': form, 'title': 'Add Deduction'})

@login_required
@role_required(['Admin', 'HR'])
def import_payroll_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        if not file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Please upload a valid Excel file.")
            return redirect('payroll:import_excel')
            
        try:
            df = pd.read_excel(file)
            required_cols = ['employee_code', 'type', 'category', 'amount']
            if not all(col in df.columns for col in required_cols):
                messages.error(request, f"Missing columns. Required: {', '.join(required_cols)}")
                return redirect('payroll:import_excel')

            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    emp_code = str(row['employee_code']).strip()
                    comp_type = str(row['type']).strip()
                    category = str(row['category']).strip().capitalize()
                    amount = float(row['amount'])
                    
                    if amount <= 0:
                        error_count += 1
                        continue
                        
                    employee = Employee.objects.filter(employee_code=emp_code).first()
                    if not employee:
                        error_count += 1
                        continue
                        
                    if category == 'Earning':
                        Earning.objects.create(employee=employee, type=comp_type, amount=amount)
                    elif category == 'Deduction':
                        Deduction.objects.create(employee=employee, type=comp_type, amount=amount)
                    else:
                        error_count += 1
                        continue
                        
                    success_count += 1
                except Exception:
                    error_count += 1
                    
            messages.success(request, f"Import complete: {success_count} success, {error_count} errors.")
            return redirect('payroll:list')
            
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            
    return render(request, 'payroll/import.html')

@login_required
@role_required(['Admin', 'HR'])
def download_payroll_template(request):
    # Create a simple Excel template
    df = pd.DataFrame(columns=['employee_code', 'type', 'category', 'amount'])
    # Add an example row
    df.loc[0] = ['EMP001', 'Bonus', 'Earning', 1000]
    df.loc[1] = ['EMP001', 'Late', 'Deduction', 50]
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=payroll_import_template.xlsx'
    
    df.to_excel(response, index=False)
    return response
