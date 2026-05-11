"""
Generador principal de datos sintéticos para Industrial Metálica Portillo.
Orquestador de todos los generators especializados.
"""

import pandas as pd
import numpy as np
import yaml
from datetime import datetime, timedelta
import uuid
import os
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from generators import invoice_generator, bank_generator, crm_generator, company_generator


class DataGenerator:
    """Orquestador principal de generación de datos sintéticos."""
    
    def __init__(self, config_path: str = "config/generation_params.yaml"):
        """Inicializa el generador con configuración."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.seed = self.config['generation']['seed']
        np.random.seed(self.seed)
        
        self.start_date = datetime.strptime(
            self.config['generation']['start_date'], "%Y-%m-%d"
        )
        self.end_date = datetime.strptime(
            self.config['generation']['end_date'], "%Y-%m-%d"
        )
        
        self.output_path = Path(self.config['output']['path'])
        self.output_path.mkdir(parents=True, exist_ok=True)
        
    def generate_all(self) -> dict:
        """Genera todos los datasets."""
        print("Iniciando generacion de datos sinteticos...")
        
        print("  - Generando estructura de empresa...")
        company_data = company_generator.generate_company()
        
        print("  - Generando facturas (ERP)...")
        invoices = invoice_generator.generate_invoices(
            company_data,
            self.start_date,
            self.end_date,
            self.config
        )
        
        print("  - Generando movimientos bancarios...")
        bank_movements = bank_generator.generate_bank_movements(
            invoices,
            company_data,
            self.start_date,
            self.end_date,
            self.config
        )
        
        print("  - Generando deals (CRM)...")
        crm_deals = crm_generator.generate_crm_deals(
            company_data,
            self.start_date,
            self.end_date,
            self.config
        )
        
        print("  - Generando empleados...")
        employees = company_generator.generate_employees(
            company_data,
            self.config
        )
        
        print("  - Generando proveedores...")
        suppliers = company_generator.generate_suppliers(
            company_data
        )
        
        print("  - Generando factores externos...")
        external_factors = company_generator.generate_external_factors(
            self.start_date,
            self.end_date
        )
        
        results = {
            'invoices': invoices,
            'bank_movements': bank_movements,
            'crm_deals': crm_deals,
            'employees': employees,
            'suppliers': suppliers,
            'external_factors': external_factors
        }
        
        self._save_all(results)
        
        print("\nGeneracion completada!")
        print(f"   Facturas: {len(invoices):,}")
        print(f"   Movimientos banco: {len(bank_movements):,}")
        print(f"   Deals CRM: {len(crm_deals):,}")
        print(f"   Empleados: {len(employees):,}")
        print(f"   Proveedores: {len(suppliers):,}")
        
        return results
    
    def _save_all(self, data: dict):
        """Guarda todos los datasets a CSV."""
        for name, df in data.items():
            filename = f"{name}.csv"
            filepath = self.output_path / filename
            df.to_csv(filepath, index=False, encoding='utf-8')
            print(f"  - Guardado: {filename}")


def main():
    """Punto de entrada principal."""
    generator = DataGenerator()
    generator.generate_all()


if __name__ == "__main__":
    main()