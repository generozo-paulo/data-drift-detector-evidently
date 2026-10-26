# CRISP-DM: Entendimento de Negócio (Business Understanding)

## 1. Problema de Negócio em Saúde
Modelos preditivos implantados em ambiente hospitalar sofrem degradação silenciosa contínua devido a:
1. **Alterações demográficas sazonais** (ex: aumento de idosos no inverno).
2. **Mudança de protocolos laboratoriais** (ex: troca de kits de reagentes que alteram a distribuição basal de creatinina ou PCR).
3. **Mutações epidemiológicas** (novas cepas patogênicas alterando tempo de internação e desfecho).

## 2. Riscos Clínicos
A inferência com modelo enviesado ou desalinhado pode gerar falsos negativos em triagem de sepse ou superalocação inadequada de leitos de UTI.

## 3. Critérios de Sucesso Técnico
- Detecção estatística formal de Kolmogorov-Smirnov bicaudal (KS-test) em cada biomarcador.
- Cálculo de Population Stability Index (PSI) com estratificação em decis.
- Acionamento automático de alertas e recomendação de retreinamento quando a proporção de features com drift superar 30%.
