from subprocess import run

from utils.constants import FRONTEND_PATH


def run_dashboard():
    run(["streamlit", "run", FRONTEND_PATH / "dashboard.py"])


if __name__ == "__main__":
    run_dashboard()
