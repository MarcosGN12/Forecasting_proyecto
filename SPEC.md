# Cash Flow Forecasting System - Technical Specification

## 0. EMPRESA SIMULADA

### Datos Generales
- **Nombre**: Industrial Metálica Portillo S.L.
- **CIF**: B-45678901
- **Domicilio**: Polígono Industrial La Vega, Calle Metalurgia 23, Portillo de Toledo
- **Sector**: Fabricación de componentes metálicos para automoción
- **Tamaño**: Empresa mediana (50-100 empleados, facturación ~8M€/año)
- **Forma jurídica**: Sociedad Limitada

### Actividad Económica
- Fabricación de piezas de precisión para sector automotriz
- Mecanizado CNC
- Soldadura y ensamblaje de subconjuntos
- Tratamiento superficial (pintura, anodizado)

### Comportamiento Financiero Esperado
- Ingresos recurrentes con estacionalidad (típicamente mayor Q1 y Q4 por contratos anuales)
- Ciclos de cobro: 30-60 días (clientes grandes), 15-30 días (clientes pequeños)
- Ciclos de pago: 60-90 días (proveedores principales), 30 días (proveedores locales)
- Gastos fijos elevados (nómina, alquiler, energía)
- Gastos variables (materias primas, mantenimiento)
- Capacidad de inversión en equipamiento cada 2-3 años

### Clientes Simulados (5 principales)
| Cliente | Sector | Facturación anual | Condiciones pago | Ciclo típico |
|---------|--------|-------------------|------------------|---------------|
| AutoPartes Castilla | Automoción | 2.1M€ | 60 días | Confirming |
| MotorTech Solutions | Automoción | 1.8M€ | 45 días | Transferencia |
| Industrial Vical | Maquinaria | 1.2M€ | 30 días | Recibo |
| Componentes Henares | Automoción | 900K€ | 60 días | Confirming |
| Talleres Línea Sur | Automoción | 600K€ | 30 días | Efectivo |

### Proveedores Simulados (5 principales)
| Proveedor | Tipo | Gasto anual | Condiciones | Ciclo pago |
|-----------|------|--------------|-------------|------------|
| MetalSteel S.A. | Materia prima | 1.5M€ | 90 días | Confirming |
| Recambios Express | Repuestos | 400K€ | 30 días | Transferencia |
| Energía Castilla | Energía | 350K€ | 15 días | Domiciliación |
| Embalajes Toledo | Envases | 200K€ | 60 días | Recibo |
| Servicios Logs | Limpieza/Mant. | 180K€ | 30 días | Transferencia |

### Estacionalidad Básica
- **Alta temporada**: Septiembre-Diciembre (cierre de contratos anuales, producción para siguiente año)
- **Baja temporada**: Julio-Agosto (paros técnicos, mantenimiento)
- **Pico Q1**: Enero-Febrero (facturación de contratos nuevos)
- **Variación típica**: ±15% de ingresos trimestrales

---

## 1. ARQUITECTURA GENERAL DEL SISTEMA

### Componentes del Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CASH FLOW FORECASTING SYSTEM                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   GENERADOR │───▶│     ETL      │───▶│   FORECAST   │              │
│  │   DATOS      │    │   PIPELINE   │    │    MODEL     │              │
│  │   SINTÉTICOS │    │   (Python)   │    │   (Prophet)  │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         │                   │                   │                      │
│         ▼                   ▼                   ▼                      │
│  ┌─────────────────────────────────────────────────────────────┐        │
│  │                    BASE DE DATOS (SQLite)                   │        │
│  │         raw + processed + models + metadata                 │        │
│  └─────────────────────────────────────────────────────────────┘        │
│                              │                    │                     │
│                              ▼                    ▼                     │
│                    ┌──────────────────┐  ┌──────────────────┐          │
│                    │    POWER BI      │  │   TELEGRAM BOT   │          │
│                    │   DASHBOARD      │  │   ALERTAS        │          │
│                    └──────────────────┘  └──────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos Extremo a Extremo

```
raw/                          processed/                    models/
┌─────────────┐              ┌─────────────┐              ┌─────────────┐
│ invoices.csv│── ETL ──────▶│ invoices_cl │              │ prophet_... │
│ bank_...csv │─────────────▶│ bank_clean  │              │ metrics.json│
│ crm_deals   │              │ cash_flow   │              └─────────────┘
│ external    │              │ forecast    │
└─────────────┘              └─────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
    ┌─────────┐              ┌─────────────┐           ┌─────────────┐
    │POWER BI │◀─────────────│  alerts.py  │◀──────────│ forecast.py │
    └─────────┘              └─────────────┘           └─────────────┘
```

### Dependencias entre Módulos

