# 📈 Pattern-Based Trend Confirmation with 9-Day Moving Average Strategy

## 📖 Strategy Description

This trading strategy identifies **bullish trend patterns** using swing highs/lows and confirms them with a **9-day moving average (MA9)** filter. It executes trades only when both **price action** and **trend confirmation** align.

---

### 🔹 Step 1 – Data Collection & Moving Average Calculation

* The strategy maintains a rolling window of recent closing prices (`deque`).
* The **9-day simple moving average (MA9)** is computed as:

$$
MA(9) = \frac{\sum_{i=1}^{9} Price_i}{9}
$$

This moving average is used to confirm upward momentum before entering trades.

---

### 🔹 Step 2 – Swing High/Low Detection

* A **High point** is detected if the current price is greater than its immediate neighbors.
* A **Low point** is detected if the current price is lower than its immediate neighbors.
* These swing points are stored and continuously updated for each instrument.

---

### 🔹 Step 3 – Bullish Pattern Recognition

A bullish pattern is identified if:

* The most recent **High (H1)** > previous High (H2).
* The most recent **Low (L1)** > previous Low (L2).

This structure of **higher highs and higher lows** indicates a classic bullish trend.

---

### 🔹 Step 4 – Buy Condition

A **Buy Order** is placed when:

* Current Price < H1 × 1.02 (ensures price is near but not too far above recent high).
* Current Price > MA(9) (trend confirmation).

💰 **Position sizing:** 20% of available balance is allocated.
🕒 **Order type:** Limit Buy, with a 6-hour hold time.

---

### 🔹 Step 5 – Sell Condition (Exit Strategy)

* For each open position, if **current price < MA(9)** → Close the position immediately.
* This prevents holding during trend reversals.

---

### 🔹 Step 6 – Order Tracking

* Each order is assigned a **unique reference** (`uuid`).
* Successfully filled buy orders are tracked.
* Sell orders are triggered only on open tracked positions.

---

## 📊 Trading Interpretation

* **Entry Signal:** Bullish pattern (HH/HL) + price above MA(9).
* **Exit Signal:** Price closes below MA(9).
* **Strengths:**

  * Filters false signals by combining structure + moving average.
  * Maintains disciplined risk management.
* **Risk Control:** Caps exposure at 20% of available balance per trade.

---

## 🛠 Libraries Used

* **AlgoAPI (AlgoAPIUtil, AlgoAPI\_Backtest)** – Trading framework for event handling, execution, and backtesting.
* **collections.deque** – Efficient rolling window for price history.
* **uuid** – Unique order references for tracking trades.

---


