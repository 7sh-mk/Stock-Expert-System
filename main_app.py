import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
import os
from collections import Counter
from PIL import Image, ImageTk

# Matplotlib for comparison chart
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from data_utils import load_and_prepare_data
from expert_system import analyze_stock_day

# --- Global Variables
try:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder_path = os.path.join(base_dir, "Stock_Data")
    BACKGROUND_IMAGE_PATH = os.path.join(base_dir, "background1.png")
except NameError:
    data_folder_path = os.path.join(os.getcwd(), "Stock_Data")
    BACKGROUND_IMAGE_PATH = os.path.join(os.getcwd(), "background1.png")

data_cache = {}
chart_data = {"A": None, "B": None}
all_ticker_list = None

# --- Explanations Dictionary ---

PATTERN_EXPLANATIONS = {
    "Immense Closing Strength (Bullish Close)": "Buyers controlled the market until the closing bell",
    "Immense Closing Weakness (Bearish Close)": "Sellers controlled the market until the closing bell",
    "Perfect Upward Day (Strong Uptrend)": "The price rose consistently throughout the entire day",
    "Perfect Downward Day (Strong Downtrend)": "The price dropped consistently throughout the entire day",
    "Day of Consolidation/Indecision": "The market is waiting for a catalyst; narrow trading range",
    "Strong Positive Jump (Major Positive News)": "Major positive news triggered a significant price increase",
    "Strong Negative Jump (Major Negative News)": "Major negative news triggered a significant price drop",
    "Stock Distribution / Major Selling Pressure": "Massive volume on a down day, indicating institutions are selling",
    "Stock Accumulation / Major Buying Interest": "Massive volume on an up day, indicating institutions are buying",
    "Suspicious / Unreliable Signal (Low Volume Move)": "Significant price movement unsupported by volume (low reliability)",
    "No Specific Pattern Detected": "No distinct price or volume anomaly occurred during this period"
}


# Function to run analysis for ONE stock
def analyze_single_ticker(ticker_str, num_days):
    """
    Loads, analyzes, and summarizes a single ticker.
    Returns the full summary text and the data for charting.
    """

    current_df = None
    if ticker_str in data_cache:
        current_df = data_cache[ticker_str]
    else:
        current_df = load_and_prepare_data(ticker_str, data_folder_path)
        if current_df is None:
            return f"Error: Could not load data for {ticker_str}.", None
        data_cache[ticker_str] = current_df

    if current_df.shape[0] < num_days:
        num_days = current_df.shape[0]
    period_df = current_df.iloc[-num_days:]

    all_conclusions = []
    for index, day_data in period_df.iterrows():
        results = analyze_stock_day(day_data)
        all_conclusions.extend(results)

    conclusion_counts_full = Counter(all_conclusions)
    dominant_counts = conclusion_counts_full.copy()
    if 'No Specific Pattern Detected' in dominant_counts:
        del dominant_counts['No Specific Pattern Detected']

    summary_conclusion = dominant_counts.most_common(1)[0][0] if dominant_counts else "No Specific Pattern Detected"

    # Get the explanation from our dictionary
    explanation_text = PATTERN_EXPLANATIONS.get(summary_conclusion, "Analysis complete.")

    report_lines = []
    report_lines.append(f"--- Summary for {ticker_str} ---\n")
    report_lines.append(f"Dominant Pattern:\n• {summary_conclusion}\n\n")
    report_lines.append(f"explanation the main of Dominant Pattern:\n|| {explanation_text} ||\n\n ")

    report_lines.append("Breakdown:\n")

    price_action_rules = [
        "Immense Closing Strength (Bullish Close)", "Immense Closing Weakness (Bearish Close)",
        "Perfect Upward Day (Strong Uptrend)", "Perfect Downward Day (Strong Downtrend)",
        "Day of Consolidation/Indecision", "Strong Positive Jump (Major Positive News)",
        "Strong Negative Jump (Major Negative News)"
    ]
    volume_rules = [
        "Stock Distribution / Major Selling Pressure", "Stock Accumulation / Major Buying Interest",
        "Suspicious / Unreliable Signal (Low Volume Move)"
    ]

    report_lines.append("\nPrice Action Signals:\n")
    found = any(conclusion_counts_full.get(r, 0) > 0 for r in price_action_rules)
    for rule in price_action_rules:
        if (count := conclusion_counts_full.get(rule, 0)) > 0: report_lines.append(f"  • {rule}: {count}\n")
    if not found: report_lines.append("  (No price signals)\n")

    report_lines.append("\nVolume-Based Signals:\n")
    found = any(conclusion_counts_full.get(r, 0) > 0 for r in volume_rules)
    for rule in volume_rules:
        if (count := conclusion_counts_full.get(rule, 0)) > 0: report_lines.append(f"  • {rule}: {count}\n")
    if not found: report_lines.append("  (No volume signals)\n")

    report_lines.append("\nNeutral Days:\n")
    report_lines.append(f"  • No Specific Pattern: {conclusion_counts_full.get('No Specific Pattern Detected', 0)}\n")

    return "".join(report_lines), period_df


