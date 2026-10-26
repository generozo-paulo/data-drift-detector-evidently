import pytest
import pandas as pd
from src.schemas import DriftDetectionConfig
from src.detector import ClinicalDriftEngine

def test_generate_clinical_cohorts():
    ref_df, curr_df = ClinicalDriftEngine.generate_clinical_cohorts(n_ref=200, n_curr=100, inject_drift=False)
    assert len(ref_df) == 200
    assert len(curr_df) == 100
    assert "glucose_mg_dl" in ref_df.columns
    assert "creatinine_mg_dl" in curr_df.columns

def test_psi_calculation_zero_drift():
    ref_df, curr_df = ClinicalDriftEngine.generate_clinical_cohorts(n_ref=1000, n_curr=1000, inject_drift=False, random_state=42)
    psi = ClinicalDriftEngine.calculate_psi(ref_df["systolic_bp"].values, curr_df["systolic_bp"].values)
    # Sem drift o PSI deve ser muito baixo (< 0.1)
    assert psi < 0.15

def test_drift_detection_with_induced_shift():
    config = DriftDetectionConfig(
        reference_sample_size=1000,
        current_sample_size=500,
        drift_p_value_threshold=0.05,
        concept_drift_threshold_psi=0.15
    )
    ref_df, curr_df = ClinicalDriftEngine.generate_clinical_cohorts(
        n_ref=config.reference_sample_size,
        n_curr=config.current_sample_size,
        inject_drift=True,
        random_state=42
    )
    report = ClinicalDriftEngine.analyze_dataset_drift(ref_df, curr_df, config)

    assert report.total_features_evaluated > 0
    assert report.drifted_features_count > 0
    assert report.dataset_drift_detected is True
    assert report.recommended_action in ["retrain_recommended", "immediate_retrain_and_alert"]
