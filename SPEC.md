# Especificação Contratual (SDD) - Data Drift & Concept Drift Detector

## 1. Escopo & Objetivos
Detecção de Covariate Shift (Data Drift) em biomarcadores clínicos (ex: glicose, creatinina, leucócitos, pressão sistólica) e Concept Drift (degradação da relação P(Y|X)) entre populações hospitalares pré-pandemia / pós-pandemia ou entre centros de atendimento distintos.

## 2. Contratos de Entrada (Pydantic)

### 2.1 Schema de Configuração do Detector (`DriftDetectionConfig`)
- `reference_sample_size`: int (default: 1500)
- `current_sample_size`: int (default: 800)
- `drift_p_value_threshold`: float = 0.05
- `statistical_test`: Literal["ks_2samp", "wasserstein", "psi"] = "ks_2samp"
- `concept_drift_threshold_psi`: float = 0.15

## 3. Contratos de Saída (Pydantic)

### 3.1 Resultado por Feature (`FeatureDriftResult`)
- `feature_name`: str
- `statistic_value`: float
- `p_value`: float
- `drift_detected`: bool
- `severity`: Literal["none", "warning", "critical"]
- `summary`: str

### 3.2 Relatório Consolidado de Drift (`ClinicalDriftReport`)
- `timestamp`: str
- `total_features_evaluated`: int
- `drifted_features_count`: int
- `dataset_drift_detected`: bool
- `share_drifted_features`: float
- `feature_metrics`: List[FeatureDriftResult]
- `recommended_action`: Literal["maintain", "retrain_recommended", "immediate_retrain_and_alert"]
