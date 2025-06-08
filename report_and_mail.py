import sys, os
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from email.message import EmailMessage
import matplotlib.dates as mdates

def main(csv_path, date):
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)

    fig, (ax1, ax2) = plt.subplots(
        ncols=2, figsize=(12, 4), 
        gridspec_kw={'width_ratios': [3, 1]}
    )
    
    ax1.step(df.index, df.power, where='post', linewidth=2, label='Power (kW)')
    ax1.fill_between(df.index, df.power, step='post', alpha=0.2)
    ax1.set_ylabel("kW")
    ax1.set_title(f"Heater usage on {date} (CET)")
    
    ax1.xaxis.set_major_locator(mdates.HourLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
    
    interval_min = 2
    counts = df.power.value_counts().to_dict()
    durations = {
        0: counts.get(0, 0) * interval_min,
        2: counts.get(2, 0) * interval_min,
        6: counts.get(6, 0) * interval_min
    }
    
    labels = ['Off (0 kW)', 'Ch1 (2 kW)', 'Both (6 kW)']
    sizes = [durations[0], durations[2], durations[6]]
    labels_h = [f"{labels[i]}: {sizes[i]/60:.2f} h" for i in range(3)]
    
    ax2.pie(sizes, labels=labels_h, autopct="%1.1f%%", startangle=90)
    ax2.set_title("Runtime distribution")
    
    plt.tight_layout()
    
    plot_dir = os.path.join("solar_data_PV","plots")
    os.makedirs(plot_dir, exist_ok=True)
    plot_path = os.path.join(plot_dir, f"{date}.png")
    plt.savefig(plot_path)
    print(f"Saved plot to {plot_path}")

    msg = EmailMessage()
    msg["Subject"] = f"Daily Heater Report {date}"
    msg["From"]    = os.environ["EMAIL_USER"]
    msg["To"]      = os.environ["EMAIL_TO"]
    msg.set_content(f"Attached is the heater usage plot for {date}.")
    with open(plot_path, "rb") as f:
        img = f.read()
    msg.add_attachment(img, maintype="image", subtype="png", filename=f"{date}.png")

    with smtplib.SMTP_SSL('smtp.gmail.com', 587) as s:
        s.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
        s.send_message(msg)
    print("Email sent.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: report_and_mail.py <csv_path> <date>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