| Módulo | Dependencias | Input | Output |
|--------|--------------|-------|--------|
| Generador | Faker, Pandas | config/empresa.yaml | data/raw/*.csv |
| ETL | Pandas, SQL | data/raw/*.csv | data/processed/*.csv |
| Forecasting | Prophet, Pandas | data/processed/cash_flow.csv | models/*.json, forecast.csv |
| Alerts | Telegram API | models/forecast.json | Notificaciones |
| Dashboard | Power BI Connector | data/processed/*.pbix | Visualizaciones |

---

## 2. ESTRATEGIA DE DATOS SINTÉTICOS

### Datasets Obligatorios

#### 2.1 invoices.csv (ERP Simulado)
```
invoice_id        : UUID único
invoice_date      : Fecha emisión (2023-01-01 a 2025-12-31)
due_date          : Fecha vencimiento (invoice_date + ciclo_pago)
customer_id       : FK a customer
customer_name     : Nombre cliente
amount            : Float (1000 - 150000)
vat               : Float (21% del amount)
total             : Float (amount + vat)
status            : ENUM: 'paid', 'pending', 'overdue', 'cancelled'
paid_date         : Fecha pago (nullable)
payment_method    : ENUM: 'transfer', 'confirming', 'cash', 'receipt'
category          : ENUM: 'product', 'service'
```

#### 2.2 bank_movements.csv (Banco Simulado)
```
movement_id       : UUID único
date              : Fecha operación
value_date        : Fecha valoración
description       : Texto descriptivo
amount            : Float (negativo=gasto, positivo=ingreso)
balance_after     : Float (saldo post-operación)
category          : ENUM: 'invoice_payment', 'salary', 'supplier', 
                              'utility', 'tax', 'loan', 'investment',
                              'other'
reference         : FK a invoice_id (si aplica)
bank_account      : IBAN simulada
```

#### 2.3 crm_deals.csv (CRM Simulado)
```
deal_id           : UUID único
deal_name         : Nombre oportunidad
customer_id       : FK cliente
customer_name     : Nombre
stage            : ENUM: 'prospecting', 'qualification', 'proposal',
                          'negotiation', 'won', 'lost'
probability       : Float (0.0 - 1.0)
expected_amount   : Float (valor esperado)
expected_close    : Fecha cierre estimada
actual_close      : Fecha cierre real (nullable)
created_date      : Fecha creación
closed_date       : Fecha cierre (nullable)
```

#### 2.4 external_factors.csv (Factores Externos)
```
date              : Fecha
indicator         : ENUM: 'interest_rate', 'inflation', 
                          'sector_growth', 'fuel_price'
value             : Float
source            : ENUM: 'bank_spain', 'ine', 'market'
```

#### 2.5 employees.csv (RRHH Simulado)
```
employee_id       : UUID único
name              : Nombre empleado
department        : ENUM: 'production', 'admin', 'sales', 'logistics'
contract_type     : ENUM: 'permanent', 'temporary'
salary            : Float (mensual bruto)
ss_contribution  : Float
start_date        : Fecha alta
```

#### 2.6 suppliers.csv (Proveedores Simulados)
```
supplier_id       : UUID único
name              : Nombre proveedor
category          : ENUM: 'raw_material', 'services', 'utilities'
payment_cycle    : Integer (días)
typical_amount    : Float (media factura)
```

### Relaciones entre Datasets

```
CRM Deals ──(converted to)──▶ Invoices ──(paid by)──▶ Bank Movements
     │                                                   │
     │                                                   │
     ▼                                                   ▼
External Factors ◀──────────────────────────────────┘
     │
     ▼
  Employees ──(paid by)──▶ Bank Movements
     │
     ▼
 Suppliers ──(paid by)──▶ Bank Movements
```

### Reglas de Coherencia Financiera

| Regla | Descripción | Validación |
|-------|-------------|------------|
| R1 | Factura pagada → movement en banco con mismo amount | invoice.paid_date == bank.date && invoice.total == bank.amount |
| R2 | Deal ganado → factura futura en 30-60 días | crm_deals.won → invoices未来的 |
| R3 | Saldo banco = Σ movements acumulativo | balance_after(n) = balance_after(n-1) + amount(n) |
| R4 | Nómina mensual → movement tipo salary | 1er día laborable cada mes |
| R5 | IVA trimestral → movement tipo tax | Trimestre natural |
| R6 | Proveedor pagado según ciclo | bank.date <= invoice.due_date |

---

## 3. DISEÑO TÉCNICO DE GENERACIÓN SINTÉTICA

### Herramientas Recomendadas

```python
# requirements.txt
pandas>=2.0.0
numpy>=1.24.0
faker>=18.0.0
python-dateutil>=2.8.0
random
hashlib (built-in)
```

### Volumen de Datos Recomendado

| Dataset | Registros | Rango Temporal | Justificación |
|---------|-----------|----------------|---------------|
| invoices | ~3,000 | 3 años (2023-2025) | ~100 facturas/mes |
| bank_movements | ~5,000 | 3 años | ~140 movimientos/mes |
| crm_deals | ~400 | 3 años | ~11 deals/mes |
| employees | ~75 | Actuales | Plantilla estable |
| suppliers | ~30 | Actuales | Proveedores fijos |

### Parámetros de Generación

```python
# config/generation_params.yaml
generation:
  start_date: "2023-01-01"
  end_date: "2025-12-31"
  seed: 42  # Reprodicible

company:
  name: "Industrial Metálica Portillo S.L."
  initial_balance: 450000.0
  avg_monthly_income: 650000.0
  avg_monthly_expense: 580000.0

customers:
  count: 25
  top_5_revenue_pct: 0.75

suppliers:
  count: 30
  top_5_expense_pct: 0.60
```

### Comportamiento Financiero Simulado

```python
# Lógica de generación de ingresos
monthly_income = base_income * seasonal_factor * random_variation

# Estacionalidad (2023=1.0)
seasonal_factor = {
    1: 0.95, 2: 0.98, 3: 1.10, 4: 1.05,
    5: 1.02, 6: 0.90, 7: 0.70, 8: 0.65,
    9: 1.00, 10: 1.15, 11: 1.20, 12: 1.10
}

# Variación aleatoria
random_variation = random.normal(1.0, 0.08)  # ±8% desviación estándar
```

---

## 4. ESTRUCTURA DE CARPETAS

```
Forecasting_proyecto/
├── SPEC.md                          # Este documento
├── README.md                        # Visión general
├── requirements.txt                 # Dependencias Python
├── .gitignore                       # Ignorar datos, logs, cache
│
├── data/                            # Datos del proyecto
│   ├── raw/                         # Datos sintéticos generados (input)
│   │   ├── invoices.csv
│   │   ├── bank_movements.csv
│   │   ├── crm_deals.csv
│   │   ├── employees.csv
│   │   ├── suppliers.csv
│   │   └── external_factors.csv
│   │
│   ├── processed/                   # Datos transformados (ETL output)
│   │   ├── invoices_clean.csv
│   │   ├── bank_clean.csv
│   │   ├── cash_flow_daily.csv
│   │   ├── forecast_results.csv
│   │   └── kpi_summary.json
│   │
│   ├── synthetic/                  # Datos de testing/validación
│   │   └── test_set_2025.csv
│   │
│   └── external/                   # Datos de fuentes externas
│       └── market_indices.csv
│
├── models/                          # Modelos entrenados y métricas
│   ├── prophet_cashflow_model.json # Modelo Prophet serializado
│   ├── model_metrics.json          # MAE, RMSE, MAPE
│   └── feature_importance.csv
│
├── src/                            # Código fuente
│   ├── etl/                        # Pipeline de transformación
│   │   ├── __init__.py
│   │   ├── extractor.py            # Carga datos raw
│   │   ├── transformer.py          # Limpieza y transformación
│   │   ├── loader.py               # Guarda datos processed
│   │   └── validator.py           # Reglas coherencia
│   │
│   ├── forecasting/                # Modelado predictivo
│   │   ├── __init__.py
│   │   ├── data_prep.py           # Prepara serie temporal
│   │   ├── trainer.py             # Entrena Prophet
│   │   ├── predictor.py           # Genera forecasts
│   │   └── evaluator.py           # Calcula métricas
│   │
│   ├── alerts/                    # Sistema de alertas
│   │   ├── __init__.py
│   │   ├── checker.py            # Evalúa condiciones
│   │   └── notifier.py           # Envía notificaciones
│   │
│   ├── bots/                      # Integración Telegram
│   │   ├── __init__.py
│   │   └── telegram_bot.py        # Bot de alertas
│   │
│   ├── utils/                     # Utilidades compartidas
│   │   ├── __init__.py
│   │   ├── logger.py             # Logging estructurado
│   │   ├── config.py             # Carga configuración
│   │   └── date_utils.py        # Funciones de fecha
│   │
│   └── generators/                # Generadores de datos
│       ├── __init__.py
│       ├── company_generator.py # Simula empresa
│       ├── invoice_generator.py # Genera facturas
│       ├── bank_generator.py    # Genera movimientos
│       ├── crm_generator.py     # Genera deals
│       └── main_generator.py    # Orquestador
│
├── config/                         # Configuración
│   ├── empresa.yaml              # Datos empresa simulada
│   ├── generation_params.yaml    # Parámetros generación
│   ├── database.yaml             # Config SQLite
│   ├── forecasting.yaml          # Params Prophet
│   ├── alerts.yaml               # Thresholds alertas
│   └── telegram.yaml             # Credenciales bot
│
├── notebooks/                      # Jupyter notebooks
│   ├── 01_exploratory.ipynb      # Análisis datos
│   ├── 02_etl_process.ipynb      # Desarrollo ETL
│   ├── 03_forecasting.ipynb      # Modelo Prophet
│   ├── 04_dashboard_powerbi.ipynb # Conexión BI
│   └── 05_evaluation.ipynb       # Métricas finales
│
├── tests/                          # Suite de tests
│   ├── test_etl.py
│   ├── test_forecasting.py
│   ├── test_generators.py
│   ├── test_coherence.py
│   └── test_alerts.py
│
└── logs/                           # Archivos de logging
    ├── etl.log
    ├── forecasting.log
    └── alerts.log
```

### Descripción de Carpetas

| Carpeta | Propósito |
|---------|-----------|
| `data/raw` | Datos sintéticos generados (fuente de verdad) |
| `data/processed` | Datos transformados tras ETL, listos para modelado |
| `data/synthetic` | Conjuntos de test adicionales |
| `data/external` | Índices externos (ej. tipos de interés) |
| `models` | Modelos entrenados serializados + métricas |
| `src/etl` | Pipeline extracción, transformación, carga |
| `src/forecasting` | Lógica de entrenamiento y predicción Prophet |
| `src/alerts` | Evaluación de condiciones de alerta |
| `src/bots` | Bot de Telegram y mensajería |
| `src/utils` | Logging, config, helpers |
| `src/generators` | Generadores de datos sintéticos |
| `config` | Archivos YAML de configuración |
| `notebooks` | Análisis exploratorio y desarrollo |
| `tests` | Tests unitarios y de integración |
| `logs` | Archivos de ejecución |

---

## 5. ROADMAP POR FASES

### Fase 0: Simulación de Empresa y Generación de Datos Sintéticos

**Objetivo**: Crear empresa simulada con datos coherentes y realistas

**Tareas**:
- [ ] Definir estructura empresa (CIF, sector, empleados, proveedores)
- [ ] Crear generator de clientes y proveedores
- [ ] Implementar generator invoices (ERP simulado)
- [ ] Implementar generator bank_movements (banco simulado)
- [ ] Implementar generator crm_deals (CRM simulado)
- [ ] Implementar generator employees y suppliers
- [ ] Validar coherencia financiera entre datasets
- [ ] Generar dataset completo 2023-2025
- [ ] Documentar seed y parámetros de reproducibilidad

**Entregables**:
- `data/raw/*.csv` (5 archivos)
- `config/empresa.yaml`
- `config/generation_params.yaml`

**Dependencias**: Ninguna (punto de partida)

---

### Fase 1: Ingesta y Estructura de Datos

**Objetivo**: Cargar datos raw y validar estructura mínima

**Tareas**:
- [ ] Crear extractor.py para cargar CSVs
- [ ] Validar schema de cada dataset
- [ ] Verificar rangos temporales
- [ ] Detectar valores nulos y outliers
- [ ] Crear database SQLite con tablas derivadas
- [ ] Implementar logger de proceso

**Entregables**:
- `src/etl/extractor.py`
- Base de datos SQLite inicial
- Reporte de calidad de datos

**Dependencias**: Fase 0 completada

---

### Fase 2: ETL y Limpieza en Python

**Objetivo**: Transformar datos raw en datos procesados

**Tareas**:
- [ ] Implementar transformer.py (limpieza)
- [ ] Estandarizar fechas y formatos
- [ ] Normalizar categorías
- [ ] Eliminar duplicados
- [ ] Manejar valores nulos según estrategia
- [ ] Crear cash_flow_daily.csv (series temporales)
- [ ] Implementar validator.py (reglas coherencia)
- [ ] Validar R1-R6 (coherencia financiera)
- [ ] Generar reporte de validación

**Entregables**:
- `data/processed/cash_flow_daily.csv`
- `src/etl/transformer.py`
- `src/etl/validator.py`
- Reporte de validación de coherencia

**Dependencias**: Fase 1 completada

---

### Fase 3: Modelado de Forecasting con Prophet

**Objetivo**: Entrenar modelo predictivo de tesorería a 90 días

**Tareas**:
- [ ] Preparar serie temporal (data_prep.py)
- [ ] Configurar modelo Prophet
- [ ] Dividir train/test (80/20)
- [ ] Entrenar modelo base
- [ ] Añadir regresores (estacionalidad, factores externos)
- [ ] Optimizar hiperparámetros
- [ ] Generar predicción 90 días
- [ ] Serializar modelo guardado
- [ ] Calcular métricas (MAE, RMSE, MAPE)

**Entregables**:
- `models/prophet_cashflow_model.json`
- `models/model_metrics.json`
- `data/processed/forecast_results.csv`
- Notebook de desarrollo

**Dependencias**: Fase 2 completada

---

### Fase 4: Dashboard Financiero en Power BI

**Objetivo**: Crear visualizaciones ejecutivas

**Tareas**:
- [ ] Exportar datos processed a formato accesible
- [ ] Conectar Power BI a SQLite o CSV
- [ ] Diseñar dashboard principal
- [ ] Implementar KPIs obligatorios
- [ ] Crear gráfico de tendencia cash balance
- [ ] Añadir comparación forecast vs real
- [ ] Implementar alertas visuales
- [ ] Configurar actualización automática
- [ ] Documentar manual de usuario

**Entregables**:
- `CashFlow_Dashboard.pbix`
- Manual de usuario
- Video tutorial

**Dependencias**: Fase 3 completada

---

### Fase 5: Bot de Telegram y Sistema de Alertas

**Objetivo**: Notificaciones automáticas de riesgos

**Tareas**:
- [ ] Configurar bot Telegram (BotFather)
- [ ] Implementar telegram_bot.py
- [ ] Diseñar lógica de alertas (checker.py)
- [ ] Implementar condiciones de alerta:
  - Cash balance < umbral
  - Caída > X% en 7 días
  - Desviación forecast > 10%
- [ ] Integrar con modelo de forecasting
- [ ] Testing de notificaciones
- [ ] Documentar uso del bot

**Entregables**:
- Bot de Telegram operativo
- `src/bots/telegram_bot.py`
- `src/alerts/checker.py`
- Documentación de comandos

**Dependencias**: Fase 3 y 4 completadas

---

### Fase 6: Validación del Modelo y Métricas de Error

**Objetivo**: Verificar precisión del forecasting

**Tareas**:
- [ ] Ejecutar backtesting del modelo
- [ ] Calcular MAE, RMSE, MAPE finales
- [ ] Analizar errores por período
- [ ] Identificar patrones de desviación
- [ ] Comparar con benchmark (naive forecast)
- [ ] Generar reporte de validación
- [ ] Ajustar modelo si MAPE > 5%
- [ ] Documentar limitaciones y recomendaciones

**Entregables**:
- Reporte de validación final
- Modelo optimizado (si aplica)
- Recomendaciones de mejora

**Dependencias**: Fases 1-5 completadas

---

## 6. DEFINICIÓN DE TAREAS (BACKLOG)

### Tareas Técnicas - Fase 0

| ID | Tarea | Tipo | Prioridad | Estimación |
|----|-------|------|-----------|------------|
| T01 | Crear estructura empresa simulada | Config | Alta | 1h |
| T02 | Implementar generator clientes/proveedores | Generator | Alta | 2h |
| T03 | Implementar invoice_generator.py | Generator | Alta | 3h |
| T04 | Implementar bank_generator.py | Generator | Alta | 3h |
| T05 | Implementar crm_generator.py | Generator | Media | 2h |
| T06 | Implementar employees_generator.py | Generator | Media | 1h |
| T07 | Crear main_generator.py orquestador | Generator | Alta | 1h |
| T08 | Validar coherencia datasets | Testing | Alta | 2h |
| T09 | Generar dataset completo 2023-2025 | Generator | Alta | 1h |

### Tareas Técnicas - Fase 1

| ID | Tarea | Tipo | Prioridad | Estimación |
|----|-------|------|-----------|------------|
| T10 | Crear extractor.py base | ETL | Alta | 2h |
| T11 | Implementar validación schema | ETL | Alta | 1h |
| T12 | Crear SQLite database | ETL | Media | 1h |
| T13 | Implementar logger.py | Utils | Media | 1h |
| T14 | Generar reporte calidad datos | ETL | Media | 1h |

### Tareas Técnicas - Fase 2

| ID | Tarea | Tipo | Prioridad | Estimación |
|----|-------|------|-----------|------------|
| T15 | Implementar transformer.py principal | ETL | Alta | 4h |
| T16 | Crear cash_flow_daily aggregation | ETL | Alta | 2h |
| T17 | Implementar validator.py reglas R1-R6 | ETL | Alta | 3h |
| T18 | Crear tests coherencia financiera | Testing | Alta | 2h |
| T19 | Generar reporte validación | ETL | Media | 1h |

### Tareas Técnicas - Fase 3

| ID | Tarea | Tipo | Prioridad | Estimación |
|----|-------|------|-----------|------------|
| T20 | Implementar data_prep.py | Forecasting | Alta | 2h |
| T21 | Configurar modelo Prophet base | Forecasting | Alta | 2h |
| T22 | Implementar trainer.py | Forecasting | Alta | 3h |
| T23 | Implementar predictor.py | Forecasting | Alta | 2h |
| T24 | Implementar evaluator.py métricas | Forecasting | Alta | 2h |
| T25 | Optimizar hiperparámetros | Forecasting | Media | 3h |
| T26 | Serializar y guardar modelo | Forecasting | Alta | 1h |

### Tareas Técnicas - Fase 4

| ID | Tarea | Tipo | Prioridad | Estimación |
|----|-------|------|-----------|------------|
| T27 | Preparar datos para Power BI | Dashboard | Alta | 1h |
| T28 | Diseñar dashboard KPIs | Dashboard | Alta | 4h |
| T29 | Crear visualizaciones tendencia | Dashboard | Alta | 2h |
| T30 | Implementar comparación forecast | Dashboard | Alta | 2h |
| T31 | Configurar refresh automático | Dashboard | Media | 1h |

### Tareas Técnicas - Fase 5

| ID | Tarea | Tipo | Prioridad | Estimación |
|----|-------|------|-----------|------------|
| T32 | Configurar bot Telegram | Bot | Alta | 1h |
| T33 | Implementar telegram_bot.py | Bot | Alta | 2h |
| T34 | Implementar checker.py alertas | Alerts | Alta | 3h |
| T35 | Implementar notifier.py | Alerts | Alta | 2h |
| T36 | Testing integración completa | Testing | Alta | 2h |

### Tareas Técnicas - Fase 6

| ID | Tarea | Tipo | Prioridad | Estimación |
|----|-------|------|-----------|------------|
| T37 | Ejecutar backtesting completo | Evaluation | Alta | 2h |
| T38 | Calcular métricas finales | Evaluation | Alta | 1h |
| T39 | Analizar errores y patrones | Evaluation | Media | 3h |
| T40 | Generar reporte final | Evaluation | Alta | 2h |
| T41 | Documentar limitaciones | Documentation | Media | 1h |

---

## 7. FLUJO DE DATOS DETALLADO

### Pipeline Completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FLUJO DE DATOS                                 │
└─────────────────────────────────────────────────────────────────────────┘

Generación Sintética (Batch - 1 vez)
│
├─ main_generator.py ejecuta:
│   ├─ company_generator.py
│   ├─ invoice_generator.py
│   ├─ bank_generator.py
│   └─ crm_generator.py
│
└─▶ data/raw/
    ├── invoices.csv         (~3000 registros)
    ├── bank_movements.csv  (~5000 registros)
    ├── crm_deals.csv       (~400 registros)
    ├── employees.csv       (~75 registros)
    └── suppliers.csv       (~30 registros)


ETL Pipeline (Batch - diario/semanal)
│
├─ extractor.py carga data/raw/*.csv
├─ transformer.py limpia y estandariza
│   ├─ Estandarización fechas
│   ├─ Normalización categorías
│   ├─ Unión con dimensiones (customers, suppliers)
│   └─ Agregación a nivel diario
│
├─ validator.py valida coherencia R1-R6
│
└─▶ data/processed/
    ├── invoices_clean.csv
    ├── bank_clean.csv
    ├── cash_flow_daily.csv    ← SERIE TEMPORAL PRINCIPAL
    └── kpi_summary.json


Forecasting (Batch - semanal)
│
├─ data_prep.py prepara cash_flow_daily.csv
│   └─ Estructura: ds (fecha), y (balance), regressors
│
├─ trainer.py entrena modelo Prophet
│   ├─ Train: 2023-01-01 a 2024-06-30
│   ├─ Test: 2024-07-01 a 2025-12-31
│   └─ Holdout para validación
│
├─ predictor.py genera predicción 90 días
│
└─▶ models/
    ├── prophet_cashflow_model.json
    └── forecast_results.csv


Power BI (Near real-time - refresh diario)
│
├─ Conexión a SQLite o CSV directo
├─ Dashboard principal:
│   ├─ KPI: Cash Balance actual
│   ├─ KPI: Cash Inflow (30d)
│   ├─ KPI: Cash Outflow (30d)
│   ├─ KPI: Forecast 90 días
│   ├─ Gráfico: Evolución saldo (12 meses)
│   └─ Gráfico: Comparación forecast vs real
│
└─▶ Visualizaciones actualizadas


Alertas (Near real-time - ejecución programada)
│
├─ checker.py evalúa condiciones:
│   ├─ cash_balance < 50000
│   ├─ variación_7días < -15%
│   └─ desviación_forecast > 10%
│
├─ notifier.py formatea mensaje
├─ telegram_bot.py envía notificación
│
└─▶ Notificación Telegram al administrator
```

### Procesos Batch vs Near Real-time

| Proceso | Frecuencia | Tipo |
|---------|------------|------|
| Generación datos sintéticos | Una vez (inicial) | Batch |
| ETL pipeline | Diario/Semanal | Batch |
| Entrenamiento modelo | Semanal/Mensual | Batch |
| Predicción forecasting | Semanal | Batch |
| Refresh Power BI | Diario | Near real-time |
| Chequeo alertas | Cada 6 horas | Scheduled |
| Notificaciones Telegram | On-demand | Near real-time |

### Datasets Fuente Principal de Verdad

| Dataset | Rol | Frecuencia Actualización |
|---------|-----|---------------------------|
| `cash_flow_daily.csv` | Serie temporal principal | Diario |
| `invoices.csv` | Base de facturación | Semanal |
| `bank_movements.csv` | Movimientos bancarios | Diario |
| `prophet_cashflow_model.json` | Modelo entrenado | Semanal |

---

## 8. KPIs FINANCIEROS OBLIGATORIOS

### KPI 1: Cash Balance (Saldo de Caja)

```python
# Cálculo: Saldo actual de cuenta corriente
# Origen: bank_movements.csv (último balance_after)
# Fórmula: balance_after del movimiento más reciente

current_cash = bank_movements.sort_values('date').iloc[-1]['balance_after']
```

**Visualización Power BI**: Tarjeta con valor actual + indicador color (verde/rojo)

---

### KPI 2: Cash Inflow (Ingresos período)

```python
# Cálculo: Suma de ingresos en período seleccionado
# Origen: bank_movements.csv (amount > 0)
# Fórmula: Σ(amount) WHERE amount > 0 AND date ∈ [period]

cash_inflow_30d = bank_movements[
    (bank_movements['date'] >= (today - 30 days)) & 
    (bank_movements['amount'] > 0)
]['amount'].sum()
```

**Visualización Power BI**: Gráfico de barras mensual + tendencia

---

### KPI 3: Cash Outflow (Gastos período)

```python
# Cálculo: Suma de gastos en período seleccionado
# Origen: bank_movements.csv (amount < 0)
# Fórmula: Σ(|amount|) WHERE amount < 0 AND date ∈ [period]

cash_outflow_30d = abs(bank_movements[
    (bank_movements['date'] >= (today - 30 days)) & 
    (bank_movements['amount'] < 0)
]['amount'].sum())
```

**Visualización Power BI**: Gráfico de barras mensual + tendencia

---

### KPI 4: Forecast Cash (Predicción 90 días)

```python
# Cálculo: Predicción de saldo a 90 días vista
# Origen: models/forecast_results.csv (fila 90)
# Fórmula: forecast.iloc[89]['yhat']

forecast_90d = forecast_df.iloc[89]['yhat']
```

**Visualización Power BI**: Gráfico línea con intervalos de confianza

---

### KPI 5: Desviación Forecast vs Real

```python
# Cálculo: Diferencia porcentual entre predicción y real
# Origen: cash_flow_daily.csv + forecast_results.csv
# Fórmula: ((real - forecast) / forecast) * 100

# Para período de validación (ej. últimos 30 días)
deviation = ((actual - forecasted) / abs(forecasted)) * 100
```

**Visualización Power BI**: Indicador de desviación % con threshold (ej. ±5%)

---

### KPI 6: Riesgo de Liquidez

```python
# Cálculo: Indicador binario/categoría según saldo proyectado
# Origen: forecast_results.csv + config/alerts.yaml
# Fórmula:

liquidity_risk = "ALTO" if forecast_90d < threshold else \
                 "MEDIO" if forecast_90d < threshold * 1.5 else \
                 "BAJO"

# threshold configurable (ej. 50000€)
```

**Visualización Power BI**: Medidor con umbrales (rojo/amarillo/verde)

---

### KPI 7: Saldo Proyectado a 90 Días

```python
# Alias de KPI 4, presentación diferente
# Mismo origen: models/forecast_results.csv

projection_90d = forecast_df.tail(90)['yhat'].iloc[-1]
```

**Visualización Power BI**: Tarjeta + comparación con saldo actual

---

## 9. REGLAS DEL SISTEMA

### Reglas de Coherencia Temporal

| Código | Regla | Validación |
|--------|-------|------------|
| T1 | Fechas en rango válido | 2023-01-01 ≤ fecha ≤ 2025-12-31 |
| T2 | No hay fechas futuras en datos históricos | fecha ≤ today (al generar) |
| T3 | Orden temporal en bank_movements | date[i] >= date[i-1] |
| T4 | Invoice due_date > invoice_date | validado en generación |

### Reglas de Coherencia ERP/CRM/Banco

| Código | Regla | Validación |
|--------|-------|------------|
| E1 | Factura pagada → movimiento banco existe | link invoice_id ↔ bank reference |
| E2 | Deal ganado → factura futura en 30-90 días | crm_deals.won → invoices futura |
| E3 | Saldo banco = suma acumulativa movimientos | balance_after = Σ(amount) + initial |
| E4 | Payment método consistente con cliente | mapping customer.payment_term |

### Reglas de Control de Valores Nulos

| Código | Regla | Tratamiento |
|--------|-------|-------------|
| N1 | invoice.paid_date nulo → status ≠ 'paid' | Eliminados de análisis de cobros |
| N2 | bank_movements.description no puede ser nulo | Default: "Sin descripción" |
| N3 | crm_deals.actual_close nulo si stage ≠ 'won/lost' | Válido |
| N4 | external_factors缺失 → interpolar | Interpolación lineal |

### Reglas de Validación de Saldos

| Código | Regla | Threshold |
|--------|-------|-----------|
| S1 | Saldo banco no puede ser negativo | Alert if < 0 |
| S2 | Saldo inicial debe ser positivo | Configurable |
| S3 | Variación diaria no excesiva | |Δ| < 2x media diaria |

### Reglas de Integridad Financiera

| Código | Regla | Fórmula |
|--------|-------|---------|
| F1 | Ingresos período = Σ facturas cobradas | invoice.status='paid' |
| F2 | Gastos período = Σ movements negativos | bank.amount < 0 |
| F3 | Balance final = Balance inicial + Ingresos - Gastos | cash_flow equation |
| F4 | EBITDA = Ingresos - Gastos operativos | excluye inversiones |

### Estructura Mínima Viable del Dataset

```python
# cash_flow_daily.csv mínimos campos requeridos
required_columns = [
    'date',           # Fecha (índice)
    'cash_balance',  # Saldo final día
    'cash_inflow',   # Ingresos día
    'cash_outflow',  # Gastos día
    'net_cash',      # Flujo neto (inflow - outflow)
    'forecast'       # Predicción (nullable si futuro)
]
```

### Trazabilidad de Transformaciones

```python
# Metadata de cada transformación
transformation_log = {
    'step': 'transformer.py',
    'input': 'data/raw/invoices.csv',
    'output': 'data/processed/invoices_clean.csv',
    'rows_in': 3000,
    'rows_out': 2950,
    'transformations': [
        'remove_duplicates',
        'standardize_dates',
        'fill_null_description',
        'normalize_status'
    ],
    'timestamp': '2025-01-15T10:30:00'
}
```

---

## 10. FORECASTING Y VALIDACIÓN

### Estrategia de Forecasting

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PROPHET FORECASTING PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────┘

1. DATA PREPARATION
   └── cash_flow_daily.csv → data_prep.py
       ├── Resample a frecuencia diaria
       ├── Fill gaps (interpolación)
       ├── Añadir features:
       │   ├── day_of_week
       │   ├── month
       │   ├── quarter
       │   ├── is_month_end
       │   └── regressors externos
       └── Train/Test split (80/20 temporal)

2. MODEL TRAINING
   └── trainer.py → Prophet
       ├── modelo base:
       │   ├── growth: linear
       │   ├── seasonality_mode: multiplicative
       │   ├── yearly_seasonality: True
       │   ├── weekly_seasonality: True
       │   └── daily_seasonality: False
       │
       ├── estacionalidades:
       │   ├── yearly: Fourier order 10
       │   ├── weekly: Fourier order 3
       │   └── monthly: Fourier order 5
       │
       └── regresores adicionales:
           ├── external_interest_rate
           ├── external_sector_growth
           └── rolling_mean_7d

3. PREDICTION
   └── predictor.py
       ├── Horizonte: 90 días
       ├── Frecuencia: diaria
       ├── Intervalo confianza: 95%
       └── Output: forecast.csv + metrics

4. EVALUATION
   └── evaluator.py → métricas
       ├── MAE: Mean Absolute Error
       ├── RMSE: Root Mean Square Error
       └── MAPE: Mean Absolute Percentage Error
```

### Estructura de Serie Temporal

```python
# Formato de entrada para Prophet
df_prophet = pd.DataFrame({
    'ds': dates,           # Columna fecha
    'y': cash_balance,     # Variable objetivo
    # Regresores opcionales
    'regressor1': values
})
```

### Horizonte de Predicción

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| Horizonte | 90 días | Ciclo típico de planificación financiera |
| Frecuencia | Diaria | Resolución suficiente para tesorería |
| Intervalo confianza | 95% | Balance entre precisión y cobertura |
| Refresh | Semanal | Actualización modelo cada semana |

### Métricas de Evaluación

```python
# Métricas obligatorias

# MAE (Mean Absolute Error)
mae = mean_absolute_error(y_true, y_pred)
# Objetivo: < 10000€

# RMSE (Root Mean Square Error)
rmse = sqrt(mean_squared_error(y_true, y_pred))
# Objetivo: < 15000€

# MAPE (Mean Absolute Percentage Error)
mape = mean_absolute_percentage_error(y_true, y_pred)
# Objetivo: < 5%

def mean_absolute_percentage_error(y_true, y_pred):
    """Calcula MAPE evitando división por cero"""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    # Filter out zero values
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
```

### Validación Cruzada Temporal

```python
# TimeSeriesSplit para validación
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)

for train_idx, test_idx in tscv.split(df_prophet):
    train = df_prophet.iloc[train_idx]
    test = df_proplit.iloc[test_idx]
    
    model = Prophet()
    model.fit(train)
    forecast = model.predict(test)
    
    # Calcular métricas en cada fold
```

---

## 11. SISTEMA DE ALERTAS

### Arquitectura de Alertas

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SISTEMA DE ALERTAS                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CHECKER   │────▶│  NOTIFIER   │────▶│   TELEGRAM  │
│   (Lógica)  │     │ (Formato)   │     │    BOT      │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
config/alerts.yaml    templates/          admin chat_id
                  alert_messages.json
```

### Condiciones de Alerta

| Código | Condición | Threshold | Severidad |
|--------|-----------|-----------|-----------|
| A1 | Cash Balance < umbral | 50,000€ | CRÍTICA |
| A2 | Variación 7 días < -15% | -15% | ALTA |
| A3 | Desviación forecast > 10% | 10% | MEDIA |
| A4 | Saldo proyectado 90d < 0 | 0€ | CRÍTICA |
| A5 | Movimiento anómalo detectado | 3x media | MEDIA |
| A6 | Predicción below floor | 25,000€ | ALTA |

### Lógica de Chequeo

```python
# src/alerts/checker.py

def check_alerts(cash_data: pd.DataFrame, 
                 forecast_data: pd.DataFrame,
                 config: dict) -> List[Alert]:
    
    alerts = []
    current_balance = cash_data.iloc[-1]['cash_balance']
    forecast_90d = forecast_data.iloc[-1]['yhat']
    
    # A1: Balance crítico
    if current_balance < config['thresholds']['min_balance']:
        alerts.append(Alert(
            code='A1',
            severity='CRITICAL',
            message=f"💰 SALDO CRÍTICO: {current_balance:,.0f}€ "
                   f"(mínimo: {config['thresholds']['min_balance']:,.0f}€)"
        ))
    
    # A2: Caída semanal
    cash_7d_ago = cash_data.iloc[-7]['cash_balance']
    variation_7d = (current_balance - cash_7d_ago) / cash_7d_ago * 100
    
    if variation_7d < config['thresholds']['min_variation_7d']:
        alerts.append(Alert(
            code='A2',
            severity='HIGH',
            message=f"📉 CAÍDA SEMANAL: {variation_7d:.1f}% "
                   f"(7 días: {cash_7d_ago:,.0f}€ → {current_balance:,.0f}€)"
        ))
    
    # A4: Proyección negativa
    if forecast_90d < 0:
        alerts.append(Alert(
            code='A4',
            severity='CRITICAL',
            message=f"⚠️ PROYECCIÓN NEGATIVA: Saldo proyectado a 90 días: "
                   f"{forecast_90d:,.0f}€"
        ))
    
    return alerts
```

### Formato de Notificación Telegram

```python
# Mensaje formateado
message = """
🚨 *ALERTA DE TESORERÍA* 🚨

*Código*: A1 - SALDO CRÍTICO
*Severidad*: 🔴 CRÍTICA
*Fecha*: 2025-01-15 09:30:00

*Detalle*:
Saldo actual: 45,230€
Umbral mínimo: 50,000€
Diferencia: -4,770€

*Recomendación*: Revisar próximas facturas pendientes de cobro.
"""

# Envío
bot.send_message(chat_id=admin_chat_id, 
                 text=message,
                 parse_mode='Markdown')
```

### Programación de Ejecución

```python
# config/scheduler.yaml
scheduler:
  alert_check:
    frequency: "0 */6 * * *"  # Cada 6 horas
    enabled: true
  
  forecast_refresh:
    frequency: "0 8 * * 1"     # Lunes 8:00
    enabled: true
