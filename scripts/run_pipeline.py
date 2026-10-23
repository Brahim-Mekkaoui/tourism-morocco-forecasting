#!/usr/bin/env python
"""
Complete Pipeline Orchestration

Runs the entire forecasting pipeline end-to-end:
1. Training (models/train.py)
2. Evaluation (scripts/evaluate.py)
3. Forecasting (scripts/forecast.py)
4. Report Generation (scripts/generate_report.py)

Usage:
    python scripts/run_pipeline.py [--skip-training] [--skip-evaluation] [--skip-forecast] [--skip-report]

Author: MEKKAOUI Brahim
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime

from src.logger import get_logger

logger = get_logger(__name__)


def run_command(cmd, description):
    """Run a shell command and log results."""
    logger.info("=" * 80)
    logger.info(description)
    logger.info("=" * 80)

    try:
        result = subprocess.run(cmd, shell=True, capture_output=False)
        if result.returncode == 0:
            logger.info(f"✓ {description} completed successfully")
            return True
        else:
            logger.error(f"✗ {description} failed with exit code {result.returncode}")
            return False
    except Exception as e:
        logger.error(f"✗ Error running {description}: {e}")
        return False


def main():
    """Run complete pipeline."""
    parser = argparse.ArgumentParser(description='Run complete forecasting pipeline')
    parser.add_argument('--skip-training', action='store_true', help='Skip training step')
    parser.add_argument('--skip-evaluation', action='store_true', help='Skip evaluation step')
    parser.add_argument('--skip-forecast', action='store_true', help='Skip forecasting step')
    parser.add_argument('--skip-report', action='store_true', help='Skip report generation')

    args = parser.parse_args()

    logger.info("\n" + "=" * 80)
    logger.info("TOURISM MOROCCO FORECASTING PIPELINE")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    steps = []

    # Step 1: Training
    if not args.skip_training:
        steps.append((
            "python scripts/train.py",
            "STEP 1: Training Models"
        ))

    # Step 2: Evaluation
    if not args.skip_evaluation:
        steps.append((
            "python scripts/evaluate.py",
            "STEP 2: Evaluating Models"
        ))

    # Step 3: Forecasting
    if not args.skip_forecast:
        steps.append((
            "python scripts/forecast.py --horizons 1 3 6 12",
            "STEP 3: Generating Forecasts"
        ))

    # Step 4: Report Generation
    if not args.skip_report:
        steps.append((
            "python scripts/generate_report.py --output outputs/Tourism_Morocco_Report.docx",
            "STEP 4: Generating Report"
        ))

    # Run all steps
    results = []
    for cmd, desc in steps:
        success = run_command(cmd, desc)
        results.append((desc, success))

        if not success:
            logger.error(f"Pipeline stopped at: {desc}")
            break

        logger.info("")

    # Summary
    logger.info("=" * 80)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 80)

    for desc, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        logger.info(f"{status}: {desc}")

    # Overall result
    all_passed = all(success for _, success in results)

    logger.info("\n" + "=" * 80)
    if all_passed:
        logger.info("✓ PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info("\nGenerated files:")
        logger.info("  - models/: Trained model files")
        logger.info("  - outputs/: Results, forecasts, and visualizations")
        logger.info("  - outputs/Tourism_Morocco_Report.docx: Final report")
        logger.info("\nNext steps:")
        logger.info("  1. Review outputs/model_evaluation.csv for model metrics")
        logger.info("  2. Check outputs/forecast_summary.csv for forecast values")
        logger.info("  3. Open outputs/Tourism_Morocco_Report.docx for final report")
        logger.info("  4. Run 'streamlit run app/dashboard.py' to launch interactive dashboard")
    else:
        logger.error("✗ PIPELINE FAILED")
        logger.error("=" * 80)

    logger.info(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