# --- Charting Function handles 1 or 2 Stock
def open_chart_window():
    global chart_data

    ticker_A = ticker_entry_A.get().upper()
    ticker_B = ticker_entry_B.get().upper()
    period = period_var.get()

    if chart_data["A"] is None and chart_data["B"] is None:
        messagebox.showwarning("No Data", "Please run an analysis first.")
        return

    chart_window = tk.Toplevel(root)
    chart_window.title(f"Comparison Chart ({period})")
    chart_window.geometry("800x600")

    fig, ax = plt.subplots(figsize=(10, 5), dpi=100)

    if chart_data["A"] is not None:
        ax.plot(chart_data["A"]['Date'], chart_data["A"]['Close'], label=f'{ticker_A} Close Price')

    if chart_data["B"] is not None:
        ax.plot(chart_data["B"]['Date'], chart_data["B"]['Close'], label=f'{ticker_B} Close Price', linestyle='--')

    ax.set_title(f"Comparison: {ticker_A} vs. {ticker_B} ({period})")
    ax.set_ylabel("Price (USD)")
    ax.set_xlabel("Date")
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()

    canvas = FigureCanvasTkAgg(fig, master=chart_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)


# --- Save Report
def save_report():
    report_A = result_text_A.get("1.0", tk.END).strip()
    report_B = result_text_B.get("1.0", tk.END).strip()

    if not report_A and not report_B:
        messagebox.showwarning("Empty Report", "There is no report to save.")
        return

    full_report = f"{'=' * 30}\n   REPORT: {ticker_entry_A.get().upper()}   \n{'=' * 30}\n\n{report_A}\n\n\n"
    full_report += f"{'=' * 30}\n   REPORT: {ticker_entry_B.get().upper()}   \n{'=' * 30}\n\n{report_B}"

    file_path = filedialog.asksaveasfilename(
        title="Save Comparison Report As",
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not file_path: return

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_report)
        messagebox.showinfo("Success", f"Report saved successfully to:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Save Error", f"Failed to save report: {e}")


