#!/usr/bin/env python3
from bot_trader import CryptoTrader
from config import *
import signal
import sys
import logging

def signal_handler(sig, frame):
    print("\n🔴 Recebido sinal de interrupção - Encerrando...")
    sys.exit(0)

def load_config():
    """Carrega todas as configurações do config.py"""
    return {
        'API_KEY': API_KEY,
        'API_SECRET': API_SECRET,
        'PARES_MONITORADOS': PARES_MONITORADOS,
        'INTERVALO': INTERVALO,
        'QUANTIDADE_CANDLES': QUANTIDADE_CANDLES,
        'TAKE_PROFIT_PCT': TAKE_PROFIT_PCT,
        'STOP_LOSS_PCT': STOP_LOSS_PCT,
        'VALOR_OPERACAO_USD': VALOR_OPERACAO_USD,
        'TEMPO_MAXIMO_OPERACAO': TEMPO_MAXIMO_OPERACAO,
        'VERIFICACAO_INTERVALO': VERIFICACAO_INTERVALO,
        'VALOR_MINIMO_RESIDUAL': VALOR_MINIMO_RESIDUAL,
        'SCORE_MINIMO_ENTRADA': SCORE_MINIMO_ENTRADA,
        'LOG_FILE': LOG_FILE,
        'LOG_LEVEL': LOG_LEVEL,
        'EXPANSAO_TEMPO_PREJUIZO': getattr(sys.modules[__name__], 'EXPANSAO_TEMPO_PREJUIZO', 1.5),
        'VOLATILIDADE_MAXIMA_SL': getattr(sys.modules[__name__], 'VOLATILIDADE_MAXIMA_SL', 0.05),
        'SALDO_MINIMO_USD': SALDO_MINIMO_USD,
        # Indicadores técnicos
        'RSI_PERIODO': RSI_PERIODO,
        'MACD_PERIODO_RAPIDO': MACD_PERIODO_RAPIDO,
        'MACD_PERIODO_LENTO': MACD_PERIODO_LENTO,
        'MACD_PERIODO_SINAL': MACD_PERIODO_SINAL,
        'SMA_CURTA': SMA_CURTA,
        'SMA_LONGA': SMA_LONGA,
        'EMA_CURTA': EMA_CURTA,
        'EMA_LONGA': EMA_LONGA,
        'BB_PERIODO': BB_PERIODO,
        'BB_DESVIOS': BB_DESVIOS,
        'STOCH_K_PERIODO': STOCH_K_PERIODO,
        'STOCH_D_PERIODO': STOCH_D_PERIODO,
        'VOLUME_MULTIPLIER': VOLUME_MULTIPLIER
    }

def main():
    # Configura tratadores de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Banner de inicialização
    print("""
    ╔══════════════════════════════════════════╗
    ║   CRYPTO TRADER PRO - MULTI-INDICADORES  ║
    ║                                          ║
    ║   • RSI ({})      • MACD ({},{},{})      ║
    ║   • SMA ({},{})   • EMA ({},{})          ║
    ║   • Bollinger Bands ({},{})              ║
    ║   • Estocástico ({},{})                  ║
    ╚══════════════════════════════════════════╝
    """.format(
        RSI_PERIODO,
        MACD_PERIODO_RAPIDO, MACD_PERIODO_LENTO, MACD_PERIODO_SINAL,
        SMA_CURTA, SMA_LONGA,
        EMA_CURTA, EMA_LONGA,
        BB_PERIODO, BB_DESVIOS,
        STOCH_K_PERIODO, STOCH_D_PERIODO
    ))

    try:
        # Carrega configurações
        config = load_config()
        
        # Inicializa o bot
        bot = CryptoTrader(config)
        
        # Registro de inicialização
        logging.basicConfig(level=config['LOG_LEVEL'])
        logging.info("Iniciando bot com recuperação ativada")
        logging.info(f"Pares: {config['PARES_MONITORADOS']}")
        logging.info(f"Tempo máximo por operação: {config['TEMPO_MAXIMO_OPERACAO']/60} minutos")
        logging.info("Iniciando bot com os seguintes pares:")
        for par in PARES_MONITORADOS:
            logging.info(f"   - {par} ({INTERVALO})")
        
        # Inicia o loop principal
        bot.start()
        
    except Exception as e:
        logging.critical(f"Falha na inicialização: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    