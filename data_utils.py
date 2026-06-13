import pandas as pd
import os
def load_and_prepare_data(ticker, data_folder_path):
    """
    Loads and prepares the data for a single specified ticker
    from the main data folder.
    """

# Data cleaning, to ensure it is error-free and dates are formatted correctly.
    file_name = f"{ticker}.csv"
    file_path = os.path.join(data_folder_path, file_name)

    try:
        # Read the specific CSV file
        df = pd.read_csv(file_path)

        # Check for required columns
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: The file {file_path} is missing required columns.")
            print(f"It must contain: {required_cols}")
            return None

        # Convert 'Date' column to datetime objects
        df['Date'] = pd.to_datetime(df['Date'])

        # Sort by Date
        df.sort_values(by='Date', inplace=True)

# Feature engineering, where it performs complex calculations
        # Calculate 50-day moving average for Volume (for Rule-Set 2)
        df['Avg_Volume_50D'] = df['Volume'].rolling(window=50, min_periods=1).mean()

        # Calculate daily price change percentage (for Rule-Set 1)
        # (Close - Open) / Open
        df['Price_Change_Percent'] = (df['Close'] - df['Open']) / df['Open'] * 100

        # Calculate daily price range percentage (for Rule-Set 1)
        # (High - Low) / Open
        df['Day_Range_Percent'] = (df['High'] - df['Low']) / df['Open'] * 100

        print(f"Successfully loaded and prepared data for {ticker}.")
        return df

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading {ticker}: {e}")
        return None