"""
Tests para generadores de datos sintéticos.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generators import company_generator, invoice_generator, bank_generator, crm_generator


class TestCompanyGenerator:
    """Tests para generador de empresa."""
    
    def test_generate_company(self):
        """Test generación de empresa."""
        company = company_generator.generate_company()
        
        assert 'name' in company
        assert 'cif' in company
        assert company['name'] == 'Industrial Metálica Portillo S.L.'
    
    def test_generate_employees(self):
        """Test generación de empleados."""
        company = company_generator.generate_company()
        
        with open('config/generation_params.yaml', 'r') as f:
            import yaml
            config = yaml.safe_load(f)
        
        employees = company_generator.generate_employees(company, config)
        
        assert len(employees) > 0
        assert 'employee_id' in employees.columns
        assert 'department' in employees.columns


class TestInvoiceGenerator:
    """Tests para generador de facturas."""
    
    def test_generate_invoices(self):
        """Test generación de facturas."""
        from datetime import datetime
        
        company = company_generator.generate_company()
        
        with open('config/generation_params.yaml', 'r') as f:
            import yaml
            config = yaml.safe_load(f)
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        invoices = invoice_generator.generate_invoices(
            company, start_date, end_date, config
        )
        
        assert len(invoices) > 0
        assert 'invoice_id' in invoices.columns
        assert 'total' in invoices.columns
        assert 'status' in invoices.columns


class TestBankGenerator:
    """Tests para generador de movimientos bancarios."""
    
    def test_generate_movements(self):
        """Test generación de movimientos."""
        from datetime import datetime
        
        company = company_generator.generate_company()
        
        with open('config/generation_params.yaml', 'r') as f:
            import yaml
            config = yaml.safe_load(f)
        
        invoices = invoice_generator.generate_invoices(
            company, 
            datetime(2023, 1, 1),
            datetime(2023, 1, 31),
            config
        )
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        movements = bank_generator.generate_bank_movements(
            invoices, company, start_date, end_date, config
        )
        
        assert len(movements) > 0
        assert 'movement_id' in movements.columns
        assert 'balance_after' in movements.columns


class TestCRMGenerator:
    """Tests para generador de CRM."""
    
    def test_generate_deals(self):
        """Test generación de deals."""
        from datetime import datetime
        
        company = company_generator.generate_company()
        
        with open('config/generation_params.yaml', 'r') as f:
            import yaml
            config = yaml.safe_load(f)
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        deals = crm_generator.generate_crm_deals(
            company, start_date, end_date, config
        )
        
        assert len(deals) > 0
        assert 'deal_id' in deals.columns
        assert 'stage' in deals.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])