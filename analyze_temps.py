# pip install pandas matplotlib numpy paramiko scipy
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import paramiko
from datetime import datetime
from scipy.optimize import curve_fit
from config import SSH_HOST, SSH_USER, SSH_KEY_PATH, REMOTE_FILE_PATH


# Read the remote file directly
def read_remote_file():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH)

    sftp = ssh.open_sftp()
    with sftp.open(REMOTE_FILE_PATH, 'r') as remote_file:
        # Read directly into pandas
        df = pd.read_csv(remote_file, skiprows=1,
                         names=["Datetime", "CPU_Temp"])

    sftp.close()
    ssh.close()
    return df


# Analyze data
def analyze_data(df):
    mean_temp = df["CPU_Temp"].mean()
    var_temp = df["CPU_Temp"].var()
    print(f"Mean CPU Temp: {mean_temp:.2f}°C")
    print(f"Variance: {var_temp:.2f}")

    timestamps = (df["Datetime"] - df["Datetime"].min()
                  ).dt.total_seconds() / 3600  # Convert to hours
    coeffs = np.polyfit(timestamps, df["CPU_Temp"], 1)  # Linear fit (ax + b)
    temp_rise_per_hour = coeffs[0]
    print(f"Temperature rise per hour: {temp_rise_per_hour:.2f}°C/h")

    return mean_temp, var_temp, temp_rise_per_hour


# Fit a linear trend
def fit_trend(df):
    timestamps = (df["Datetime"] - df["Datetime"].min()).dt.total_seconds()
    temps = df["CPU_Temp"].values

    # Initial parameter guesses
    a_guess = np.max(temps)  # asymptote
    b_guess = np.max(temps) - np.min(temps)  # total change
    c_guess = 1/timestamps.mean()  # time constant

    try:
        # Exponential approach curve fit: y = a - b * exp(-c * x)
        def exp_approach(x, a, b, c):
            return a - b * np.exp(-c * x)

        popt, pcov = curve_fit(
            exp_approach,
            timestamps,
            temps,
            p0=[a_guess, b_guess, c_guess],
            bounds=([0, 0, 0], [np.inf, np.inf, np.inf])
        )

        def trend(x):
            return exp_approach(x, *popt)

        return timestamps, trend

    except RuntimeError:
        # Fallback to linear fit if exponential doesn't converge
        coeffs = np.polyfit(timestamps, temps, 1)

        def trend(x):
            return coeffs[0] * x + coeffs[1]

        print("Warning: Exponential fit failed, using linear fit instead")
        return timestamps, trend


# Plot data
def plot_data(df, trendline=True, save_plot=True):
    plt.figure(figsize=(10, 5))
    plt.plot(df["Datetime"], df["CPU_Temp"],
             label="CPU Temperature", marker='o', linestyle='-')

    if trendline:
        timestamps, trend = fit_trend(df)
        plt.plot(df["Datetime"], trend(timestamps),
                 label="Trendline", linestyle='--', color='red')

    plt.xlabel("Time")
    plt.ylabel("CPU Temperature (°C)")
    plt.title("CPU Temperature Over Time")
    plt.legend()
    plt.grid()
    plt.xticks(rotation=45)

    if save_plot:
        # Create images directory if it doesn't exist
        import os
        os.makedirs('./images', exist_ok=True)

        # Save the plot
        plt.savefig('./images/cpu_temperature_plot.png')

    # Show the plot
    plt.show()


# Main function
def main():
    df = read_remote_file()
    df["Datetime"] = pd.to_datetime(df["Datetime"])  # Convert to datetime
    df["CPU_Temp"] = df["CPU_Temp"].str.extract(
        r'([\d\.]+)').astype(float)  # Extract numeric values
    analyze_data(df)
    plot_data(df)


if __name__ == "__main__":
    main()
