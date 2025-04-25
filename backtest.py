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

                    future_klines = klines[i:i+12]  # até 1 hora depois
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
                    else:
                        last_price = float(future_klines[-1][4])
                        lucro = last_price - entry_price
                        self.resultados[pair].append((close_time, lucro))
                        self.resultados['total'].append((close_time, lucro))

    def plot_resultados(self):
        for pair in self.config['PARES_MONITORADOS']:
            dados = self.resultados.get(pair, [])
            if not dados:
                print(f"⚠️ Sem dados de lucro para {pair}")
                continue

            df = pd.DataFrame(dados, columns=['timestamp', 'lucro'])
            df['data'] = pd.to_datetime(df['timestamp'], unit='s')
            df['lucro_acumulado'] = df['lucro'].cumsum()
            lucro_total = df['lucro_acumulado'].iloc[-1]
            entradas = len(df)

            # Gera gráfico
            plt.figure(figsize=(10, 6))
            plt.plot(df['data'], df['lucro_acumulado'], label=f'{pair}')
            plt.title(f'{pair} - Lucro Acumulado (30 dias)\n'
                      f'Lucro total: {lucro_total:.4f} USDT | Entradas: {entradas}')
            plt.xlabel('Data')
            plt.ylabel('Lucro (USDT)')
            plt.grid(True)
            plt.legend()
            plt.tight_layout()

            # Salva gráfico
            nome_arquivo = f'lucro_{pair}.jpg'
            plt.savefig(nome_arquivo)
            plt.close()

            print(f"📈 Gráfico salvo: {nome_arquivo}")
    def gerar_relatorio_final(self):
        relatorio = []
        lucro_total = 0
        entradas_total = 0

        relatorio.append("🔎 RELATÓRIO FINAL BACKTEST (últimos 30 dias)\n")
        relatorio.append("="*50 + "\n")

        for pair in self.config['PARES_MONITORADOS']:
            dados = self.resultados.get(pair, [])
            if not dados:
                continue

            df = pd.DataFrame(dados, columns=['timestamp', 'lucro'])
            df['data'] = pd.to_datetime(df['timestamp'], unit='s')
            df['lucro_acumulado'] = df['lucro'].cumsum()

            lucro_par = df['lucro_acumulado'].iloc[-1]
            entradas_par = len(df)

            relatorio.append(f"{pair}:")
            relatorio.append(f"  Entradas: {entradas_par}")
            relatorio.append(f"  Lucro/Prejuízo: {lucro_par:.4f} USDT\n")

            lucro_total += lucro_par
            entradas_total += entradas_par

        relatorio.append("="*50)
        relatorio.append(f"Total de Entradas: {entradas_total}")
        relatorio.append(f"Lucro/Prejuízo Final: {lucro_total:.4f} USDT")
        relatorio.append("="*50)

        # Salva no arquivo
        with open("relatorio_backtest.txt", "w") as f:
            f.write("\n".join(relatorio))

        print("📄 Relatório final salvo: relatorio_backtest.txt")

if __name__ == "__main__":
    print("🚀 Iniciando Backtest dos últimos 30 dias")

    config = {
        'API_KEY': API_KEY,
        'API_SECRET': API_SECRET,
        'PARES_MONITORADOS': PARES_MONITORADOS,
        'INTERVALO': INTERVALO,
        'QUANTIDADE_CANDLES': 150,        # <- AUMENTADO
        'TAKE_PROFIT_PCT': TAKE_PROFIT_PCT,
        'STOP_LOSS_PCT': STOP_LOSS_PCT,
        'VALOR_OPERACAO_USD': VALOR_OPERACAO_USD,
        'SCORE_MINIMO_ENTRADA': 60,        # <- REDUZIDO
        'VOLUME_MULTIPLIER': 1.2,          # <- REDUZIDO
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
    backtester.gerar_relatorio_final()
    