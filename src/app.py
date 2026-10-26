import streamlit as st
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go
from src.schemas import DriftDetectionConfig
from src.detector import ClinicalDriftEngine

st.set_page_config(
    page_title="Clinical Data Drift & MLOps Monitor",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Enterprise Clinical Data Drift & Concept Drift Monitor")
st.markdown("""
Monitoramento contínuo de **Covariate Shift** e **Concept Drift** em biomarcadores clínicos. 
Garante que modelos em produção permaneçam calibrados e alerta preventivamente contra degradação silenciosa.
""")

st.sidebar.header("⚙️ Parâmetros do Monitor de Drift")
p_val_thresh = st.sidebar.slider("Limiar de Significância (p-value KS-test)", min_value=0.01, max_value=0.10, value=0.05, step=0.01)
psi_thresh = st.sidebar.slider("Limiar PSI (Population Stability Index)", min_value=0.05, max_value=0.30, value=0.15, step=0.01)
inject_drift_toggle = st.sidebar.checkbox("Simular Alteração Populacional / Sazonal (Injetar Drift)", value=True)

config = DriftDetectionConfig(
    reference_sample_size=1500,
    current_sample_size=800,
    drift_p_value_threshold=p_val_thresh,
    concept_drift_threshold_psi=psi_thresh
)

ref_df, curr_df = ClinicalDriftEngine.generate_clinical_cohorts(
    n_ref=config.reference_sample_size,
    n_curr=config.current_sample_size,
    inject_drift=inject_drift_toggle
)

report = ClinicalDriftEngine.analyze_dataset_drift(ref_df, curr_df, config)

tab1, tab2, tab3 = st.tabs(["📊 Visão Geral de Drift", "🔬 Análise Detalhada por Biomarcador", "🚨 Ações & Governança MLOps"])

with tab1:
    st.subheader("Painel Executivo de Integridade Populacional")
    col1, col2, col3, col4 = st.columns(4)

    status_icon = "🔴" if report.dataset_drift_detected else "🟢"
    col1.metric("Status do Dataset", f"{status_icon} {'DRIFT DETECTADO' if report.dataset_drift_detected else 'ESTÁVEL'}")
    col2.metric("Biomarcadores com Drift", f"{report.drifted_features_count} / {report.total_features_evaluated}")
    col3.metric("Taxa de Degradação", f"{report.share_drifted_features*100:.1f}%")
    col4.metric("Ação Recomendada", report.recommended_action.upper())

    st.markdown("### Tabela Sumária de Monitoramento Contínuo")
    summary_data = []
    for f in report.feature_metrics:
        status_flag = "🚨 CRÍTICO" if f.severity == "critical" else ("⚠️ ALERTA" if f.severity == "warning" else "✅ ESTÁVEL")
        summary_data.append({
            "Biomarcador": f.feature_name,
            "KS-Statistic": f"{f.statistic_value:.4f}",
            "p-value": f"{f.p_value:.2e}",
            "PSI (Population Stability)": f"{f.psi_value:.4f}",
            "Status": status_flag,
            "Diagnóstico": f.summary
        })
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

with tab2:
    st.subheader("Curvas de Densidade Empírica (Baseline vs. População Recente)")
    selected_feature = st.selectbox("Selecione o biomarcador clínico:", list(ref_df.columns))

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ref_df[selected_feature].dropna(),
        histnorm='probability density',
        name='Referência (Baseline Histórico)',
        opacity=0.6,
        marker_color='#1f77b4'
    ))
    fig.add_trace(go.Histogram(
        x=curr_df[selected_feature].dropna(),
        histnorm='probability density',
        name='Corrente (Últimos 30 Dias)',
        opacity=0.6,
        marker_color='#d62728'
    ))
    fig.update_layout(
        barmode='overlay',
        title=f"Comparação de Distribuição: {selected_feature}",
        xaxis_title="Valor Clínico / Unidade Laboratorial",
        yaxis_title="Densidade Populacional",
        template="plotly_white",
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Protocolo de Resposta a Incidentes de Machine Learning")
    if report.recommended_action == "immediate_retrain_and_alert":
        st.error("🚨 **AÇÃO IMEDIATA REQUERIDA**: Degradação severa detectada. Disparar pipeline de re-treinamento com dados recentes e acionar equipe médica de auditoria.")
    elif report.recommended_action == "retrain_recommended":
        st.warning("⚠️ **RECOMENDAÇÃO**: Deriva moderada identificada. Agendar recalibração quinzenal do modelo preditivo.")
    else:
        st.success("✅ **SISTEMA SEGURO**: Distribuições aderentes às premissas de treinamento. Inferência em tempo real validada.")

    st.info("💡 **Conformidade Regulatória**: Os relatórios de drift são persistidos em formato imutável para atendimento aos requisitos de auditoria de algoritmos clínicos.")
