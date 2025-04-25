# Configurações de API
API_KEY = 'Sua chave API'
API_SECRET = 'Sua secret API'

#############################################
### CONFIGURAÇÕES GERAIS DO BOT ###
#############################################

# Pares e Timeframes
PARES_MONITORADOS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
INTERVALO = '5m'  # Pode ser: 1m, 5m, 15m, 1h, 4h, 1d
QUANTIDADE_CANDLES = 100  # Quantidade de candles para análise histórica

# Gerenciamento de Risco
TAKE_PROFIT_PCT = 0.015  # 1.5% de lucro alvo
STOP_LOSS_PCT = 0.01     # 1% de perda máxima
VALOR_OPERACAO_USD = 45  # Valor fixo por operação
TEMPO_MAXIMO_OPERACAO = 60 * 30  # 30 hora em segundos
VERIFICACAO_INTERVALO = 30  # Tempo entre análises (segundos)
VALOR_MINIMO_RESIDUAL = 6  # Ignorar saldos < $6

# Sistema de Pontuação
SCORE_MINIMO_ENTRADA = 65  # Score mínimo para entrada (0-100)

#############################################
### CONFIGURAÇÕES DE INDICADORES TÉCNICOS ###
#############################################

# RSI (Índice de Força Relativa)
RSI_PERIODO = 10

# MACD (Convergência/Divergência de Médias Móveis)
MACD_PERIODO_RAPIDO = 10  # Período rápido
MACD_PERIODO_LENTO = 26   # Período lento
MACD_PERIODO_SINAL = 9    # Período do sinal

# Médias Móveis Simples (SMA)
SMA_CURTA = 9   # SMA curta
SMA_LONGA = 21  # SMA longa

# Médias Móveis Exponenciais (EMA)
EMA_CURTA = 6   # EMA curta
EMA_LONGA = 18  # EMA longa

# Bandas de Bollinger
BB_PERIODO = 20  # Período das Bandas
BB_DESVIOS = 1.8   # Número de desvios padrão

# Oscilador Estocástico
STOCH_K_PERIODO = 14  # Período da linha K
STOCH_D_PERIODO = 3   # Período da linha D

# Volume
VOLUME_MULTIPLIER = 1.5  # Mínimo 1.5x a média de volume

#############################################
### CONFIGURAÇÕES DE LOG E MONITORAMENTO ###
#############################################

LOG_FILE = "/var/log/bot_trader.log"
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

#############################################
### CONFIGURAÇÕES AVANÇADAS ###
#############################################

# Horários Prioritários (UTC)
HORARIOS_OTIMOS = [0, 4, 8, 12, 16, 20]  # Horas de maior volume

# Filtro de Volatilidade Mínima
VOLATILIDADE_MINIMA = 0.01  # 1%

# Log Total
LOG_ANALISE_COMPLETA = False  # False para desativar

# Tentativas de ajuste
MAX_LOT_SIZE_RETRIES = 3  # Máximo de tentativas de ajuste

# Outras
EXPANSAO_TEMPO_PREJUIZO = 1.5  # Expande em 50% o tempo original
VOLATILIDADE_MAXIMA_SL = 0.03  # Stop Loss máximo de 3%
SALDO_MINIMO_USD = 6  # Valor mínimo em USD para considerar posição
