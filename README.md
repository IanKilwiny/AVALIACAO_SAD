# Dashboard RU — AVALIACAO_SAD

Painel interativo para análise de agendamentos, faltas, desperdício e satisfação.

Pré-requisitos

- Python 3.10+

Criar o ambiente virtual

```bash
python -m venv venv
```

Ativar o ambiente virtual no Windows

```bash
/venv/Script/activate
```

Ativar o ambiente virtual no Linux

```bash
source venv/bin/activate

```

Instalação

```bash
pip install -r requirements.txt
```

Executar

```bash
streamlit run app..py
```

Observações

- O arquivo padrão `rucedro.csv` é usado se nenhum CSV for carregado via uploader.
- É possível fazer upload opcional de dois CSVs:
  - CSV de desperdício: colunas `menu_id,wasted_kg`
  - CSV de satisfação: colunas `menu_id,satisfaction_score`