# --- Main Analysis Function
# --- Main Analysis Function
def perform_comparison():
    global chart_data

    show_chart_button.config(state=tk.DISABLED)
    save_report_button.config(state=tk.DISABLED)

    # --- Reset Text Boxes & Configure Color Tags ---

    # 1. Prepare Box A
    result_text_A.config(state=tk.NORMAL)
    result_text_A.delete('1.0', tk.END)
    # Define color (Gold) and font style for the explanation
    result_text_A.tag_config("meaning_tag", foreground="#FFD700", font=('Arial', 10, 'bold'))
    result_text_A.config(state=tk.DISABLED)

    # 2. Prepare Box B
    result_text_B.config(state=tk.NORMAL)
    result_text_B.delete('1.0', tk.END)
    # Define color (Gold) and font style for the explanation
    result_text_B.tag_config("meaning_tag", foreground="#FFD700", font=('Arial', 10, 'bold'))
    result_text_B.config(state=tk.DISABLED)

    chart_data = {"A": None, "B": None}

    if not os.path.isdir(data_folder_path):
        messagebox.showerror("Folder Not Found", f"Path checked: {data_folder_path}")
        return

    ticker_A = ticker_entry_A.get().upper()
    ticker_B = ticker_entry_B.get().upper()

    if not ticker_A and not ticker_B:
        messagebox.showwarning("Missing Ticker", "Please enter at least one stock symbol.")
        return

    period_choice = period_var.get()
    period_map = {"Last Day": 1, "Last Week": 5, "Last Month": 22, "Last 3 Months": 66, "Last 5 Months": 110}
    num_days = period_map.get(period_choice, 1)

    # The exact string to search for highlighting
    search_target = "explanation the main of Dominant Pattern:"

    # --- Process Stock A
    if ticker_A:
        report_A, data_A = analyze_single_ticker(ticker_A, num_days)
        chart_data["A"] = data_A

        result_text_A.config(state=tk.NORMAL)
        result_text_A.insert(tk.END, report_A)

        # Search and Apply Color
        start_pos = result_text_A.search(search_target, "1.0", stopindex=tk.END)
        if start_pos:
            # Highlight the title and the following explanation lines
            end_pos = f"{start_pos} + 3 lines"
            result_text_A.tag_add("meaning_tag", start_pos, end_pos)

        result_text_A.config(state=tk.DISABLED)

    # --- Process Stock B
    if ticker_B:
        report_B, data_B = analyze_single_ticker(ticker_B, num_days)
        chart_data["B"] = data_B

        result_text_B.config(state=tk.NORMAL)
        result_text_B.insert(tk.END, report_B)

        # Search and Apply Color
        start_pos = result_text_B.search(search_target, "1.0", stopindex=tk.END)
        if start_pos:
            # Highlight the title and the following explanation lines
            end_pos = f"{start_pos} + 3 lines"
            result_text_B.tag_add("meaning_tag", start_pos, end_pos)

        result_text_B.config(state=tk.DISABLED)

    show_chart_button.config(state=tk.NORMAL)
    save_report_button.config(state=tk.NORMAL)


