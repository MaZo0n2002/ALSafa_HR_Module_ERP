import pandas as pd
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from accounts.decorators import role_required
from .models import Payslip, Earning, Deduction
from .forms import EarningForm, DeductionForm
from employees.models import Employee

@login_required
@role_required(['Admin', 'HR'])
def payslip_list(request):
    q = request.GET.get('q', '')
    payslips = Payslip.objects.select_related('employee').order_by('-year', '-month')
    
    if q:
        payslips = payslips.filter(
            Q(employee__full_name__icontains=q) | 
            Q(employee__employee_code__icontains=q)
        )
        
    if request.user.branch:
        payslips = payslips.filter(employee__branch=request.user.branch)
    
    # We keep the context for the form, but don't filter the list itself by month/year
    # unless we add a specific filter UI later.
    now = timezone.now()
    return render(request, 'payroll/list.html', {
        'payslips': payslips, 
        'query': q,
        'current_month': int(request.GET.get('month', now.month)),
        'current_year': int(request.GET.get('year', now.year))
    })

@login_required
@role_required(['Admin', 'HR'])
def earning_list(request):
    earnings = Earning.objects.all().order_by('-date')
    if request.user.branch:
        earnings = earnings.filter(employee__branch=request.user.branch)
    return render(request, 'payroll/earning_list.html', {'earnings': earnings})

@login_required
@role_required(['Admin', 'HR'])
def earning_add(request):
    if request.method == 'POST':
        form = EarningForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Earning added successfully.")
            return redirect('payroll:earning_list')
    else:
        form = EarningForm(user=request.user)
    return render(request, 'payroll/component_form.html', {'form': form, 'title': 'Add Earning'})

@login_required
@role_required(['Admin', 'HR'])
def earning_edit(request, pk):
    earning = get_object_or_404(Earning, pk=pk)
    if request.user.branch and earning.employee.branch != request.user.branch:
        messages.error(request, "Permission denied.")
        return redirect('payroll:earning_list')
        
    if request.method == 'POST':
        form = EarningForm(request.POST, instance=earning, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Earning updated successfully.")
            return redirect('payroll:earning_list')
    else:
        form = EarningForm(instance=earning, user=request.user)
    return render(request, 'payroll/component_form.html', {'form': form, 'title': 'Edit Earning', 'edit_mode': True})

@login_required
@role_required(['Admin', 'HR'])
def earning_delete(request, pk):
    earning = get_object_or_404(Earning, pk=pk)
    if request.user.branch and earning.employee.branch != request.user.branch:
        messages.error(request, "Permission denied.")
    else:
        earning.delete()
        messages.success(request, "Earning deleted successfully.")
    return redirect('payroll:earning_list')

@login_required
@role_required(['Admin', 'HR'])
def deduction_list(request):
    deductions = Deduction.objects.all().order_by('-date')
    if request.user.branch:
        deductions = deductions.filter(employee__branch=request.user.branch)
    return render(request, 'payroll/deduction_list.html', {'deductions': deductions})

@login_required
@role_required(['Admin', 'HR'])
def deduction_add(request):
    if request.method == 'POST':
        form = DeductionForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Deduction added successfully.")
            return redirect('payroll:deduction_list')
    else:
        form = DeductionForm(user=request.user)
    return render(request, 'payroll/component_form.html', {'form': form, 'title': 'Add Deduction'})

@login_required
@role_required(['Admin', 'HR'])
def deduction_edit(request, pk):
    deduction = get_object_or_404(Deduction, pk=pk)
    if request.user.branch and deduction.employee.branch != request.user.branch:
        messages.error(request, "Permission denied.")
        return redirect('payroll:deduction_list')
        
    if request.method == 'POST':
        form = DeductionForm(request.POST, instance=deduction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Deduction updated successfully.")
            return redirect('payroll:deduction_list')
    else:
        form = DeductionForm(instance=deduction, user=request.user)
    return render(request, 'payroll/component_form.html', {'form': form, 'title': 'Edit Deduction', 'edit_mode': True})

@login_required
@role_required(['Admin', 'HR'])
def deduction_delete(request, pk):
    deduction = get_object_or_404(Deduction, pk=pk)
    if request.user.branch and deduction.employee.branch != request.user.branch:
        messages.error(request, "Permission denied.")
    else:
        deduction.delete()
        messages.success(request, "Deduction deleted successfully.")
    return redirect('payroll:deduction_list')

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

@login_required
@role_required(['Admin', 'HR'])
@login_required
@role_required(['Admin', 'HR'])
def recalculate_payslip(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    if request.user.branch and payslip.employee.branch != request.user.branch:
        messages.error(request, "Permission denied.")
        return redirect('payroll:list')
    
    payslip.save() 
    messages.success(request, f"Financial data for {payslip.employee.full_name} has been synchronized and recalculated.")
    return redirect('payroll:detail', pk=pk)

@login_required
@role_required(['Admin', 'HR'])
def payslip_detail(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    if request.user.branch and payslip.employee.branch != request.user.branch:
        messages.error(request, "You do not have permission to view this payslip.")
        return redirect('payroll:list')
    
    earnings = Earning.objects.filter(employee=payslip.employee, date__month=payslip.month, date__year=payslip.year)
    deductions = Deduction.objects.filter(employee=payslip.employee, date__month=payslip.month, date__year=payslip.year)
    
    return render(request, 'payroll/detail.html', {
        'payslip': payslip,
        'earnings': earnings,
        'deductions': deductions
    })

@login_required
@role_required(['Admin', 'HR'])
def export_payroll_excel(request):
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    
    payslips = Payslip.objects.filter(month=month, year=year).select_related('employee', 'employee__branch')
    if request.user.branch:
        payslips = payslips.filter(employee__branch=request.user.branch)
        
    data = []
    for slip in payslips:
        data.append({
            'Employee Code': slip.employee.employee_code,
            'Full Name': slip.employee.full_name,
            'Branch': slip.employee.branch.name if slip.employee.branch else 'Global',
            'Basic Salary': slip.employee.basic_salary,
            'Overtime Earnings': slip.overtime_earnings,
            'Other Earnings': slip.total_earnings - slip.employee.basic_salary - slip.overtime_earnings,
            'Total Earnings': slip.total_earnings,
            'Late Deductions': slip.attendance_late_deduction,
            'Absence Deductions': slip.attendance_absence_deduction,
            'Loan Installments': slip.loan_installment_deduction,
            'Other Deductions': slip.total_deductions - slip.attendance_late_deduction - slip.attendance_absence_deduction - slip.loan_installment_deduction,
            'Total Deductions': slip.total_deductions,
            'Net Salary': slip.net_salary,
            'Status': slip.status
        })
        
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=payroll_{month}_{year}.xlsx'
    
    df.to_excel(response, index=False)
    return response

@login_required
@role_required(['Admin', 'HR'])
def generate_payroll(request):
    if request.method == 'POST':
        month = int(request.POST.get('month', timezone.now().month))
        year = int(request.POST.get('year', timezone.now().year))
        
        employees = Employee.objects.filter(is_active=True)
        if request.user.branch:
            employees = employees.filter(branch=request.user.branch)
            
        created_count = 0
        for emp in employees:
            # Check if already exists
            if not Payslip.objects.filter(employee=emp, month=month, year=year).exists():
                Payslip.objects.create(
                    employee=emp,
                    month=month,
                    year=year,
                    status='Draft'
                )
                created_count += 1
        
        messages.success(request, f"Generated {created_count} payslips for {month}/{year}.")
        return redirect(f"{reverse('payroll:list')}?month={month}&year={year}")
    
    return redirect('payroll:list')
