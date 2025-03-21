# pip install pandas matplotlib numpy paramiko scipy
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import paramiko
import logging
from datetime import datetime
from scipy.optimize import curve_fit
from config import (
    SSH_HOST, SSH_USER, SSH_KEY_PATH, REMOTE_FILE_PATH,
    SAVE_PLOT, START_TIME, END_TIME
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('temperature_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Read the remote file directly
def read_remote_file():
    logger.info(f"Connecting to {SSH_HOST} to fetch temperature data")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH)

        sftp = ssh.open_sftp()
        with sftp.open(REMOTE_FILE_PATH, 'r') as remote_file:
            logger.debug(f"Reading data from {REMOTE_FILE_PATH}")
            df = pd.read_csv(remote_file, skiprows=1,
                             names=["Datetime", "CPU_Temp"])

        sftp.close()
        ssh.close()
        logger.info(f"Successfully read {len(df)} temperature records")
        return df
    except Exception as e:
        logger.error(f"Failed to read remote file: {str(e)}")
        raise


# Analyze data
def analyze_data(df):
    logger.info("Analyzing temperature data")
    mean_temp = df["CPU_Temp"].mean()
    var_temp = df["CPU_Temp"].var()
    logger.info(f"Mean CPU Temperature: {mean_temp:.2f}°C")
    logger.info(f"Temperature Variance: {var_temp:.2f}")

    timestamps = (df["Datetime"] - df["Datetime"].min()
                  ).dt.total_seconds() / 3600
    coeffs = np.polyfit(timestamps, df["CPU_Temp"], 1)
    temp_rise_per_hour = coeffs[0]
    logger.info(f"Temperature rise per hour: {temp_rise_per_hour:.2f}°C/h")

    return mean_temp, var_temp, temp_rise_per_hour


# Fit a linear trend
def fit_trend(df):
    logger.debug("Fitting trend to temperature data")
    timestamps = (df["Datetime"] - df["Datetime"].min()).dt.total_seconds()
    temps = df["CPU_Temp"].values

    a_guess = np.max(temps)
    b_guess = np.max(temps) - np.min(temps)
    c_guess = 1/timestamps.mean()

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

        logger.debug(f"Exponential fit parameters: {popt}")

        def trend(x):
            return exp_approach(x, *popt)

        return timestamps, trend

    except RuntimeError as e:
        logger.warning(
            f"Exponential fit failed: {str(e)}. Using linear fit instead")
        coeffs = np.polyfit(timestamps, temps, 1)
        logger.debug(f"Linear fit coefficients: {coeffs}")

        def trend(x):
            return coeffs[0] * x + coeffs[1]

        print("Warning: Exponential fit failed, using linear fit instead")
        return timestamps, trend


# Plot data
def plot_data(df, trendline=True):
    logger.info("Generating temperature plot")
    plt.figure(figsize=(12, 6))

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
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    if SAVE_PLOT:
        import os
        os.makedirs('./images', exist_ok=True)
        plot_path = './images/cpu_temperature_plot.png'
        plt.savefig(plot_path, bbox_inches='tight')
        logger.info(f"Plot saved to {plot_path}")

    plt.show()


def filter_timeframe(df):
    logger.debug("Filtering data based on configured timeframe")
    filtered_df = df.copy()

    if START_TIME:
        filtered_df = filtered_df[filtered_df["Datetime"] >= START_TIME]
        logger.debug(f"Filtered data after {START_TIME}")
    if END_TIME:
        filtered_df = filtered_df[filtered_df["Datetime"] <= END_TIME]
        logger.debug(f"Filtered data before {END_TIME}")

    logger.info(
        f"Retained {len(filtered_df)} of {len(df)} records after time filtering")
    return filtered_df


# Main function
def main():
    logger.info("Starting temperature analysis")
    try:
        df = read_remote_file()
        logger.debug("Converting datetime and temperature values")
        df["Datetime"] = pd.to_datetime(df["Datetime"])
        df["CPU_Temp"] = df["CPU_Temp"].str.extract(r'([\d\.]+)').astype(float)

        df = filter_timeframe(df)

        if len(df) == 0:
            logger.error("No data points found in the specified time frame")
            return

        analyze_data(df)
        plot_data(df)
        logger.info("Temperature analysis completed successfully")

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
