
TOLERANCE_PERCENT = 0.005


def analyze_stock_day(day_data):
    """
    This is the Inference Engine.
    It applies the Rule-Set to a single day's data.
    'day_data' is a single row (a pandas Series) from the DataFrame.
    """
# Inference Engine and Knowledge Base which includes the ten rules we defined
    conclusions = []

    # --- Extract variables
    O = day_data['Open']
    H = day_data['High']
    L = day_data['Low']
    C = day_data['Close']
    V = day_data['Volume']
    Avg_V = day_data['Avg_Volume_50D']
    Change_Pct = day_data['Price_Change_Percent']
    Range_Pct = day_data['Day_Range_Percent']

    # --- Rule-Set 1: Intraday Price Action Rules ---

    # Rule 1: Bullish Close
    # "If the Close price is almost equal to the High price"
    if abs(C - H) <= (H * TOLERANCE_PERCENT):
        conclusions.append("Immense Closing Strength (Bullish Close)")

    # Rule 2: Bearish Close
    # "If the Close price is almost equal to the Low price"
    if abs(C - L) <= (L * TOLERANCE_PERCENT):
        conclusions.append("Immense Closing Weakness (Bearish Close)")

    # Rule 3: Strong Uptrend Day
    # "If Open is nearly equal to Low AND Close is nearly equal to High"
    if abs(O - L) <= (L * TOLERANCE_PERCENT) and abs(C - H) <= (H * TOLERANCE_PERCENT):
        conclusions.append("Perfect Upward Day (Strong Uptrend)")

    # Rule 4: Strong Downtrend Day
    # "If Open is nearly equal to High AND Close is nearly equal to Low"
    if abs(O - H) <= (H * TOLERANCE_PERCENT) and abs(C - L) <= (L * TOLERANCE_PERCENT):
        conclusions.append("Perfect Downward Day (Strong Downtrend)")

    # Rule 5: Consolidation/Indecision
    # "If the difference between High and Low is very small"
    # We define "very small" as less than 1% (you can change 1.0)
    if Range_Pct < 1.0:
        conclusions.append("Day of Consolidation/Indecision")

    # Rule 6: Strong Positive Jump
    # "If Close is significantly higher than Open (e.g., 5%)"
    if Change_Pct >= 5.0:
        conclusions.append("Strong Positive Jump (Major Positive News)")
    # Rule 7: Strong Negative Jump
    # If Close is significantly lower than Open (-5%)
    if Change_Pct <= -5.0:
        conclusions.append("Strong Negative Jump (Major Negative News)")

    # --- Rule-Set 2: Volume Rules ---

    # Rule 8: Stock Distribution
    # "If today's Volume is 150% higher than average AND negative close"
    # (150% higher = 2.5 * average)
    if V > (Avg_V * 2.5) and C < O:
        conclusions.append("Stock Distribution / Major Selling Pressure")

    # Rule 9: Stock Accumulation
    # "If today's Volume is 150% higher than average AND positive close"
    if V > (Avg_V * 2.5) and C > O:
        conclusions.append("Stock Accumulation / Major Buying Interest")

    # Rule 10: Suspicious/Unreliable Signal
    # "If Volume is very low (less than 50%) on a day with significant price change"
    if V < (Avg_V * 0.5) and abs(Change_Pct) > 3.0:
        conclusions.append("Suspicious / Unreliable Signal (Low Volume Move)")


    if not conclusions:
        # If no rules were triggered
        return ["No Specific Pattern Detected"]

    return conclusions