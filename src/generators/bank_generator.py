"""
Generador de movimientos bancarios.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid


def generate_bank_movements(invoices: pd.DataFrame, company: dict,
                            start_date: datetime, end_date: datetime,
                            config: dict) -> pd.DataFrame:
    """Genera movimientos bancarios simulados."""
    
    movements = []
    
    initial_balance = config['financial']['initial_balance']
    current_balance = initial_balance
    
    dates = pd.date_range(start_date, end_date, freq='D')
    
    paid_invoices = invoices[invoices['paid_date'].notna()].copy()
    paid_invoices['paid_date_dt'] = pd.to_datetime(paid_invoices['paid_date'])
    
    invoice_movements = []
    for _, inv in paid_invoices.iterrows():
        invoice_movements.append({
            'date': inv['paid_date_dt'],
            'amount': inv['total'],
            'description': f"Cobro factura {inv['invoice_id']} - {inv['customer_name']}",
            'category': 'invoice_payment',
            'reference': inv['invoice_id']
        })
    
    employees = company.get('employees', 65)
    monthly_payroll = employees * 2400 * 1.32
    payroll_days = []
    
    year = start_date.year
    month = start_date.month
    current_month = month
    
    while True:
        payroll_date = datetime(year, current_month, 1)
        day = 1
        
        while payroll_date.weekday() > 4:
            day += 1
            payroll_date = datetime(year, current_month, day)
        
        if payroll_date >= start_date and payroll_date <= end_date:
            payroll_days.append(payroll_date)
        
        current_month += 1
        if current_month > 12:
            current_month = 1
            year += 1
        
        if payroll_date > end_date:
            break
    
    for pd_date in payroll_days:
        invoice_movements.append({
            'date': pd_date,
            'amount': -monthly_payroll,
            'description': "Nómina mensual - Industrial Metálica Portillo",
            'category': 'salary',
            'reference': None
        })
    
    supplier_payments = [
        ('MetalSteel S.A.', 125000, 90),
        ('Recambios Express S.L.', 33000, 30),
        ('Energía Castilla', 29000, 15),
        ('Embalajes Toledo S.L.', 17000, 60),
        ('Servicios Logs S.L.', 15000, 30),
    ]
    
    current_date = start_date
    while current_date <= end_date:
        for supplier, amount, cycle in supplier_payments:
            if current_date.day == 1 or np.random.random() < 0.03:
                adjusted_amount = amount * (1 + np.random.uniform(-0.1, 0.1))
                
                invoice_movements.append({
                    'date': current_date,
                    'amount': -adjusted_amount,
                    'description': f"Pago proveedor {supplier}",
                    'category': 'supplier',
                    'reference': None
                })
        
        current_date += timedelta(days=30)
    
    iva_dates = [
        datetime(2023, 4, 20), datetime(2023, 7, 20),
        datetime(2023, 10, 20), datetime(2024, 1, 20),
        datetime(2024, 4, 20), datetime(2024, 7, 20),
        datetime(2024, 10, 20), datetime(2025, 1, 20),
        datetime(2025, 4, 20), datetime(2025, 7, 20),
        datetime(2025, 10, 20),
    ]
    
    for iva_date in iva_dates:
        if start_date <= iva_date <= end_date:
            iva_amount = np.random.uniform(35000, 55000)
            
            invoice_movements.append({
                'date': iva_date,
                'amount': -iva_amount,
                'description': "IVA trimestral",
                'category': 'tax',
                'reference': None
            })
    
    seguro_social_dates = [
        datetime(2023, 1, 30), datetime(2023, 2, 28),
        datetime(2023, 3, 30), datetime(2023, 4, 28),
    ]
    
    current_year = start_date.year
    current_month = start_date.month
    
    while True:
        ss_date = datetime(current_year, current_month, 28)
        
        if start_date <= ss_date <= end_date:
            employees = company.get('employees', 65)
            ss_amount = employees * 2400 * 0.12
            
            invoice_movements.append({
                'date': ss_date,
                'amount': -ss_amount,
                'description': "Cotización Seguridad Social",
                'category': 'tax',
                'reference': None
            })
        
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1
        
        if ss_date > end_date:
            break
    
    utility_payments = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.month in [2, 5, 8, 11]:
            utility_payments.append({
                'date': current_date,
                'amount': -np.random.uniform(8000, 12000),
                'description': "Factura electricidad",
                'category': 'utility',
                'reference': None
            })
        
        if current_date.month in [3, 6, 9, 12]:
            utility_payments.append({
                'date': current_date,
                'amount': -np.random.uniform(2000, 4000),
                'description': "Factura gas natural",
                'category': 'utility',
                'reference': None
            })
        
        current_date += timedelta(days=30)
    
    all_movements = invoice_movements + utility_payments
    
    for date in dates:
        if date.day == 15:
            all_movements.append({
                'date': date,
                'amount': -np.random.uniform(2000, 5000),
                'description': "Alquiler nave industrial",
                'category': 'other',
                'reference': None
            })
    
    movements_df = pd.DataFrame(all_movements)
    
    movements_df = movements_df.sort_values('date')
    
    cumulative = movements_df['amount'].cumsum()
    movements_df['balance_after'] = initial_balance + cumulative
    
    movements_df['value_date'] = movements_df['date']
    
    movements_df['bank_account'] = 'ES7621000000001234567890'
    
    movements_df['movement_id'] = [str(uuid.uuid4()) for _ in range(len(movements_df))]
    
    movements_df = movements_df[['movement_id', 'date', 'value_date', 'description',
                                   'amount', 'balance_after', 'category', 'reference',
                                   'bank_account']]
    
    return movements_df