```

---

## 12. STACK TECNOLÓGICO RECOMENDADO

### Stack Principal

| Componente | Tecnología | Versión | Justificación |
|------------|------------|---------|---------------|
| Lenguaje | Python | 3.10+ | Mayor ecosistema ML/DS |
| Datos | Pandas | ≥2.0.0 | Eficiencia y sintaxis moderna |
| Forecasting | Prophet | ≥1.1 | Robusto, maneja estacionalidad |
| Base de datos | SQLite | 3.x | Simple, sin setup, ideal prototipos |
| Visualización | Power BI | Latest | Estándar empresarial |
| Notificaciones | Telegram Bot API | Latest | Gratuito, push notifications |

### Librerías ETL

```python
# requirements.txt - ETL
pandas>=2.0.0
numpy>=1.24.0
python-dateutil>=2.8.0
```

### Librerías Forecasting

```python
# requirements.txt - Forecasting
prophet>=1.1.0
scikit-learn>=1.3.0  # Métricas
```

### Librerías Generación Sintética

```python
# requirements.txt - Synthetic Data
faker>=18.0.0
```

### Librerías Utilidades

```python
# requirements.txt - Utils
pyyaml>=6.0         # Config files
loguru>=0.7.0       # Logging mejorado
telegram>=2.0      # Bot Telegram
```

### Librerías Testing

```python
# requirements.txt - Testing
pytest>=7.4.0
pytest-cov>=4.1.0
```

### Archivo requirements.txt Consolidado

```txt
pandas>=2.0.0
numpy>=1.24.0
python-dateutil>=2.8.0
prophet>=1.1.0
scikit-learn>=1.3.0
faker>=18.0.0
pyyaml>=6.0
loguru>=0.7.0
python-telegram-bot>=20.0
pytest>=7.4.0
pytest-cov>=4.1.0
```

---

## ANEXO: CONSIDERACIONES FINALES

### Limitaciones del Sistema

1. **Datos sintéticos**: Los patrones son simulados, no reales
2. **Prophet局限性**: Asume estacionalidad constante, no captura shocks
3. **Moneda única**: Solo EUR, sin conversión de divisas
4. **Un solo banco**: No simula múltiples cuentas
5. **Sin fraude**: Datos siempre coherentes

### Recomendaciones de Extensión Futura

1. Integrar más fuentes (factoring, confirming)
2. Añadir modelos alternativos (XGBoost, LightGBM)
3. Implementar detección de anomalías
4. Añadir simulación Monte Carlo
5. Integrar con herramientas de gestión (SAP simplificado)

### Métricas de Éxito del Proyecto

| Métrica | Target | Validación |
|---------|--------|------------|
| MAPE forecasting | < 5% | Backtesting |
| Coherencia datos | 100% R1-R6 | Validator |
| KPIs cobertura | 7/7 implementados | Dashboard |
| Alertas funcionales | 6/6 configuradas | Testing |
| Tiempo ejecución ETL | < 5 min | Benchmarks |