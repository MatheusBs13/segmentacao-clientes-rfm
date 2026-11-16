# Dados

Os arquivos de dados **não são versionados** (ver `.gitignore`). Para reproduzir o projeto:

1. Baixe o **Online Retail II** no repositório da UCI:
   https://archive.ics.uci.edu/dataset/502/online+retail+ii
   (arquivo `online_retail_II.xlsx`, cerca de 43 MB)
2. Salve o arquivo em `data/raw/online_retail_II.xlsx`.
3. Rode o notebook `notebooks/01_eda_limpeza.ipynb`. Ele junta as duas abas da planilha, limpa os dados e salva os resultados em `data/interim/` e `data/processed/`.

**Sobre o dataset:** transações de uma loja online do Reino Unido, de 01/12/2009 a 09/12/2011, com cerca de 1,07 milhão de linhas e 8 colunas.

Citação: Chen, D. (2012). *Online Retail II* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5CG6D
