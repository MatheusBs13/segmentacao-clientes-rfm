# 🛍️ Segmentação de Clientes com RFM e Clusterização

Projeto de ciência de dados que segmenta os clientes de uma loja online a partir do histórico de compras, usando **RFM** (Recência, Frequência e Valor Monetário) e comparando algoritmos de clusterização. O objetivo é transformar os grupos encontrados em **perfis de cliente com ações de marketing** para cada um.

> 🚧 **Status:** em andamento. Os resultados serão preenchidos ao final de cada etapa.

## 🎯 Problema de negócio

Tratar todos os clientes da mesma forma desperdiça dinheiro de marketing. Quem são os clientes mais valiosos? Quem está esfriando e vale tentar reativar? Quem compra pouco, mas pode crescer?

## 📊 Dados

[Online Retail II (UCI)](https://archive.ics.uci.edu/dataset/502/online+retail+ii): transações de uma loja online do Reino Unido entre dez/2009 e dez/2011 (cerca de 1,07 milhão de linhas). Veja [`data/README.md`](data/README.md) para baixar.

## 🧭 Método

1. **EDA e limpeza**: tratar clientes sem ID, cancelamentos, preços e quantidades inválidas, duplicatas
2. **Engenharia de features RFM**: recência, frequência e valor monetário por cliente
3. **Pré-processamento**: tratamento de assimetria (log) e padronização
4. **Clusterização**: K-Means, DBSCAN e GMM, comparados com silhouette e Davies-Bouldin
5. **Interpretação**: perfil de cada segmento e ação recomendada
6. **Dashboard**: app em Streamlit para explorar os segmentos

## 📁 Estrutura

```
├── data/            # dados (não versionados) e instruções de download
├── notebooks/       # 01_eda_limpeza, 02_rfm, 03_clusterizacao ...
├── src/             # funções reutilizáveis
├── app/             # dashboard Streamlit
├── reports/figures/ # gráficos para o README
└── requirements.txt
```

## ▶️ Como rodar

```bash
git clone https://github.com/MatheusBs13/segmentacao-clientes-rfm.git
cd segmentacao-clientes-rfm
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

Depois baixe os dados conforme [`data/README.md`](data/README.md) e abra `notebooks/01_eda_limpeza.ipynb`.

## ✅ Roadmap

- [ ] 01 — EDA e limpeza
- [ ] 02 — Features RFM
- [ ] 03 — Clusterização e comparação de algoritmos
- [ ] 04 — Perfis de segmento e recomendações
- [ ] 05 — Dashboard em Streamlit

## 📈 Resultados

_A preencher ao final do projeto._

## 👤 Autor

[MatheusBs13](https://github.com/MatheusBs13)
