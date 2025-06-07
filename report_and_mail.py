import sys, os
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
from email.message import EmailMessage

def main(csv_path, date):
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)

    off  = df.power.where(df.power==0)
    ch1  = df.power.where(df.power==2)
    both = df.power.where(df.power==6)

    plt.figure()
    off.plot(label="Off (0 kW)")
    ch1.plot(label="Ch1 (2 kW)")
    both.plot(label="Both (6 kW)")
    plt.legend()
    plt.ylabel("kW")
    plt.title(f"Heater usage on {date} (CET)")
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

    with smtplib.SMTP_SSL("smtp.example.com", 465) as s:
        s.login(os.environ["EMAIL_USER"], os.environ["EMAIL_PASS"])
        s.send_message(msg)
    print("Email sent.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: report_and_mail.py <csv_path> <date>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
