# Dashboard RU — AVALIACAO_SAD

Painel interativo para análise de agendamentos, faltas, desperdício e satisfação.

Pré-requisitos

- Python 3.10+

Instalação

```bash
python -m pip install -r requirements.txt
```

Executar

```bash
streamlit run dashboard.py
```

Observações

- O arquivo padrão `rucedro.csv` é usado se nenhum CSV for carregado via uploader.
- É possível fazer upload opcional de dois CSVs:
  - CSV de desperdício: colunas `menu_id,wasted_kg`
  - CSV de satisfação: colunas `menu_id,satisfaction_score`

