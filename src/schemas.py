from pydantic import BaseModel, Field
from typing import List, Literal, Dict

class DriftDetectionConfig(BaseModel):
    reference_sample_size: int = Field(default=1500, ge=100)
    current_sample_size: int = Field(default=800, ge=50)
    drift_p_value_threshold: float = Field(default=0.05, gt=0.0, lt=1.0)
    statistical_test: Literal["ks_2samp", "psi", "wasserstein"] = "ks_2samp"
    concept_drift_threshold_psi: float = Field(default=0.15, gt=0.0)

class FeatureDriftResult(BaseModel):
    feature_name: str
    statistic_value: float
    p_value: float
    psi_value: float
    drift_detected: bool
    severity: Literal["none", "warning", "critical"]
    summary: str

class ClinicalDriftReport(BaseModel):
    timestamp: str
    total_features_evaluated: int
    drifted_features_count: int
    dataset_drift_detected: bool
    share_drifted_features: float
    feature_metrics: List[FeatureDriftResult]
    recommended_action: Literal["maintain", "retrain_recommended", "immediate_retrain_and_alert"]
