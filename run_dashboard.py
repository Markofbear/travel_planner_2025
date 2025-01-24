import subprocess
from pathlib import Path


def run_dashboard():
    dashboard_path = Path(__file__).parents[0] / "frontend" / "dashboard.py"

    subprocess.run(["streamlit", "run", str(dashboard_path)])


if __name__ == "__main__":
    run_dashboard()
