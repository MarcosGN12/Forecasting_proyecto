# Cash Flow Forecasting System

Sistema de forecasting financiero para **Industrial Metálica Portillo S.L.** - Empresa mediana de fabricación de componentes metálicos ubicada en Portillo de Toledo.

---

## 📋 Resumen

| Componente | Estado | Descripción |
|------------|--------|-------------|
| Datos sintéticos | ✅ | 3,107 facturas, 2,795 movimientos banco |
| ETL | ✅ | Validación coherencia 6/6 reglas |
| Forecasting | ✅ | Prophet, MAPE 2.28% |
| Power BI | ✅ | 3 archivos exportados |
| SQLite | ✅ | Base de datos actualizada |
| Telegram | ✅ | Alertas configuradas |

---

## 🚀 Inicio Rápido

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar pipeline completo
python main.py
```

---

## 📁 Estructura del Proyecto

```
Forecasting_proyecto/
├── main.py                      # Pipeline principal (ejecutar esto)
├── requirements.txt            # Dependencias Python
├── .env                        # Variables de entorno (TOKENs)
├── SPEC.md                     # Especificación técnica detallada
│
├── config/                     # Configuración
│   ├── empresa.yaml           # Datos empresa simulada
│   ├── generation_params.yaml  # Parámetros generación datos
│   └── alerts.yaml             # Configuración alertas Telegram
│
├── src/
│   ├── generators/             # Generación datos sintéticos
│   │   ├── main_generator.py
│   │   ├── company_generator.py
│   │   ├── invoice_generator.py
│   │   ├── bank_generator.py
│   │   └── crm_generator.py
│   │
│   ├── etl/                   # Pipeline ETL
│   │   ├── extractor.py       # Carga datos raw
│   │   ├── transformer.py     # Limpieza y transformación
│   │   └── validator.py       # Validación coherencia
│   │
│   ├── forecasting/            # Modelo Prophet
│   │   ├── data_prep.py       # Prepara datos
│   │   ├── trainer.py         # Entrena modelo
│   │   ├── predictor.py      # Genera predicciones
│   │   └── evaluator.py       # Calcula métricas
│   │
│   ├── alerts/                # Sistema alertas
│   │   ├── checker.py        # Evalúa condiciones
│   │   └── notifier.py       # Envía notificaciones
│   │
│   ├── database/              # SQLite
│   │   └── db_manager.py     # Gestor base datos
│   │
│   └── utils/                 # Utilidades
│       └── run_pipeline.py   # Pipeline secuencial
│
├── data/
│   ├── raw/                   # Datos sintéticos originales
│   │   ├── invoices.csv
│   │   ├── bank_movements.csv
│   │   ├── crm_deals.csv
│   │   └── external_factors.csv
│   │
│   └── processed/             # Datos transformados
│       ├── cash_flow_daily.csv
│       └── ...
│
├── models/                    # Modelo entrenado
│   ├── prophet_cashflow_model.json
│   └── forecast_results.csv
│
├── powerbi/                   # Datos para Power BI
│   ├── cash_flow_daily.csv
│   ├── forecast_results.csv
│   └── kpis.csv
│
└── tests/                     # Tests unitarios
    ├── test_generators.py
    ├── test_etl.py
    ├── test_forecasting.py
    └── test_alerts.py
```

---

## ⚙️ Configuración

### 1. Archivo `.env`

```bash
# Telegram (ya configurado)
TELEGRAM_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id

# Database
DATABASE_PATH=data/cashflow.db

# Alert Thresholds
MIN_BALANCE_THRESHOLD=50000
PROJECTION_FLOOR=25000
```

### 2. Configurar Telegram (si no está hecho)

1. Busca **@BotFather** en Telegram
2. Envía `/newbot`
3. Copia el token en `.env`
4. Busca **@userinfobot** y envía un mensaje
5. Copia tu `chat_id` en `.env`

---

## ▶️ Ejecución

### Opción 1: Pipeline completo (recomendado)

```bash
python main.py
```

Esto ejecuta todas las fases automáticamente:
- Generación datos → ETL → Forecasting → Métricas → Power BI → Alertas → SQLite

### Opción 2: Por fases

```bash
# Fase 0: Generar datos
python -m src.generators.main_generator

# Fases 1-2: ETL
python -c "from src.etl.extractor import DataExtractor; from src.etl.transformer import DataTransformer; e=DataExtractor(); d=e.load_all(); t=DataTransformer(); r=t.transform_all(d); t.save_processed(r)"

# Fase 3: Forecasting
python -c "from src.forecasting.trainer import train_prophet_model; from src.forecasting.data_prep import prepare_forecasting_data; d=prepare_forecasting_data(); train_prophet_model(d['train'])"
```

---

## 📊 Métricas del Modelo

| Métrica | Valor | Objetivo |
|---------|-------|----------|
| MAPE | 2.28% | < 5% ✅ |
| MAE | 250,976€ | - |
| RMSE | 273,281€ | - |

---

## 💰 KPIs Financieros

| KPI | Descripción | Campo |
|-----|-------------|-------|
| Cash Balance | Saldo actual de cuenta | `current_cash_balance` |
| Cash Inflow | Ingresos últimos 30 días | `cash_inflow_30d` |
| Cash Outflow | Gastos últimos 30 días | `cash_outflow_30d` |
| Forecast 90d | Proyección a 90 días | `forecast_90d` |
| Liquidity Risk | Nivel de riesgo | `ALTO/MEDIO/BAJO` |

---

## 📈 Power BI

### Archivos a importar

1. `powerbi/kpis.csv` - Resumen KPIs
2. `powerbi/cash_flow_daily.csv` - Serie temporal
3. `powerbi/forecast_results.csv` - Predicciones

### Visualizaciones recomendadas

| Visualización | Tipo | Campo |
|---------------|------|-------|
| Saldo actual | Tarjeta | `current_cash_balance` |
| Ingresos 30d | Tarjeta | `cash_inflow_30d` |
| Gastos 30d | Tarjeta | `cash_outflow_30d` |
| Forecast 90d | Tarjeta | `forecast_90d` |
| Evolución saldo | Gráfico línea | `date` vs `cash_balance` |
| Forecast vs real | Gráfico línea | `ds` vs `yhat`/`y` |

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## 🔄 Automatización (Opcional)

### Windows (Tarea Programadora)

```cmd
schtasks /create /tn "CashFlow" /tr "python C:\ruta\a\main.py" /sc daily /st 08:00
```

### Linux/Mac (Cron)

```bash
0 8 * * * cd /ruta/proyecto && python main.py
```

---

## 📞 Soporte

- Revisa `SPEC.md` para especificación técnica detallada
- Los logs se guardan en `logs/`
- La base de datos está en `data/cashflow.db`

---

## Licencia

MIT