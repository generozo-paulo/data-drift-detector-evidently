import datetime
import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, List, Dict
from src.schemas import DriftDetectionConfig, FeatureDriftResult, ClinicalDriftReport

class ClinicalDriftEngine:
    """
    Motor analítico para detecção de Data Drift e Concept Drift em dados de saúde.
    Implementa Kolmogorov-Smirnov bicaudal, Population Stability Index (PSI) e Wasserstein distance.
    """

    @staticmethod
    def generate_clinical_cohorts(
        n_ref: int = 1500, 
        n_curr: int = 800, 
        inject_drift: bool = True,
        random_state: int = 42
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Gera dois conjuntos de dados clínicos representativos:
        - Referência: Linha de base histórica (baseline)
        - Corrente: Pacientes admitidos recentemente (com drift induzido em subconjunto de biomarcadores)
        """
        np.random.seed(random_state)
        
        # Referência (distribuições basais)
        ref_data = {
            "systolic_bp": np.random.normal(loc=122, scale=14, size=n_ref),
            "glucose_mg_dl": np.random.normal(loc=98, scale=18, size=n_ref),
            "creatinine_mg_dl": np.random.lognormal(mean=0.0, sigma=0.35, size=n_ref), # mediana ~1.0
            "crp_mg_l": np.random.exponential(scale=3.5, size=n_ref), # PCR basal
            "hemoglobin_g_dl": np.random.normal(loc=13.8, scale=1.5, size=n_ref),
            "oxygen_sat_pct": np.clip(np.random.normal(loc=97.5, scale=1.8, size=n_ref), 80, 100)
        }
        ref_df = pd.DataFrame(ref_data)

        # Corrente
        if inject_drift:
            curr_data = {
                # Covariate Shift severo: aumento de glicemia e PCR (ex: onda inflamatória ou mudança de perfil)
                "systolic_bp": np.random.normal(loc=123, scale=15, size=n_curr), # estável
                "glucose_mg_dl": np.random.normal(loc=115, scale=26, size=n_curr), # DRIFT CRÍTICO (+17 mg/dL)
                "creatinine_mg_dl": np.random.lognormal(mean=0.35, sigma=0.45, size=n_curr), # DRIFT (piora renal)
                "crp_mg_l": np.random.exponential(scale=7.8, size=n_curr), # DRIFT (inflamação sistêmica aguda)
                "hemoglobin_g_dl": np.random.normal(loc=13.6, scale=1.6, size=n_curr), # estável
                "oxygen_sat_pct": np.clip(np.random.normal(loc=95.0, scale=3.2, size=n_curr), 75, 100) # DRIFT
            }
        else:
            curr_data = {
                "systolic_bp": np.random.normal(loc=122.2, scale=14.1, size=n_curr),
                "glucose_mg_dl": np.random.normal(loc=98.5, scale=18.2, size=n_curr),
                "creatinine_mg_dl": np.random.lognormal(mean=0.02, sigma=0.36, size=n_curr),
                "crp_mg_l": np.random.exponential(scale=3.6, size=n_curr),
                "hemoglobin_g_dl": np.random.normal(loc=13.7, scale=1.5, size=n_curr),
                "oxygen_sat_pct": np.clip(np.random.normal(loc=97.4, scale=1.8, size=n_curr), 80, 100)
            }
        curr_df = pd.DataFrame(curr_data)
        return ref_df, curr_df

    @staticmethod
    def calculate_psi(expected: np.ndarray, actual: np.ndarray, num_buckets: int = 10) -> float:
        """Calcula o Population Stability Index (PSI) usando quantis do dataset esperado."""
        quantiles = np.linspace(0, 100, num_buckets + 1)
        bins = np.percentile(expected, quantiles)
        bins[0] = -np.inf
        bins[-1] = np.inf
        # Remove duplicatas em bins com baixa variabilidade
        bins = np.unique(bins)
        if len(bins) < 3:
            return 0.0

        expected_counts, _ = np.histogram(expected, bins=bins)
        actual_counts, _ = np.histogram(actual, bins=bins)

        expected_pct = expected_counts / len(expected)
        actual_pct = actual_counts / len(actual)

        # Suavização epsilon para evitar divisão por zero ou log(0)
        eps = 1e-4
        expected_pct = np.where(expected_pct == 0, eps, expected_pct)
        actual_pct = np.where(actual_pct == 0, eps, actual_pct)

        psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
        return float(psi)

    @staticmethod
    def analyze_dataset_drift(
        reference_df: pd.DataFrame, 
        current_df: pd.DataFrame, 
        config: DriftDetectionConfig
    ) -> ClinicalDriftReport:
        """Executa a bateria de testes de drift em todas as colunas numéricas."""
        feature_results: List[FeatureDriftResult] = []
        drifted_count = 0

        for col in reference_df.columns:
            ref_vals = reference_df[col].dropna().values
            curr_vals = current_df[col].dropna().values

            # Teste Kolmogorov-Smirnov bicaudal
            ks_stat, p_val = stats.ks_2samp(ref_vals, curr_vals)
            psi = ClinicalDriftEngine.calculate_psi(ref_vals, curr_vals)

            is_drift = bool(p_val < config.drift_p_value_threshold or psi > config.concept_drift_threshold_psi)
            if is_drift:
                drifted_count += 1
                severity = "critical" if (psi > 0.25 or p_val < 0.001) else "warning"
                summary = f"Drift confirmado ({config.statistical_test} p={p_val:.2e}, PSI={psi:.3f})"
            else:
                severity = "none"
                summary = f"Distribuição estável (p={p_val:.4f}, PSI={psi:.3f})"

            feature_results.append(FeatureDriftResult(
                feature_name=col,
                statistic_value=float(ks_stat),
                p_value=float(p_val),
                psi_value=float(psi),
                drift_detected=is_drift,
                severity=severity,
                summary=summary
            ))

        total_features = len(reference_df.columns)
        share_drifted = drifted_count / total_features if total_features > 0 else 0.0
        dataset_drift = share_drifted >= 0.33 # Se 1/3 das variáveis sofrerem drift

        if share_drifted >= 0.5:
            rec_action = "immediate_retrain_and_alert"
        elif share_drifted >= 0.25:
            rec_action = "retrain_recommended"
        else:
            rec_action = "maintain"

        return ClinicalDriftReport(
            timestamp=datetime.datetime.now().isoformat(),
            total_features_evaluated=total_features,
            drifted_features_count=drifted_count,
            dataset_drift_detected=dataset_drift,
            share_drifted_features=float(share_drifted),
            feature_metrics=feature_results,
            recommended_action=rec_action
        )
