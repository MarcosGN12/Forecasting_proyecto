"""
Generador de deals de CRM.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid


def generate_crm_deals(company: dict, start_date: datetime, end_date: datetime,
                       config: dict) -> pd.DataFrame:
    """Genera deals de CRM simulados."""
    
    crm_config = config['crm']
    customers = company['customers']
    
    deals = []
    deal_counter = 0
    
    dates = pd.date_range(start_date, end_date, freq='W')
    
    for date in dates:
        new_deals = np.random.poisson(crm_config['monthly_deals_created'] / 4)
        
        for _ in range(new_deals):
            deal_counter += 1
            
            customer = np.random.choice(customers)
            
            stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'won', 'lost']
            stage_weights = [0.20, 0.25, 0.20, 0.15, 0.10, 0.10]
            stage = np.random.choice(stages, p=stage_weights)
            
            base_amount = customer.get('facturacion_anual', 750000) / 12
            expected_amount = base_amount * np.random.uniform(0.5, 2.0)
            
            created_date = date
            expected_close = date + timedelta(days=np.random.randint(30, 120))
            
            if stage in ['won', 'lost']:
                actual_close = expected_close - timedelta(days=np.random.randint(0, 15))
                closed_date = actual_close
                probability = 1.0 if stage == 'won' else 0.0
            else:
                actual_close = None
                closed_date = None
                probability = {
                    'prospecting': 0.10,
                    'qualification': 0.25,
                    'proposal': 0.50,
                    'negotiation': 0.75
                }.get(stage, 0.0)
            
            deal_name = f"Oportunidad_{deal_counter:04d} - {customer['nombre'][:15]}"
            
            deals.append({
                'deal_id': f'DEAL-{deal_counter:05d}',
                'deal_name': deal_name,
                'customer_id': customer['nombre'][:8].upper().replace(' ', '_'),
                'customer_name': customer['nombre'],
                'stage': stage,
                'probability': round(probability, 2),
                'expected_amount': round(expected_amount, 2),
                'expected_close': expected_close.strftime('%Y-%m-%d'),
                'actual_close': actual_close.strftime('%Y-%m-%d') if actual_close else None,
                'created_date': created_date.strftime('%Y-%m-%d'),
                'closed_date': closed_date.strftime('%Y-%m-%d') if closed_date else None
            })
    
    deals_df = pd.DataFrame(deals)
    
    won_deals = deals_df[deals_df['stage'] == 'won']
    conversion_rate = crm_config['win_rate']
    
    expected_revenue = won_deals['expected_amount'].sum()
    
    return deals_df