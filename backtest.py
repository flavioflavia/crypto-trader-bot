import time
import datetime
import matplotlib.pyplot as plt
import pandas as pd
from binance.client import Client
from config import *
from bot_trader import CryptoTrader

class BacktestTrader(CryptoTrader):
    def __init__(self, config):
        super().__init__(config)
        self.resultados = {pair: [] for pair in config['PARES_MONITORADOS']}
        self.resultados['total'] = []

    def start_backtest(self):
        dias = 30
        intervalo = self.config['INTERVALO']
        minutos_por_candle = int(intervalo.replace('m', ''))
        total_candles = int((60 * 24 * dias) / minutos_por_candle)

        for pair in self.config['PARES_MONITORADOS']:
            print(f"\n🔍 Backtest em: {pair}")
            klines = self.client.get_klines(
                symbol=pair,
                interval=intervalo,
                limit=total_candles
            )

            for i in range(self.config['QUANTIDADE_CANDLES'], len(klines)):
                subset = klines[i - self.config['QUANTIDADE_CANDLES']:i]
                indicadores = self.calculate_indicators(subset)
                score = self.calculate_entry_score(indicadores)

                entry_conditions = (
                    score >= self.config['SCORE_MINIMO_ENTRADA'] and
                    indicadores['volume_ratio'] > self.config['VOLUME_MULTIPLIER']
                )

                if entry_conditions:
                    entry_price = indicadores['price']
                    stop_loss = entry_price * (1 - self.config['STOP_LOSS_PCT'])
                    take_profit = entry_price * (1 + self.config['TAKE_PROFIT_PCT'])

                    # Simula movimento futuro
                    future_klines = klines[i:i+12]  # 1 hora à frente
                    for future_k in future_klines:
                        high = float(future_k[2])
                        low = float(future_k[3])
                        close_time = future_k[6] // 1000

                        if low <= stop_loss:
                            lucro = stop_loss - entry_price
                            self.resultados[pair].append((close_time, lucro))
                            self.resultados['total'].append((close_time, lucro))
                            break
                        elif high >= take_profit:
                            lucro = take_profit - entry_price
                            self.resultados[pair].append((close_time, lucro))
                            self.resultados['total'].append((close_time, lucro))
                            break
                    # Se não atingiu SL ou TP
                    else:
                        last_price = float(future_klines[-1][4])
                        lucro = last_price - entry_price
                        self.resultados[pair].append((close_time, lucro))
                        self.resultados['total'].append((close_time, lucro))

    def plot_resultados(self):
        df_total = pd.DataFrame(self.resultados['total'], columns=['timestamp', 'lucro'])
        df_total['data'] = pd.to_datetime(df_total['timestamp'], unit='s')
        df_total['lucro_acumulado'] = df_total['lucro'].cumsum()

        plt.figure(figsize=(10, 6))
        plt.plot(df_total['data'], df_total['lucro_acumulado'], label='Lucro Total')
        plt.title('Backtest - Lucro Acumulado (30 dias)')
        plt.xlabel('Data')
        plt.ylabel('Lucro (USDT)')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    print("🚀 Iniciando Backtest dos últimos 30 dias")

    config = {
        'API_KEY': API_KEY,
        'API_SECRET': API_SECRET,
        'PARES_MONITORADOS': PARES_MONITORADOS,
        'INTERVALO': INTERVALO,
        'QUANTIDADE_CANDLES': QUANTIDADE_CANDLES,
        'TAKE_PROFIT_PCT': TAKE_PROFIT_PCT,
        'STOP_LOSS_PCT': STOP_LOSS_PCT,
        'VALOR_OPERACAO_USD': VALOR_OPERACAO_USD,
        'SCORE_MINIMO_ENTRADA': 65,            # <- AJUSTE AQUI
        'VOLUME_MULTIPLIER': 1.5,              # <- AJUSTE AQUI
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
        'VOLUME_MULTIPLIER': 1.5,
        'LOG_FILE': '/tmp/backtest.log',
        'LOG_LEVEL': 'ERROR',
        'TEMPO_MAXIMO_OPERACAO': 60 * 60,
        'EXPANSAO_TEMPO_PREJUIZO': EXPANSAO_TEMPO_PREJUIZO,
        'VOLATILIDADE_MAXIMA_SL': VOLATILIDADE_MAXIMA_SL,
        'SALDO_MINIMO_USD': SALDO_MINIMO_USD,
        'VALOR_MINIMO_RESIDUAL': VALOR_MINIMO_RESIDUAL
    }

    backtester = BacktestTrader(config)
    backtester.start_backtest()
    backtester.plot_resultados()
