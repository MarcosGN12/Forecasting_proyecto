"""
Generador de facturas (ERP simulado).
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid


def generate_invoices(company: dict, start_date: datetime, end_date: datetime, 
                     config: dict) -> pd.DataFrame:
    """Genera facturas simuladas para la empresa."""
    
    fin_config = config['financial']
    invoice_config = config['invoices']
    seasonality = company['seasonality']
    
    customers = company['customers']
    top_5_customers = customers[:5]
    
    dates = pd.date_range(start_date, end_date, freq='D')
    
    invoices = []
    
    invoice_counter = 0
    
    for date in dates:
        month = date.month
        seasonal_factor = seasonality[month]
        
        base_daily_income = fin_config['avg_monthly_income'] / 30
        daily_income = base_daily_income * seasonal_factor
        daily_income += np.random.normal(0, fin_config['income_std_dev'] / 30)
        
        if daily_income <= 0:
            daily_income = base_daily_income * 0.5
        
        while daily_income > 5000:
            amount = min(np.random.uniform(1000, 15000), daily_income)
            
            customer = np.random.choice(top_5_customers)
            ciclo_pago = customer['ciclo_pago']
            
            invoice_date = date
            due_date = date + timedelta(days=ciclo_pago)
            
            prob_paid = 0.85
            status_roll = np.random.random()
            
            if status_roll < prob_paid:
                status = 'paid'
                days_to_pay = int(np.random.uniform(0, ciclo_pago))
                paid_date = invoice_date + timedelta(days=days_to_pay)
                payment_method = np.random.choice(
                    ['transfer', 'confirming', 'receipt'],
                    p=[0.5, 0.3, 0.2]
                )
            elif status_roll < prob_paid + 0.10:
                status = 'pending'
                paid_date = None
                payment_method = np.random.choice(['transfer', 'confirming'])
            else:
                status = 'overdue'
                paid_date = None
                payment_method = np.random.choice(['transfer', 'confirming'])
            
            vat = amount * invoice_config['vat_rate']
            total = amount + vat
            
            invoice_counter += 1
            
            invoices.append({
                'invoice_id': f'INV-{invoice_counter:06d}',
                'invoice_date': invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'customer_id': customer['nombre'][:8].upper().replace(' ', '_'),
                'customer_name': customer['nombre'],
                'amount': round(amount, 2),
                'vat': round(vat, 2),
                'total': round(total, 2),
                'status': status,
                'paid_date': paid_date.strftime('%Y-%m-%d') if paid_date else None,
                'payment_method': payment_method,
                'category': 'product'
            })
            
            daily_income -= amount
        
        extra_invoices = np.random.poisson(0.3)
        for _ in range(extra_invoices):
            if np.random.random() < 0.3:
                amount = np.random.uniform(500, 3000)
                
                customer = np.random.choice(customers)
                ciclo_pago = customer.get('ciclo_pago', 30)
                
                invoice_date = date
                due_date = date + timedelta(days=ciclo_pago)
                
                status = 'paid' if np.random.random() < 0.9 else 'pending'
                paid_date = (invoice_date + timedelta(days=np.random.randint(5, ciclo_pago))) \
                          if status == 'paid' else None
                
                vat = amount * invoice_config['vat_rate']
                total = amount + vat
                
                invoice_counter += 1
                
                invoices.append({
                    'invoice_id': f'INV-{invoice_counter:06d}',
                    'invoice_date': invoice_date.strftime('%Y-%m-%d'),
                    'due_date': due_date.strftime('%Y-%m-%d'),
                    'customer_id': customer['nombre'][:8].upper().replace(' ', '_'),
                    'customer_name': customer['nombre'],
                    'amount': round(amount, 2),
                    'vat': round(vat, 2),
                    'total': round(total, 2),
                    'status': status,
                    'paid_date': paid_date.strftime('%Y-%m-%d') if paid_date else None,
                    'payment_method': 'transfer',
                    'category': 'service'
                })
    
    return pd.DataFrame(invoices)