# FUNCTION: Show Ticker List Window
def show_ticker_list_window():
    """
    Scans the data folder and displays a new window
    with a searchable list of all tickers.
    """
    global all_ticker_list, data_folder_path

    # Load Ticker List
    if all_ticker_list is None:
        print("Scanning for all tickers...")
        try:
            all_files = [f for f in os.listdir(data_folder_path) if f.endswith('.csv')]
            all_ticker_list = sorted([f.split('.')[0] for f in all_files])

            if not all_ticker_list:
                messagebox.showerror("Error", f"No .csv files found in '{data_folder_path}'")
                return
        except FileNotFoundError:
            messagebox.showerror("Error", f"Data folder not found at '{data_folder_path}'")
            return
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while scanning files: {e}")
            return
        print(f"Found {len(all_ticker_list)} tickers.")

    # Create the Popup Window ---
    list_window = tk.Toplevel(root)
    list_window.title(f"Available Stock ({len(all_ticker_list)})")
    list_window.geometry("300x500")
    list_window.config(bg='#3A4250')

    list_window.transient(root)
    list_window.grab_set()

    # Add a Scrollbar
    scrollbar = tk.Scrollbar(list_window, orient=tk.VERTICAL)

    # Create the ListBox
    list_box = tk.Listbox(list_window,
                          bg='#3A4250',
                          fg='white',
                          font=('Arial', 12),
                          yscrollcommand=scrollbar.set,
                          selectbackground='#FFD700',
                          selectforeground='#212631')

    scrollbar.config(command=list_box.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    list_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Populate the List
    for ticker in all_ticker_list:
        list_box.insert(tk.END, ticker)

    # Copy Ticker on Select
    def on_ticker_select(event):
        selection_indices = list_box.curselection()
        if not selection_indices:
            return

        selected_ticker = list_box.get(selection_indices[0])

        try:
            root.clipboard_clear()
            root.clipboard_append(selected_ticker)

            messagebox.showinfo("Copied!", f"Ticker '{selected_ticker}' copied to clipboard.\n"
                                           f"Paste it (Ctrl+V) into 'Stock 1' or 'Stock 2'.",
                                parent=list_window)

        except tk.TclError:
            messagebox.showwarning("Clipboard Error", "Could not access the clipboard.", parent=list_window)

        list_window.grab_release()
        list_window.destroy()
        ticker_entry_A.focus_set()

    list_box.bind('<<ListboxSelect>>', on_ticker_select)

    def on_window_close():
        list_window.grab_release()
        list_window.destroy()
        ticker_entry_A.focus_set()

    # FIXED: Was 'on_window_Glose', changed to 'on_window_close'
    list_window.protocol("WM_DELETE_WINDOW", on_window_close)


# --- GUI Setup
root = tk.Tk()
root.title("Stock Expert System")
root.geometry("1300x680")
root.resizable(False, False)

# --- Load and display background image ---
try:
    original_image = Image.open(BACKGROUND_IMAGE_PATH)
    resized_image = original_image.resize((1300, 680), Image.LANCZOS)
    bg_image = ImageTk.PhotoImage(resized_image)
    canvas = tk.Canvas(root, width=1300, height=680, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=bg_image, anchor="nw")
    main_frame_on_canvas = tk.Frame(canvas, bg='#1f2e2e')
    canvas.create_window((650, 340), window=main_frame_on_canvas, anchor="center",
                         width=1200, height=630)
    top_title_bar = tk.Label(canvas, text="CHATBOT STOCK MARKET",
                             font=('Arial', 10, 'bold'), fg='#87CEEB', bg='#1A1F26', padx=10, pady=5,
                             relief=tk.RIDGE, borderwidth=2)
    canvas.create_window((650, 20), window=top_title_bar, anchor="center")
except FileNotFoundError:
    messagebox.showerror("Error", f"Background image not found at: {BACKGROUND_IMAGE_PATH}\n"
                                  f"Please place 'background.png' in the same directory as main_app.py.")
    root.config(bg='#212631')
    main_frame_on_canvas = tk.Frame(root, bg='#212631')
    main_frame_on_canvas.pack(expand=True, fill=tk.BOTH, padx=50, pady=25)
except Exception as e:
    messagebox.showerror("Error", f"Could not load background image: {e}")
    root.config(bg='#212631')
    main_frame_on_canvas = tk.Frame(root, bg='#212631')
    main_frame_on_canvas.pack(expand=True, fill=tk.BOTH, padx=50, pady=25)

# Use main_frame_on_canvas for all subsequent widgets
main_frame = main_frame_on_canvas
main_frame.config(bg='#212631')

# --- EXPERT SYSTEM Title
expert_title_label = tk.Label(main_frame, text="EXPERT SYSTEM",
                              font=('Arial', 23, 'bold'), fg='#FFD700', bg='#212631')
expert_title_label.pack(pady=(10, 15))

# --- Stock Inputs Frame ---
ticker_inputs_frame = tk.Frame(main_frame, bg='#212631', relief=tk.FLAT, borderwidth=1)
ticker_inputs_frame.pack(fill='x', padx=50, pady=(0, 10))
# Stock A
tk.Label(ticker_inputs_frame, text="Stock 1:", font=('Arial', 10, 'bold'), fg='white', bg='#212631').pack(side=tk.LEFT,
                                                                                                          padx=(0, 5),
                                                                                                          anchor='w')
ticker_entry_A = tk.Entry(ticker_inputs_frame, width=15, font=('Arial', 12), bg='#3A4250', fg='white',
                          insertbackground='white', bd=2, relief=tk.FLAT)
ticker_entry_A.pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 50))
ticker_entry_A.focus()
# Stock B
tk.Label(ticker_inputs_frame, text="Stock 2:", font=('Arial', 10, 'bold'), fg='white', bg='#212631').pack(side=tk.LEFT,
                                                                                                          padx=(0, 5),
                                                                                                          anchor='w')
ticker_entry_B = tk.Entry(ticker_inputs_frame, width=15, font=('Arial', 12), bg='#3A4250', fg='white',
                          insertbackground='white', bd=2, relief=tk.FLAT)
ticker_entry_B.pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 0))
# Show All stock Button ---
show_tickers_btn = tk.Button(ticker_inputs_frame, text="?",
                             font=('Arial', 10, 'bold'),
                             command=show_ticker_list_window,
                             bg='#3A4250', fg='#FFD700',
                             width=3)
