
from AlgoAPI import AlgoAPIUtil, AlgoAPI_Backtest
from collections import deque
import uuid

class AlgoEvent:
    def __init__(self):
        self.myinstrument = []
        self.price_history = {}       # {instrument: deque of (timestamp, close)}
        self.pattern_points = {}      # {instrument: list of ("High"/"Low", timestamp, price)}
        self.active_orders = {}       # {orderRef: instrument}
        self.tracked_positions = {}   # {instrument: list of (tradeID, filled_buy_price)}
        self.moving_averages = {}     # {instrument: 9-day moving average}

    def start(self, mEvt):
        self.evt = AlgoAPI_Backtest.AlgoEvtHandler(self, mEvt)
        self.myinstrument = mEvt["subscribeList"]
        for instrument in self.myinstrument:
            self.price_history[instrument] = deque(maxlen=180)
            self.pattern_points[instrument] = []
            self.tracked_positions[instrument] = []
            self.moving_averages[instrument] = None
        self.evt.start()

    def on_bulkdatafeed(self, isSync, bd, ab):
        for instrument in self.myinstrument:
            if instrument not in bd:
                continue

            data_obj = bd[instrument]
            ts = data_obj['timestamp']
            close = data_obj.get('close', data_obj.get('lastPrice'))

            if ts is None or close is None:
                continue

            self.price_history[instrument].append((ts, close))

            # Calculate 9-day moving average
            if len(self.price_history[instrument]) >= 9:
                closes = [p[1] for p in list(self.price_history[instrument])[-9:]]
                self.moving_averages[instrument] = sum(closes) / 9

        for instrument in self.myinstrument:
            if len(self.price_history[instrument]) >= 3:
                self.analyze_prices(instrument)
            else:
                self.evt.consoleLog(f"[SKIP] {instrument}: only {len(self.price_history[instrument])} data points")

    def analyze_prices(self, instrument):
        data = list(self.price_history[instrument])
        result = []

        for i in range(1, len(data) - 1):
            prev = data[i - 1]
            curr = data[i]
            nxt = data[i + 1]

            if prev[1] < curr[1] and nxt[1] < curr[1]:
                result.append(("High", curr[0], curr[1]))
            elif prev[1] > curr[1] and nxt[1] > curr[1]:
                result.append(("Low", curr[0], curr[1]))

        self.pattern_points[instrument] = result

        #self.evt.consoleLog(f"[{instrument}] Pattern check on latest {len(data)} closes:")
        #for label, ts, price in result:
        #    self.evt.consoleLog(f"  {label} Point - Time: {ts}, Close: {price:.2f}")

    def on_marketdatafeed(self, md, ab):
        nav = ab['availableBalance']


        instrument = md.instrument
        current_price = getattr(md, 'close', getattr(md, 'lastPrice', None))
        if current_price is None or instrument not in self.myinstrument:
            return

        points = self.pattern_points.get(instrument, [])
        highs = [p for p in points if p[0] == "High"]
        lows = [p for p in points if p[0] == "Low"]

        if len(highs) < 2 or len(lows) < 2:
            return

        H1_label, H1_ts, H1_price = highs[-1]
        H2_label, H2_ts, H2_price = highs[-2]
        L1_label, L1_ts, L1_price = lows[-1]
        L2_label, L2_ts, L2_price = lows[-2]

        ma9 = self.moving_averages.get(instrument, None)
        if ma9 is None:
            return

        # Buy condition
        if (H1_price > H2_price and
            L1_price > L2_price and
            H1_ts > H2_ts and
            L1_ts > L2_ts and
            current_price < H1_price * 1.02 and
            current_price > ma9):

            limit_price = round(current_price, 2)
            volume = int((0.20 * nav) // limit_price)
            if volume <= 0:
                return

            order = AlgoAPIUtil.OrderObject()
            order.instrument = instrument
            order.openclose = 'open'
            order.buysell = 1
            order.ordertype = 1  # Limit Order
            order.price = limit_price
            order.volume = volume
            order.holdtime = 21600  # 6 hours
            orderRef = str(uuid.uuid4())
            order.orderRef = orderRef

            self.active_orders[orderRef] = instrument
            self.evt.sendOrder(order)
            self.evt.consoleLog(f"[BUY SENT] {instrument} at {limit_price:.2f} (vol={volume}), MA(9)={ma9:.2f}, Ref={orderRef}")
           

        # Sell condition: Close all positions if current price < MA(9)
        current_trades = self.tracked_positions[instrument]
        remaining_trades = []

        for trade_id, buy_price in current_trades:
            if current_price  < ma9:
                order = AlgoAPIUtil.OrderObject()
                order.tradeID = trade_id
                order.openclose = 'close'
                self.evt.sendOrder(order)
                self.evt.consoleLog(f" Min Tick { md.minTick} Bid Price: {md.bidPrice} Ask Price: {md.askPrice}  Bid Size {md.bidSize} Ask Size: {md.askSize} Bid Order Book: {md.bidOrderBook} Ask Order Book: {md.askOrderBook}")
                self.evt.consoleLog(f"[SELL] {instrument} - Closed tradeID={trade_id} as price {current_price:.2f} < MA(9) {ma9:.2f}")
            else:
                remaining_trades.append((trade_id, buy_price))

        self.tracked_positions[instrument] = remaining_trades

    def on_orderfeed(self, of):
        ref = of.orderRef
        if of.status == 'success' and of.openclose == 'open':
            instrument = of.instrument
            trade_id = of.tradeID
            filled_price = of.fill_price
            if ref in self.active_orders:
                self.tracked_positions[instrument].append((trade_id, filled_price))
                self.evt.consoleLog(f"[ORDER FILLED] {instrument} TradeID={trade_id}, Filled Buy={filled_price:.2f}")
                del self.active_orders[ref]

    def on_newsdatafeed(self, nd): 
        pass
    def on_weatherdatafeed(self, wd): 
        pass
    def on_econsdatafeed(self, ed): 
        pass
    def on_corpAnnouncement(self, ca): 
        pass
    def on_dailyPLfeed(self, pl): 
        pass
    def on_openPositionfeed(self, op, oo, uo): 
        pass

