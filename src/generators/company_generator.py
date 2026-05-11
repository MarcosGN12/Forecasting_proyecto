"""
Generador de datos de empresa, empleados, proveedores y factores externos.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yaml
import uuid


def load_company_config() -> dict:
    """Carga configuración de la empresa."""
    with open("config/empresa.yaml", 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_company() -> dict:
    """Genera datos básicos de la empresa simulada."""
    config = load_company_config()
    emp = config['empresa']
    
    company = {
        'name': emp['nombre'],
        'cif': emp['cif'],
        'address': emp['direccion'],
        'sector': emp['sector'],
        'employees': emp['empleados'],
        'annual_revenue': emp['facturacion_anual'],
        'tesoreria': config['tesoreria'],
        'ciclos': config['ciclos'],
        'seasonality': config['estacionalidad']['factor'],
        'customers': config['clientes'],
        'suppliers': config['proveedores']
    }
    
    return company


def generate_employees(company: dict, config: dict) -> pd.DataFrame:
    """Genera empleados simulados."""
    emp_config = config['employees']
    
    departments = ['production', 'admin', 'sales', 'logistics']
    department_weights = [0.60, 0.20, 0.10, 0.10]
    
    employees = []
    for i in range(emp_config['count']):
        dept = np.random.choice(departments, p=department_weights)
        
        base_salary = emp_config['avg_salary']
        
        if dept == 'production':
            salary = base_salary * np.random.uniform(0.9, 1.3)
        elif dept == 'admin':
            salary = base_salary * np.random.uniform(1.0, 1.5)
        elif dept == 'sales':
            salary = base_salary * np.random.uniform(0.8, 2.0)
        else:
            salary = base_salary * np.random.uniform(0.85, 1.1)
        
        ss_contribution = salary * emp_config['ss_contribution_rate']
        
        start_year = np.random.randint(2018, 2024)
        start_month = np.random.randint(1, 13)
        start_date = datetime(start_year, start_month, 1)
        
        employees.append({
            'employee_id': str(uuid.uuid4()),
            'name': f"Empleado_{i+1:03d}",
            'department': dept,
            'contract_type': 'permanent' if np.random.random() > 0.1 else 'temporary',
            'salary': round(salary, 2),
            'ss_contribution': round(ss_contribution, 2),
            'start_date': start_date.strftime('%Y-%m-%d')
        })
    
    return pd.DataFrame(employees)


def generate_suppliers(company: dict) -> pd.DataFrame:
    """Genera proveedores simulados."""
    base_suppliers = company['suppliers']
    
    all_suppliers = []
    for s in base_suppliers:
        all_suppliers.append({
            'supplier_id': str(uuid.uuid4()),
            'name': s['nombre'],
            'category': s['categoria'],
            'payment_cycle': s['ciclo_pago'],
            'typical_amount': s['gasto_anual'] / 12
        })
    
    extra_categories = ['logistics', 'maintenance', 'it', 'consulting']
    for i, cat in enumerate(extra_categories, start=len(base_suppliers)):
        all_suppliers.append({
            'supplier_id': str(uuid.uuid4()),
            'name': f"Proveedor_{i+1}",
            'category': cat,
            'payment_cycle': np.random.choice([30, 60, 90]),
            'typical_amount': np.random.uniform(5000, 30000)
        })
    
    return pd.DataFrame(all_suppliers)


def generate_external_factors(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Genera factores económicos externos."""
    dates = pd.date_range(start_date, end_date, freq='D')
    
    factors = []
    
    base_interest_rate = 3.5
    for date in dates:
        month = date.month
        
        seasonal_interest = {
            1: 0.1, 2: 0.05, 3: 0.0, 4: -0.05, 5: 0.0,
            6: 0.1, 7: 0.15, 8: 0.1, 9: 0.0, 10: -0.05,
            11: 0.0, 12: 0.05
        }
        
        value = base_interest_rate + seasonal_interest.get(month, 0) + np.random.normal(0, 0.2)
        
        factors.append({
            'date': date.strftime('%Y-%m-%d'),
            'indicator': 'interest_rate',
            'value': round(value, 2),
            'source': 'bank_spain'
        })
    
    base_inflation = 3.0
    for date in dates:
        value = base_inflation + np.random.normal(0, 0.5)
        
        factors.append({
            'date': date.strftime('%Y-%m-%d'),
            'indicator': 'inflation',
            'value': round(value, 2),
            'source': 'ine'
        })
    
    base_growth = 2.0
    for date in dates:
        quarter = (date.month - 1) // 3 + 1
        
        quarterly_growth = {
            1: 1.5, 2: 2.0, 3: 2.5, 4: 2.0
        }
        
        value = quarterly_growth[quarter] + np.random.normal(0, 1)
        
        factors.append({
            'date': date.strftime('%Y-%m-%d'),
            'indicator': 'sector_growth',
            'value': round(value, 2),
            'source': 'market'
        })
    
    return pd.DataFrame(factors)