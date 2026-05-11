"""
Tests para pipeline ETL.
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.etl.extractor import DataExtractor
from src.etl.transformer import DataTransformer


class TestExtractor:
    """Tests para extractor de datos."""
    
    @pytest.fixture
    def extractor(self):
        """Crea extractor."""
        return DataExtractor("data/raw")
    
    def test_load_all(self, extractor):
        """Test carga de todos los datasets."""
        datasets = extractor.load_all()
        
        assert len(datasets) > 0
        assert 'invoices' in datasets
        assert 'bank_movements' in datasets
    
    def test_validate_schema(self, extractor):
        """Test validación de schema."""
        datasets = extractor.load_all()
        
        result = extractor.validate_schema('invoices', datasets['invoices'])
        
        assert result['valid'] == True


class TestTransformer:
    """Tests para transformador de datos."""
    
    @pytest.fixture
    def transformer(self):
        """Crea transformer."""
        return DataTransformer()
    
    @pytest.fixture
    def sample_invoices(self):
        """Datos de ejemplo."""
        return pd.DataFrame({
            'invoice_id': ['INV-001', 'INV-002'],
            'invoice_date': ['2023-01-01', '2023-01-02'],
            'due_date': ['2023-01-31', '2023-02-01'],
            'customer_name': ['Cliente A', 'Cliente B'],
            'amount': [1000.0, 2000.0],
            'vat': [210.0, 420.0],
            'total': [1210.0, 2420.0],
            'status': ['paid', 'pending'],
            'paid_date': ['2023-01-15', None],
            'payment_method': ['transfer', 'transfer']
        })
    
    def test_transform_invoices(self, transformer, sample_invoices):
        """Test transformación de facturas."""
        result = transformer.transform_invoices(sample_invoices)
        
        assert len(result) > 0
        assert 'invoice_date' in result.columns
        assert pd.api.types.is_datetime64_any_dtype(result['invoice_date'])
    
    def test_cash_flow_creation(self, transformer):
        """Test creación de cash flow diario."""
        # Usar datos reales si existen
        if Path('data/raw/bank_movements.csv').exists():
            bank_df = pd.read_csv('data/raw/bank_movements.csv')
            cash_flow = transformer.create_cash_flow_daily(bank_df)
            
            assert 'cash_balance' in cash_flow.columns
            assert 'cash_inflow' in cash_flow.columns
            assert 'cash_outflow' in cash_flow.columns


class TestValidator:
    """Tests para validador de coherencia."""
    
    def test_coherence_validation(self):
        """Test validación de coherencia."""
        from src.etl.validator import CoherenceValidator
        
        extractor = DataExtractor("data/raw")
        datasets = extractor.load_all()
        
        transformer = DataTransformer()
        transformed = transformer.transform_all(datasets)
        
        validator = CoherenceValidator()
        results = validator.validate_all_rules(transformed)
        
        assert '_summary' in results
        assert 'passed' in results['_summary']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])