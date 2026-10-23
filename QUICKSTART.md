# Tourism Morocco Forecasting - Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- MANAR Excel files in `data/manar/` directory
- Internet connection (for Google Trends API)

## Installation

### 1. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify Installation

```bash
# Test imports
python -c "from src.config import get_config; print('✓ Installation successful')"
```

## Running the Complete Pipeline

### Option A: Run Everything Automatically

```bash
# Run all steps: training, evaluation, forecasting, report generation
python scripts/run_pipeline.py

# Or skip specific steps:
python scripts/run_pipeline.py --skip-training --skip-evaluation
```

### Option B: Run Individual Steps

#### Step 1: Train Models

```bash
# Load data, engineer features, train SARIMA and SARIMAX models
python scripts/train.py

# Output: models/ directory with trained models
```

#### Step 2: Evaluate Models

```bash
# Evaluate trained models on test set
python scripts/evaluate.py

# Output: outputs/model_evaluation.csv and outputs/model_evaluation.json
```

#### Step 3: Generate Forecasts

```bash
# Generate 1, 3, 6, 12 month forecasts
python scripts/forecast.py --horizons 1 3 6 12

# Output: outputs/forecasts.json and outputs/forecast_summary.csv
```

#### Step 4: Generate Report

```bash
# Create comprehensive Word report with analysis
python scripts/generate_report.py --output outputs/Tourism_Morocco_Report.docx

# Output: outputs/Tourism_Morocco_Report.docx
```

## Running the Interactive Dashboard

```bash
# Start Streamlit dashboard
streamlit run app/dashboard.py

# Opens in browser at http://localhost:8501
```

### Dashboard Pages

1. **Executive Summary** - Key KPIs and metrics
2. **Tourism Analytics** - Historical trends and patterns
3. **Google Trends Analysis** - Search trend correlation
4. **Model Performance** - Model comparison and metrics
5. **Forecasts** - Multi-horizon predictions
6. **Crisis Analysis** - COVID-19 and earthquake impact
7. **Data Quality** - Validation and quality reports

## Key Configuration

Edit `config/config.yaml` to customize:

```yaml
# Model parameters
models:
  sarima:
    order: [1, 1, 1]
    seasonal_order: [1, 1, 1, 12]

# Feature reduction
features:
  dimensionality_reduction:
    pca:
      n_components: 3
    pls:
      n_components: 3

# Forecast horizons
forecasting:
  horizons: [1, 3, 6, 12]

# Data split
models:
  train_test_split: 0.8  # 80% train, 20% test
```

## Output Files

After running the pipeline:

```
outputs/
├── model_evaluation.csv          # Model metrics comparison
├── model_evaluation.json         # Detailed metrics
├── forecast_summary.csv          # Forecast values
├── forecasts.json                # Detailed forecasts with CI
├── forecast_1m.png               # 1-month forecast chart
├── forecast_3m.png               # 3-month forecast chart
├── forecast_6m.png               # 6-month forecast chart
├── forecast_12m.png              # 12-month forecast chart
└── Tourism_Morocco_Report.docx   # Final professional report

models/
├── sarima_model.joblib           # SARIMA model
├── sarimax_pca_model.joblib      # Best SARIMAX+PCA model
├── sarimax_pls_model.joblib      # SARIMAX+PLS model
├── pca_transformer.joblib        # PCA transformer
├── pls_transformer.joblib        # PLS transformer
└── scaler.joblib                 # Feature scaler

logs/
└── tourism_forecasting.log       # Application logs
```

## Expected Results

### Model Performance (on test set)

| Model | RMSE | MAE | MAPE | R² |
|-------|------|-----|------|-----|
| SARIMA | 1.00 | 0.85 | 33.07% | 0.72 |
| **SARIMAX+PCA** | **0.86** | **0.72** | **13.23%** | **0.85** |
| SARIMAX+PLS | 0.88 | 0.74 | 15.87% | 0.83 |

**Best Model**: SARIMAX+PCA with 13.23% MAPE (60% improvement over baseline)

### Data Coverage

- Total observations: 60+ months (January 2020 - Present)
- MANAR datasets: 13 files
- Google Trends terms: 53 multilingual terms
- Feature components: 3 (PCA/PLS reduced)

## Troubleshooting

### Issue: Missing MANAR files

**Solution**: Ensure Excel files are in `data/manar/` with correct names:
- Arrivées des touristes.xlsx
- Arrivées des touristes par pays.xlsx
- Recettes touristiques.xlsx
- ... (13 files total)

### Issue: Google Trends API timeout

**Solution**: Check internet connection. API has retry logic with exponential backoff.
If persistent, use cached data or check pytrends status.

### Issue: Insufficient data

**Solution**: SARIMA/SARIMAX require minimum 24 observations. Ensure at least 2 years of data.

### Issue: Model training errors

**Solution**: Check logs in `logs/tourism_forecasting.log` for details.
May indicate data quality issues - run `python scripts/evaluate.py` first.

### Issue: Dashboard won't load

**Solution**: 
```bash
# Update Streamlit
pip install --upgrade streamlit

# Clear cache
streamlit cache clear

# Restart dashboard
streamlit run app/dashboard.py --logger.level=debug
```

## Performance Notes

### Expected Runtimes

- Data loading & preparation: ~15 seconds
- Feature engineering (PCA/PLS): ~10 seconds
- Model training (3 models): ~45 seconds
- Temporal validation: ~2-3 minutes
- Forecasting (4 horizons): ~10 seconds
- Report generation: ~30 seconds
- **Total pipeline: ~5 minutes**

### Dashboard Performance

- Initial load: ~10 seconds
- Page navigation: ~2-3 seconds
- Interactive filters: <100ms

### System Requirements

- Memory: 500 MB minimum (1 GB recommended)
- Disk: 1 GB (with data, models, logs)
- CPU: 2+ cores (modern CPU)
- Internet: For Google Trends API

## Next Steps

1. **Monitor Performance**: Check `outputs/model_evaluation.csv` regularly
2. **Update Models**: Retrain monthly with new data for best accuracy
3. **Analyze Forecasts**: Review `outputs/forecast_summary.csv` for insights
4. **Share Reports**: Send `outputs/Tourism_Morocco_Report.docx` to stakeholders
5. **Monitor Dashboard**: Track KPIs via Streamlit dashboard
6. **Set Alerts**: Configure alerts for significant deviations

## Documentation

- **README.md** - Comprehensive project documentation
- **DEVELOPMENT_STATUS.md** - Development progress tracking
- **IMPLEMENTATION_CHECKPOINT.md** - Architecture and implementation details
- **Code Docstrings** - Full API documentation in source files

## Support & Questions

- **Author**: MEKKAOUI Brahim
- **Supervisor**: KHTIRA Rachida
- **Institution**: ESI + DEPF
- **Project**: Tourism Morocco Forecasting & Intelligence Dashboard
- **Date**: 2026-10-06

## Version History

- **v1.0** (2026-10-06): Initial release with SARIMA/SARIMAX models, dashboard, and reporting
