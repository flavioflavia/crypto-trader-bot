import time
import logging
import numpy as np
from logging.handlers import RotatingFileHandler
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
from tenacity import retry, stop_after_attempt, wait_exponential

class CryptoTrader:
    def __init__(self, config):
        """Inicializa o bot com persistência de operações"""
        self.config = config
        self.client = Client(config['API_KEY'], config['API_SECRET'])
        self.setup_logging()
        self.current_position = None
        
        # Verifica operações existentes ao iniciar
        self.check_existing_position()
        
        self.logger.info("╔════════════════════════════════════╗")
        self.logger.info("║  CRYPTO TRADER PRO - INICIALIZADO  ║")
        self.logger.info("╚════════════════════════════════════╝")

    def setup_logging(self):
        """Configuração do sistema de logs"""
        self.logger = logging.getLogger('CryptoTraderPro')
        self.logger.setLevel(self.config['LOG_LEVEL'])
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = RotatingFileHandler(
            self.config['LOG_FILE'],
            maxBytes=5*1024*1024,
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def calculate_indicators(self, klines):
        """Calcula todos os indicadores técnicos"""
        closes = np.array([float(k[4]) for k in klines])
        highs = np.array([float(k[2]) for k in klines])
        lows = np.array([float(k[3]) for k in klines])
        volumes = np.array([float(k[5]) for k in klines])
        opens = np.array([float(k[1]) for k in klines])
        
        indicators = {
            'price': closes[-1],
            'volume': volumes[-1]
        }
        
        # 1. RSI
        deltas = np.diff(closes)
        gains = deltas[deltas > 0]
        losses = -deltas[deltas < 0]
        avg_gain = np.mean(gains[:self.config['RSI_PERIODO']]) if len(gains) > 0 else 0
        avg_loss = np.mean(losses[:self.config['RSI_PERIODO']]) if len(losses) > 0 else 1
        rs = avg_gain / avg_loss
        indicators['rsi'] = 100 - (100 / (1 + rs))

        # 2. MACD
        ema12 = closes[-self.config['MACD_PERIODO_RAPIDO']:].mean()
        ema26 = closes[-self.config['MACD_PERIODO_LENTO']:].mean()
        indicators['macd'] = ema12 - ema26
        indicators['macd_signal'] = np.mean(closes[-self.config['MACD_PERIODO_SINAL']:])
        indicators['macd_hist'] = indicators['macd'] - indicators['macd_signal']

        # 3. Médias Móveis
        indicators['sma_short'] = np.mean(closes[-self.config['SMA_CURTA']:])
        indicators['sma_long'] = np.mean(closes[-self.config['SMA_LONGA']:])
        indicators['ema_short'] = closes[-self.config['EMA_CURTA']:].mean()
        indicators['ema_long'] = closes[-self.config['EMA_LONGA']:].mean()

        # 4. Bollinger Bands
        sma = indicators['sma_long']
        std = np.std(closes[-self.config['BB_PERIODO']:])
        indicators['bb_upper'] = sma + (std * self.config['BB_DESVIOS'])
        indicators['bb_lower'] = sma - (std * self.config['BB_DESVIOS'])
        indicators['bb_width'] = (indicators['bb_upper'] - indicators['bb_lower']) / sma

        # 5. Estocástico
        lowest_low = np.min(lows[-self.config['STOCH_K_PERIODO']:])
        highest_high = np.max(highs[-self.config['STOCH_K_PERIODO']:])
        indicators['stoch_k'] = 100 * ((closes[-1] - lowest_low) / (highest_high - lowest_low)) if (highest_high - lowest_low) != 0 else 0
        indicators['stoch_d'] = np.mean([indicators['stoch_k']] * self.config['STOCH_D_PERIODO'])

        # 6. Volume
        indicators['volume_avg'] = np.mean(volumes[-20:])
        indicators['volume_ratio'] = volumes[-1] / indicators['volume_avg']

        # 7. Padrões de Candles
        indicators['bullish'] = self.is_bullish_candle(opens[-1], closes[-1])
        indicators['engulfing'] = self.is_engulfing(opens, closes)
        
        return indicators

    def is_bullish_candle(self, open, close):
        return close > open

    def is_engulfing(self, opens, closes):
        if len(closes) < 3:
            return False
        return (closes[-2] < opens[-2] and  # Candle anterior baixista
                closes[-1] > opens[-1] and  # Candle atual altista
                closes[-1] > opens[-2] and  # Fechamento acima da abertura anterior
                opens[-1] < closes[-2])     # Abertura abaixo do fechamento anterior

    def calculate_entry_score(self, indicators):
        """Calcula score baseado em múltiplos fatores"""
        score = 0
        
        # 1. Tendência (30 pontos)
        if indicators['ema_short'] > indicators['ema_long']:
            score += 20
        if indicators['sma_short'] > indicators['sma_long']:
            score += 10
            
        # 2. Momentum (25 pontos)
        if indicators['rsi'] > 30 and indicators['rsi'] < 70:
            score += 15
        if indicators['macd_hist'] > 0:
            score += 10
            
        # 3. Volatilidade (20 pontos)
        if indicators['price'] > indicators['bb_lower'] and indicators['price'] < indicators['bb_upper']:
            score += 10
        if indicators['bb_width'] > 0.05:  # Bandas suficientemente largas
            score += 10
            
        # 4. Estocástico (15 pontos)
        if indicators['stoch_k'] > indicators['stoch_d'] and indicators['stoch_k'] < 80:
            score += 15
            
        # 5. Volume (10 pontos)
        if indicators['volume_ratio'] > self.config['VOLUME_MULTIPLIER']:
            score += 10
            
        # 6. Padrões de Candles (10 pontos)
        if indicators['bullish']:
            score += 5
        if indicators['engulfing']:
            score += 5
            
        return score

    def check_existing_position(self):
        """Verifica e recupera operações existentes ao iniciar, ignorando saldos pequenos"""
        for pair in self.config['PARES_MONITORADOS']:
            try:
                base_asset = pair.replace('USDT', '')
                balance = self.client.get_asset_balance(asset=base_asset)
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_balance = free_balance + locked_balance
            
                if total_balance > 0:
                    # Verifica valor do saldo em USDT
                    ticker = self.client.get_symbol_ticker(symbol=pair)
                    current_price = float(ticker['price'])
                    balance_value = total_balance * current_price
                
                    if balance_value < self.config.get('SALDO_MINIMO_USD', 6):  # Ignora saldos menores que $6
                        self.logger.warning(f"⚠️ SALDO INSIGNIFICANTE | {pair} | Valor: ${balance_value:.2f} | Ignorando...")
                    continue
                    
                    self.current_position = {
                        'pair': pair,
                        'entry_price': current_price,
                        'quantity': total_balance,
                        'opened_at': time.time() - self.config['TEMPO_MAXIMO_OPERACAO']/2,
                        'stop_loss': 0,
                        'take_profit': 0
                    }
                    self.recalculate_sl_tp()
                    self.logger.warning(f"⚠️ OPERAÇÃO EXISTENTE RECUPERADA | {pair} | Valor: ${balance_value:.2f}")
                    break
                
            except Exception as e:
                self.logger.error(f"Erro ao verificar posição em {pair}: {str(e)}")

    def recalculate_sl_tp(self):
        """Recalcula stop loss e take profit dinamicamente"""
        if not self.current_position:
            return
            
        pair = self.current_position['pair']
        try:
            klines = self.client.get_klines(
                symbol=pair,
                interval=self.config['INTERVALO'],
                limit=20
            )
            closes = np.array([float(k[4]) for k in klines])
            volatility = np.std(closes) / np.mean(closes)
            
            # Cálculo dinâmico com limites
            sl_multiplier = min(
                self.config['VOLATILIDADE_MAXIMA_SL'],
                max(self.config['STOP_LOSS_PCT'], volatility * 1.5)
            )
            tp_multiplier = sl_multiplier * 2  # Risk-reward 1:2
            
            self.current_position.update({
                'stop_loss': self.current_position['entry_price'] * (1 - sl_multiplier),
                'take_profit': self.current_position['entry_price'] * (1 + tp_multiplier)
            })
            
            self.logger.info(
                f"🔄 SL/TP RECALCULADOS | "
                f"SL: {sl_multiplier*100:.1f}% | "
                f"TP: {tp_multiplier*100:.1f}% | "
                f"Preço Entrada: {self.current_position['entry_price']:.4f}"
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao recalcular SL/TP: {str(e)}")

    def check_stop_loss_take_profit(self):
        """Gestão avançada de SL/TP com tempo expandido"""
        if not self.current_position:
            return
            
        pair = self.current_position['pair']
        try:
            ticker = self.client.get_symbol_ticker(symbol=pair)
            current_price = float(ticker['price'])
            entry_price = self.current_position['entry_price']
            profit_pct = (current_price - entry_price) / entry_price * 100
            elapsed = time.time() - self.current_position['opened_at']
            remaining_time = max(0, self.config['TEMPO_MAXIMO_OPERACAO'] - elapsed)
            
            is_profitable = current_price > entry_price
            
            # Verificação de tempo expirado
            if elapsed > self.config['TEMPO_MAXIMO_OPERACAO']:
                if is_profitable:
                    self.logger.warning(f"⏰ TEMPO EXPIRADO COM LUCRO: {profit_pct:.2f}% - VENDENDO")
                    self.execute_trade(pair, 'sell')
                else:
                    # Expande o tempo e ajusta SL
                    new_max_time = self.config['TEMPO_MAXIMO_OPERACAO'] * self.config['EXPANSAO_TEMPO_PREJUIZO']
                    self.current_position['opened_at'] = time.time() - (new_max_time * 0.8)
                    self.recalculate_sl_tp()
                    self.logger.warning(
                        f"⏰ TEMPO EXPANDIDO | "
                        f"Prejuízo: {abs(profit_pct):.2f}% | "
                        f"Novo Limite: {new_max_time/60:.1f} min"
                    )
                return
                
            # Verificação normal de SL/TP
            if current_price <= self.current_position['stop_loss']:
                self.logger.warning(f"🛑 STOP LOSS ATINGIDO: {profit_pct:.2f}%")
                self.execute_trade(pair, 'sell')
            elif current_price >= self.current_position['take_profit']:
                self.logger.warning(f"🎯 TAKE PROFIT ATINGIDO: {profit_pct:.2f}%")
                self.execute_trade(pair, 'sell')
            else:
                self.logger.info(
                    f"📊 POSIÇÃO ATIVA | {pair} | "
                    f"Lucro: {profit_pct:.2f}% | "
                    f"Tempo Restante: {remaining_time/60:.1f} min"
                )
                
        except Exception as e:
            self.logger.error(f"ERRO AO VERIFICAR SL/TP: {str(e)}")

    def analyze_pair(self, pair):
        """Analisa um par usando múltiplos indicadores"""
        try:
            klines = self.client.get_klines(
                symbol=pair,
                interval=self.config['INTERVALO'],
                limit=self.config['QUANTIDADE_CANDLES']
            )
            
            if len(klines) < self.config['QUANTIDADE_CANDLES']:
                return None
                
            indicators = self.calculate_indicators(klines)
            score = self.calculate_entry_score(indicators)
            
            # Condições de entrada
            entry_conditions = (
                score >= self.config['SCORE_MINIMO_ENTRADA'] and
                indicators['volume_ratio'] > self.config['VOLUME_MULTIPLIER'] and
                not self.current_position
            )
            
            # Condições de saída
            exit_conditions = (
                self.current_position and 
                self.current_position['pair'] == pair and
                (indicators['price'] >= self.current_position['take_profit'] or
                 indicators['price'] <= self.current_position['stop_loss'] or
                 time.time() - self.current_position['opened_at'] > self.config['TEMPO_MAXIMO_OPERACAO'])
            )
            
            if entry_conditions:
                self.logger.info(f"📈 {pair} | Score: {score}/{self.config['SCORE_MINIMO_ENTRADA']} | RSI: {indicators['rsi']:.1f} | MACD: {indicators['macd_hist']:.4f}")
                return 'buy'
            elif exit_conditions:
                return 'sell'
                
        except Exception as e:
            self.logger.error(f"Erro ao analisar {pair}: {str(e)}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def execute_trade(self, pair, side):
        """Execução robusta com tratamento de LOT_SIZE"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=pair)
            current_price = float(ticker['price'])
            
            if side == 'buy':
                # Calcula quantidade
                quantity = round(self.config['VALOR_OPERACAO_USD'] / current_price, 8)
                
                # Verifica limites do par
                symbol_info = self.client.get_symbol_info(pair)
                filters = {f['filterType']: f for f in symbol_info['filters']}
                step_size = float(filters['LOT_SIZE']['stepSize'])
                min_qty = float(filters['LOT_SIZE']['minQty'])
                
                # Ajusta quantidade
                quantity = round(quantity - (quantity % step_size), 8)
                quantity = max(quantity, min_qty)
                
                # Executa ordem
                order = self.client.create_order(
                    symbol=pair,
                    side=SIDE_BUY,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity
                )
                
                # Armazena posição
                self.current_position = {
                    'pair': pair,
                    'entry_price': current_price,
                    'quantity': quantity,
                    'opened_at': time.time(),
                    'stop_loss': current_price * (1 - self.config['STOP_LOSS_PCT']),
                    'take_profit': current_price * (1 + self.config['TAKE_PROFIT_PCT'])
                }
                
                self.logger.info(f"✅ COMPRA {pair} | {quantity} @ {current_price:.4f} | SL: {self.current_position['stop_loss']:.4f} | TP: {self.current_position['take_profit']:.4f}")
                
            elif side == 'sell':
                if not self.current_position or self.current_position['pair'] != pair:
                    return
                    
                # Obtém regras do par
                symbol_info = self.client.get_symbol_info(pair)
                lot_size = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
                step_size = float(lot_size['stepSize'])
                min_qty = float(lot_size['minQty'])
                
                # Obtém e ajusta quantidade
                balance = self.client.get_asset_balance(asset=pair.replace('USDT', ''))
                available = float(balance['free'])
                quantity = (available // step_size) * step_size
                quantity = round(quantity, 8)
                
                if quantity < min_qty:
                    self.logger.warning(f"⚠️ SALDO RESIDUAL | Qtd: {quantity} < Mín: {min_qty}")
                    self.current_position = None
                    return
                    
                # Executa venda
                order = self.client.create_order(
                    symbol=pair,
                    side=SIDE_SELL,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity
                )
                
                # Registra resultado
                entry_price = self.current_position['entry_price']
                profit = (current_price - entry_price) * quantity
                profit_pct = (profit / (entry_price * quantity)) * 100
                
                self.logger.info(
                    f"✅ VENDA CONCLUÍDA | {pair} | "
                    f"Qtd: {quantity} | "
                    f"Lucro: {profit:.4f} USDT ({profit_pct:.2f}%)"
                )
                
                self.current_position = None
                
        except BinanceAPIException as e:
            if "LOT_SIZE" in str(e):
                self.adjust_and_retry_sell(pair)
            else:
                self.logger.error(f"API ERROR: {e.status_code} - {e.message}")
        except Exception as e:
            self.logger.error(f"ERRO NA ORDEM: {str(e)}")
            raise

    def adjust_and_retry_sell(self, pair):
        """Ajusta quantidade e tenta vender novamente"""
        try:
            symbol_info = self.client.get_symbol_info(pair)
            lot_size = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
            step_size = float(lot_size['stepSize'])
            min_qty = float(lot_size['minQty'])
            
            balance = self.client.get_asset_balance(asset=pair.replace('USDT', ''))
            available = float(balance['free'])
            adjusted_qty = (available // step_size) * step_size
            
            if adjusted_qty >= min_qty:
                self.logger.warning(f"♻️ AJUSTANDO QTD: {adjusted_qty} (Original: {available})")
                self.execute_trade(pair, 'sell')
            else:
                self.logger.error(f"❌ QTD AJUSTADA INSUFICIENTE: {adjusted_qty} < {min_qty}")
                self.current_position = None
                
        except Exception as e:
            self.logger.error(f"FALHA NO AJUSTE: {str(e)}")
            self.current_position = None

    def run(self):
        """Loop principal com gestão de operações contínuas"""
        self.logger.info("🚀 INICIANDO OPERAÇÕES")
        while True:
            try:
                # 1. Verifica SL/TP e tempo
                self.check_stop_loss_take_profit()
                
                # 2. Se posição aberta, aguarda
                if self.current_position:
                    time.sleep(self.config['VERIFICACAO_INTERVALO'])
                    continue
                    
                # 3. Busca novas oportunidades
                for pair in self.config['PARES_MONITORADOS']:
                    signal = self.analyze_pair(pair)
                    if signal == 'buy':
                        self.execute_trade(pair, 'buy')
                        break
                        
                time.sleep(self.config['VERIFICACAO_INTERVALO'])
                
            except KeyboardInterrupt:
                self.logger.info("🛑 ENCERRADO POR USUÁRIO")
                break
            except Exception as e:
                self.logger.error(f"ERRO NO LOOP: {str(e)}")
                time.sleep(60)

    def start(self):
        """Interface para iniciar o bot"""
        self.run()