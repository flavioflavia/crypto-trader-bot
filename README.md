# 🤖 Crypto Trader Bot

Um robô trader automático para o mercado de criptomoedas na Binance, utilizando análise técnica com múltiplos indicadores.

## ⚙️ Tecnologias e Indicadores

- RSI, MACD, SMA, EMA, Bandas de Bollinger, Estocástico, Volume
- Python 3 + Binance API
- Log com RotatingFileHandler
- Executado como serviço no Linux
- Logrotate integrado

## 🚀 Como usar

```bash
pip install numpy==1.26.4 pandas==2.1.4 pandas_ta==0.3.14b0 python-binance tenacity

Adicione as suas chaves de API no config.py
API_KEY = 'sua_api_key_aqui'
API_SECRET = 'seu_api_secret_aqui'

python3 main.py


#🛡️ Aviso
Este bot é para fins educacionais. Use com cautela em ambientes de produção e nunca arrisque valores que não pode perder.