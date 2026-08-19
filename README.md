# Dashboard RU — AVALIACAO_SAD

Painel interativo para análise de agendamentos, faltas, desperdício e satisfação.

Pré-requisitos

- Python 3.12 ou mais recente (o projeto foi validado com Python 3.14)

Criar o ambiente virtual

```bash
python -m venv venv
```

Ativar o ambiente virtual no Windows

```bash
.\venv\Scripts\Activate.ps1
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
streamlit run app.py
```

O aplicativo usa o arquivo `rucedro3.csv`, que deve ficar na mesma pasta do
`app.py`. Para recriar o ambiente com as versões atuais:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

