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
```

## ⚙️  Para rodar como serviço do linux faça o seguinte 

1. Arquivo de Serviço Systemd (/etc/systemd/system/bot_trader.service)

```bash
[Unit]
Description=Binance Trader Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/caminho/para/seu/script
ExecStart=/usr/bin/python3 /caminho/para/seu/script/main.py
Restart=always
RestartSec=10
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=bot_trader

[Install]
WantedBy=multi-user.target
```

2. Configuração do Logrotate (/etc/logrotate.d/bot_trader)

```bash
/var/log/bot_trader.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 640 root adm
    sharedscripts
    postrotate
        systemctl restart bot_trader > /dev/null
    endscript
}
```

3. Ative o serviço:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bot_trader
sudo systemctl start bot_trader
```

4. Verifique os logs:

```bash
journalctl -u bot_trader -f  # Logs do sistema
tail -f /var/log/bot_trader.log  # Logs detalhados do bot
```

##🛡️ Avisoo 
Este bot é para fins educacionais. Use com cautela em ambientes de produção e nunca arrisque valores que não pode perder.