show_tickers_btn.pack(side=tk.LEFT, padx=(10, 0))
# --- Period Selection Frame
period_frame = tk.Frame(main_frame, bg='#212631', bd=4, relief=tk.FLAT)
period_frame.pack(fill='x', padx=50, pady=(10, 15))
tk.Label(period_frame, text="3. Select Analysis Period (for both):", font=('Arial', 13, 'bold'), fg='white',
         bg='#212631').pack(anchor='w', pady=(1, 0))
period_var = tk.StringVar(value="Last Week")
options = ["Last Day", "Last Week", "Last Month", "Last 3 Months", "Last 5 Months"]
radio_frame = tk.Frame(period_frame, bg='#212631')
radio_frame.pack(fill='x')
for option in options:
    rb = tk.Radiobutton(radio_frame, text=option, variable=period_var, value=option,
                        fg='white', bg='#212631', selectcolor='#212631',
                        activebackground='#212631', activeforeground='#FFD700',
                        font=('Arial', 9))
    rb.pack(side=tk.LEFT, padx=10, expand=True)

# --- Run Comparison Button
analyze_button = tk.Button(main_frame, text="4. RUN COMPARISON", command=perform_comparison,
                           font=('Arial', 12, 'bold'), bg='#FFD700', fg='#212631',
                           activebackground='#E6B800', activeforeground='white',
                           bd=0, relief=tk.FLAT, padx=20, pady=10)
analyze_button.pack(pady=(0, 15), fill='x', padx=50)

# --- Action Buttons Frame (Chart/Save)
action_buttons_frame = tk.Frame(main_frame, bg='#212631')
action_buttons_frame.pack(fill='x', pady=(0, 15), padx=50)
show_chart_button = tk.Button(action_buttons_frame, text="Show Comparison Chart", command=open_chart_window,
                              font=('Arial', 10, 'bold'), bg='#3A4250', fg='white',
                              activebackground='#4B5466', activeforeground='#FFD700',
                              state=tk.DISABLED, bd=0, relief=tk.FLAT, padx=15, pady=8)
show_chart_button.pack(side=tk.LEFT, fill='x', expand=True, padx=(0, 10))
save_report_button = tk.Button(action_buttons_frame, text="Save Comparison Report", command=save_report,
                               font=('Arial', 10, 'bold'), bg='#3A4250', fg='white',
                               activebackground='#4B5466', activeforeground='#FFD700',
                               state=tk.DISABLED, bd=0, relief=tk.FLAT, padx=15, pady=8)
save_report_button.pack(side=tk.LEFT, fill='x', expand=True, padx=(10, 0))

# --- Footer ---

footer_label = tk.Label(main_frame, text="SHARIFA",
                        font=('Arial', 11, 'italic'), fg='#9EA7B5', bg='#212631')
footer_label.pack(side=tk.BOTTOM, pady=(15, 10))

# --- Results Display Frames
results_display_frame = tk.Frame(main_frame, bg='#212631')
results_display_frame.pack(fill=tk.BOTH, expand=True, padx=50)

results_display_frame.grid_columnconfigure(0, weight=1)
results_display_frame.grid_columnconfigure(1, weight=1)
results_display_frame.grid_rowconfigure(0, weight=1)

# Frame for Stock 1 Results
frame_A_results = tk.Frame(results_display_frame, bg='#2F3642', bd=0, relief=tk.FLAT)
frame_A_results.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
tk.Label(frame_A_results, text="Results: Stock 1", font=('Arial', 10, 'bold'), fg='white', bg='#2F3642').pack(
    pady=(5, 2))
result_text_A = scrolledtext.ScrolledText(frame_A_results, state=tk.DISABLED, wrap=tk.WORD,
                                          bg='#3A4250', fg='white', insertbackground='white', bd=0, relief=tk.FLAT)
result_text_A.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Frame for Stock 2 Results
frame_B_results = tk.Frame(results_display_frame, bg='#2F3642', bd=0, relief=tk.FLAT)
frame_B_results.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
tk.Label(frame_B_results, text="Results: Stock 2", font=('Arial', 10, 'bold'), fg='white', bg='#2F3642').pack(
    pady=(5, 2))
result_text_B = scrolledtext.ScrolledText(frame_B_results, state=tk.DISABLED, wrap=tk.WORD,
                                          bg='#3A4250', fg='white', insertbackground='white', bd=0, relief=tk.FLAT)
result_text_B.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# --- Start the Application ---
root.mainloop()