"""
Extractor de datos - Carga datos raw y valida estructura.
"""

import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataExtractor:
    """Carga y valida datos desde fuentes raw."""
    
    SCHEMAS = {
        'invoices': {
            'required': ['invoice_id', 'invoice_date', 'customer_name', 
                        'amount', 'vat', 'total', 'status', 'payment_method'],
            'optional': ['paid_date', 'due_date', 'customer_id', 'category']
        },
        'bank_movements': {
            'required': ['movement_id', 'date', 'description', 'amount', 
                        'balance_after', 'category', 'bank_account'],
            'optional': ['value_date', 'reference']
        },
        'crm_deals': {
            'required': ['deal_id', 'deal_name', 'customer_name', 'stage',
                        'probability', 'expected_amount', 'created_date'],
            'optional': ['expected_close', 'actual_close', 'closed_date', 'customer_id']
        },
        'employees': {
            'required': ['employee_id', 'name', 'department', 'salary'],
            'optional': ['contract_type', 'ss_contribution', 'start_date']
        },
        'suppliers': {
            'required': ['supplier_id', 'name', 'category', 'payment_cycle'],
            'optional': ['typical_amount']
        },
        'external_factors': {
            'required': ['date', 'indicator', 'value', 'source'],
            'optional': []
        }
    }
    
    def __init__(self, raw_path: str = "data/raw"):
        self.raw_path = Path(raw_path)
        self.datasets = {}
        
    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Carga todos los datasets raw."""
        logger.info("Iniciando carga de datos raw...")
        
        for csv_file in self.raw_path.glob("*.csv"):
            dataset_name = csv_file.stem
            logger.info(f"Cargando {dataset_name}...")
            
            try:
                df = pd.read_csv(csv_file, encoding='utf-8')
                self.datasets[dataset_name] = df
                logger.info(f"  - {dataset_name}: {len(df):,} registros")
            except Exception as e:
                logger.error(f"Error cargando {csv_file.name}: {e}")
                raise
        
        logger.info(f"Carga completada: {len(self.datasets)} datasets")
        return self.datasets
    
    def load_dataset(self, name: str) -> Optional[pd.DataFrame]:
        """Carga un dataset específico."""
        filepath = self.raw_path / f"{name}.csv"
        
        if not filepath.exists():
            logger.warning(f"Dataset {name} no encontrado en {self.raw_path}")
            return None
        
        return pd.read_csv(filepath, encoding='utf-8')
    
    def validate_schema(self, dataset_name: str, df: pd.DataFrame) -> Dict:
        """Valida que el dataset tenga los campos requeridos."""
        if dataset_name not in self.SCHEMAS:
            logger.warning(f"Schema no definido para {dataset_name}")
            return {'valid': True, 'warnings': []}
        
        schema = self.SCHEMAS[dataset_name]
        missing_required = []
        
        for col in schema['required']:
            if col not in df.columns:
                missing_required.append(col)
        
        extra_columns = [c for c in df.columns 
                        if c not in schema['required'] and c not in schema['optional']]
        
        result = {
            'valid': len(missing_required) == 0,
            'missing_required': missing_required,
            'extra_columns': extra_columns,
            'total_columns': len(df.columns),
            'total_rows': len(df)
        }
        
        if result['valid']:
            logger.info(f"Schema válido: {dataset_name}")
        else:
            logger.error(f"Schema inválido: {dataset_name} - Faltan: {missing_required}")
        
        return result
    
    def validate_all_schemas(self) -> Dict:
        """Valida schemas de todos los datasets cargados."""
        results = {}
        
        for name, df in self.datasets.items():
            results[name] = self.validate_schema(name, df)
        
        all_valid = all(r['valid'] for r in results.values())
        
        logger.info(f"Validación schemas: {'OK' if all_valid else 'ERRORES'}")
        return results
    
    def get_quality_report(self) -> Dict:
        """Genera reporte de calidad de datos."""
        report = {}
        
        for name, df in self.datasets.items():
            null_counts = df.isnull().sum()
            null_pct = (null_counts / len(df) * 100).round(2)
            
            numeric_cols = df.select_dtypes(include=['number']).columns
            outlier_cols = {}
            
            for col in numeric_cols:
                if col in df.columns and len(df[col]) > 0:
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    outliers = ((df[col] < q1 - 1.5*iqr) | 
                               (df[col] > q3 + 1.5*iqr)).sum()
                    if outliers > 0:
                        outlier_cols[col] = outliers
            
            report[name] = {
                'rows': len(df),
                'columns': len(df.columns),
                'null_columns': null_counts[null_counts > 0].to_dict(),
                'null_pct': null_pct[null_pct > 0].to_dict(),
                'outliers': outlier_cols
            }
        
        return report


def extract_all(raw_path: str = "data/raw") -> Dict[str, pd.DataFrame]:
    """Función convenience para extraer todos los datos."""
    extractor = DataExtractor(raw_path)
    return extractor.load_all()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    extractor = DataExtractor()
    datasets = extractor.load_all()
    results = extractor.validate_all_schemas()
    report = extractor.get_quality_report()
    
    print("\n=== REPORTE DE CALIDAD ===")
    for name, data in report.items():
        print(f"\n{name}:")
        print(f"  Rows: {data['rows']:,}")
        print(f"  Columns: {data['columns']}")
        if data['null_pct']:
            print(f"  Null columns: {data['null_pct']}")