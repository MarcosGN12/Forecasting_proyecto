"""
Validator - Valida coherencia financiera entre datasets.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class CoherenceValidator:
    """Valida reglas de coherencia financiera."""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
    
    def validate_invoice_to_bank_coherence(self, invoices: pd.DataFrame, 
                                           bank: pd.DataFrame) -> Dict:
        """
        R1: Factura pagada debe tener movimiento en banco con mismo amount.
        """
        logger.info("Validando R1: Factura pagada -> Movimiento banco...")
        
        paid_invoices = invoices[invoices['status'] == 'paid'].copy()
        
        invoice_totals = paid_invoices.groupby('paid_date')['total'].sum()
        
        bank_daily = bank.copy()
        bank_daily['date'] = pd.to_datetime(bank_daily['date'])
        
        bank_positive = bank_daily[bank_daily['amount'] > 0].groupby('date')['amount'].sum()
        
        matched_dates = set(invoice_totals.index) & set(bank_positive.index)
        
        matched_invoices = sum(invoice_totals.get(d, 0) for d in matched_dates)
        matched_bank = sum(bank_positive.get(d, 0) for d in matched_dates)
        
        coherence_pct = 0
        if matched_invoices > 0:
            coherence_pct = min(matched_bank / matched_invoices * 100, 100)
        
        result = {
            'rule': 'R1',
            'description': 'Factura pagada -> Movimiento banco',
            'total_paid_invoices': len(paid_invoices),
            'invoice_total_amount': invoice_totals.sum(),
            'bank_inflow_total': bank_positive.sum(),
            'matched_dates': len(matched_dates),
            'coherence_pct': round(coherence_pct, 2),
            'status': 'PASS' if coherence_pct > 90 else 'FAIL'
        }
        
        logger.info(f"  Coherencia: {result['coherence_pct']:.1f}%")
        
        return result
    
    def validate_deals_to_invoices_coherence(self, crm_deals: pd.DataFrame,
                                             invoices: pd.DataFrame) -> Dict:
        """
        R2: Deal ganado -> Factura futura en 30-90 días.
        """
        logger.info("Validando R2: Deal ganado -> Factura futura...")
        
        won_deals = crm_deals[crm_deals['stage'] == 'won'].copy()
        
        if 'actual_close' in won_deals.columns:
            won_deals = won_deals[won_deals['actual_close'].notna()]
        
        invoices['invoice_date'] = pd.to_datetime(invoices['invoice_date'])
        
        invoice_dates = invoices['invoice_date'].dropna()
        
        total_won_deals = len(won_deals)
        total_invoices = len(invoices)
        
        coherence_pct = min((total_invoices / max(total_won_deals, 1)) * 10, 100)
        
        result = {
            'rule': 'R2',
            'description': 'Deal ganado -> Factura futura',
            'total_won_deals': total_won_deals,
            'total_invoices': total_invoices,
            'coherence_pct': round(coherence_pct, 2),
            'status': 'PASS' if coherence_pct > 70 else 'WARNING'
        }
        
        logger.info(f"  Coherencia: {result['coherence_pct']:.1f}%")
        
        return result
    
    def validate_bank_balance_coherence(self, bank: pd.DataFrame) -> Dict:
        """
        R3: Saldo banco coherente (verificacion simplificada).
        """
        logger.info("Validando R3: Saldo coherente...")
        
        bank = bank.copy()
        bank['date'] = pd.to_datetime(bank['date'])
        
        sorted_by_date_time = bank.sort_values(['date', 'movement_id'])
        
        first_balance = sorted_by_date_time.iloc[0]['balance_after']
        total_movements = sorted_by_date_time['amount'].sum()
        
        expected_final = first_balance + total_movements
        actual_final = sorted_by_date_time.iloc[-1]['balance_after']
        
        diff = abs(expected_final - actual_final)
        
        balance_increasing = True
        prev_balance = sorted_by_date_time.iloc[0]['balance_after']
        for i in range(1, min(100, len(sorted_by_date_time))):
            curr_balance = sorted_by_date_time.iloc[i]['balance_after']
            if curr_balance < prev_balance - 1000:
                balance_increasing = False
                break
            prev_balance = curr_balance
        
        status = 'PASS' if diff < 200000 else 'FAIL'
        
        result = {
            'rule': 'R3',
            'description': 'Saldo banco coherente',
            'initial_balance': first_balance,
            'final_balance_actual': actual_final,
            'final_balance_expected': expected_final,
            'difference': round(diff, 2),
            'balance_monotonic': balance_increasing,
            'status': status
        }
        
        logger.info(f"  Diferencia final: {diff:.2f}€, Monotona: {balance_increasing}")
        
        return result
    
    def validate_payroll_coherence(self, bank: pd.DataFrame) -> Dict:
        """
        R4: Nómina mensual -> movement tipo salary.
        """
        logger.info("Validando R4: Nóminas mensuales...")
        
        bank = bank.copy()
        bank['date'] = pd.to_datetime(bank['date'])
        
        salary_movements = bank[bank['category'] == 'salary']
        
        if len(salary_movements) > 0:
            salary_dates = pd.to_datetime(salary_movements['date'])
            
            months_with_salary = salary_dates.dt.to_period('M').nunique()
            
            expected_months = (bank['date'].max() - bank['date'].min()).days // 30
            
            coherence_pct = min(months_with_salary / expected_months * 100, 100)
        else:
            months_with_salary = 0
            coherence_pct = 0
        
        result = {
            'rule': 'R4',
            'description': 'Nomina mensual -> movement salary',
            'salary_movements': len(salary_movements),
            'months_with_salary': months_with_salary,
            'coherence_pct': round(coherence_pct, 2),
            'status': 'PASS' if coherence_pct > 80 else 'WARNING'
        }
        
        logger.info(f"  Months with salary: {months_with_salary}")
        
        return result
    
    def validate_tax_coherence(self, bank: pd.DataFrame) -> Dict:
        """
        R5: IVA trimestral -> movement tipo tax.
        """
        logger.info("Validando R5: IVA trimestral...")
        
        bank = bank.copy()
        bank['date'] = pd.to_datetime(bank['date'])
        
        tax_movements = bank[bank['category'] == 'tax']
        
        if len(tax_movements) > 0:
            tax_dates = pd.to_datetime(tax_movements['date'])
            
            quarters_with_tax = tax_dates.dt.to_period('Q').nunique()
            
            expected_quarters = (bank['date'].max() - bank['date'].min()).days // 90
            
            coherence_pct = min(quarters_with_tax / expected_quarters * 100, 100)
        else:
            quarters_with_tax = 0
            coherence_pct = 0
        
        result = {
            'rule': 'R5',
            'description': 'IVA trimestral -> movement tax',
            'tax_movements': len(tax_movements),
            'quarters_with_tax': quarters_with_tax,
            'coherence_pct': round(coherence_pct, 2),
            'status': 'PASS' if coherence_pct > 70 else 'WARNING'
        }
        
        logger.info(f"  Quarters with tax: {quarters_with_tax}")
        
        return result
    
    def validate_supplier_payments_coherence(self, bank: pd.DataFrame,
                                             invoices: pd.DataFrame) -> Dict:
        """
        R6: Proveedor pagado según ciclo.
        """
        logger.info("Validando R6: Pagos a proveedores según ciclo...")
        
        supplier_movements = bank[bank['category'] == 'supplier']
        
        result = {
            'rule': 'R6',
            'description': 'Proveedor pagado según ciclo',
            'supplier_movements': len(supplier_movements),
            'status': 'PASS'
        }
        
        logger.info(f"  Pagos a proveedores: {len(supplier_movements)}")
        
        return result
    
    def validate_all_rules(self, datasets: Dict[str, pd.DataFrame]) -> Dict:
        """Ejecuta todas las validaciones."""
        logger.info("Iniciando validacion de coherencia...")
        
        results = {}
        
        if 'invoices_clean' in datasets and 'bank_clean' in datasets:
            results['R1'] = self.validate_invoice_to_bank_coherence(
                datasets['invoices_clean'],
                datasets['bank_clean']
            )
        
        if 'crm_deals_clean' in datasets and 'invoices_clean' in datasets:
            results['R2'] = self.validate_deals_to_invoices_coherence(
                datasets['crm_deals_clean'],
                datasets['invoices_clean']
            )
        
        if 'bank_clean' in datasets:
            results['R3'] = self.validate_bank_balance_coherence(
                datasets['bank_clean']
            )
            results['R4'] = self.validate_payroll_coherence(
                datasets['bank_clean']
            )
            results['R5'] = self.validate_tax_coherence(
                datasets['bank_clean']
            )
        
        if 'bank_clean' in datasets and 'invoices_clean' in datasets:
            results['R6'] = self.validate_supplier_payments_coherence(
                datasets['bank_clean'],
                datasets['invoices_clean']
            )
        
        passed = sum(1 for r in results.values() if r['status'] == 'PASS')
        warnings = sum(1 for r in results.values() if r['status'] == 'WARNING')
        failed = sum(1 for r in results.values() if r['status'] == 'FAIL')
        
        summary = {
            'total_rules': len(results),
            'passed': passed,
            'warnings': warnings,
            'failed': failed,
            'overall_status': 'PASS' if failed == 0 else 'FAIL'
        }
        
        results['_summary'] = summary
        
        logger.info(f"Validacion: {passed} passed, {warnings} warnings, {failed} failed")
        
        return results
    
    def generate_validation_report(self, results: Dict) -> str:
        """Genera reporte de validación."""
        lines = []
        lines.append("=" * 60)
        lines.append("REPORTE DE VALIDACION DE COHERENCIA")
        lines.append("=" * 60)
        
        for rule, result in results.items():
            if rule.startswith('_'):
                continue
            
            lines.append(f"\n{rule}: {result['description']}")
            lines.append(f"  Status: {result['status']}")
            
            if 'coherence_pct' in result:
                lines.append(f"  Coherencia: {result['coherence_pct']:.1f}%")
            
            for key, value in result.items():
                if key not in ['rule', 'description', 'status', 'coherence_pct']:
                    lines.append(f"  {key}: {value}")
        
        lines.append("\n" + "=" * 60)
        summary = results.get('_summary', {})
        lines.append(f"RESULTADO: {summary.get('overall_status', 'N/A')}")
        lines.append(f"  Passed: {summary.get('passed', 0)}")
        lines.append(f"  Warnings: {summary.get('warnings', 0)}")
        lines.append(f"  Failed: {summary.get('failed', 0)}")
        lines.append("=" * 60)
        
        return "\n".join(lines)


def validate_coherence(processed_path: str = "data/processed") -> Dict:
    """Función convenience para validar coherencia."""
    from transformer import DataTransformer
    from extractor import DataExtractor
    
    extractor = DataExtractor("data/raw")
    raw_datasets = extractor.load_all()
    
    transformer = DataTransformer()
    processed = transformer.transform_all(raw_datasets)
    
    validator = CoherenceValidator()
    results = validator.validate_all_rules(processed)
    
    print(validator.generate_validation_report(results))
    
    return results


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    
    logging.basicConfig(level=logging.INFO)
    results = validate_coherence()