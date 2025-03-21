# CPU Temperature Analysis Tool

A simple Python tool for analyzing and visualizing CPU temperature data from remote systems (tested on Ubuntu 24.04.2 LTS). This tool fetches temperature logs via SSH, performs statistical analysis, and generates visualizations with trend lines.

## Features

- Remote data fetching via SSH
- Statistical analysis including mean temperature and variance
- Temperature trend analysis (exponential and linear fitting)
- Customizable time frame filtering
- Data visualization with matplotlib
- Optional plot saving

## Prerequisites

- Python 3.x
- Required Python packages:
  ```
  pandas
  matplotlib
  numpy
  paramiko
  scipy
  ```
- Required Server packages (or bring your own temperature data):
  ```
  lm-sensors
  ```

## Setup

1. Clone the repository
2. Setup Server:
   1. Install dependencies:
      ```bash
      sudo apt install lm-sensors
      ```
   2. Move `log_temperature.sh` to `/usr/local/bin/` and make executable
   3. Move `log_temperature.servic` to `/etc/systemd/system/`, enable and sart it
3. Setup Python script:
   1. Install dependencies:
      ```bash
      pip install pandas matplotlib numpy paramiko scipy
      ```
   2. Copy `config.py.example` to `config.py` and update with your settings:
      ```python
      SSH_HOST = "your-host"
      SSH_USER = "your-username"
      SSH_KEY_PATH = "/path/to/your/ssh/key"
      REMOTE_FILE_PATH = "/path/to/remote/temperature.log"
      ```

## Usage

Run the analysis script:
```bash
python analyze_temps.py
```

The script will:
1. Connect to the remote system
2. Fetch temperature data
3. Perform statistical analysis
4. Generate and display a plot
5. Save the plot (if enabled in config)

## Configuration Options

- `SAVE_PLOT`: Enable/disable saving plots to disk
- `START_TIME`: Optional start time filter (format: "YYYY-MM-DD HH:MM:SS")
- `END_TIME`: Optional end time filter (format: "YYYY-MM-DD HH:MM:SS")

## Output

- Console output with analysis results
- Log file: `temperature_analysis.log`
- Plot image: `./images/cpu_temperature_plot.png` (if enabled)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.