from __future__ import annotations
import datetime
import time
import schedule

from app.config import Settings, prepare_data_workspace

def my_task() -> None:
    now = datetime.datetime.now()
    print(f"My task is running at {now}")

def run_analysis(settings: Settings) -> None:
    """Prepara diretório de dados e executa modelos de postura / quedas."""
    prepare_data_workspace(settings, reset=False)

    schedule.every(settings.pose_csv_window_seconds).seconds.do(my_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

    print("Machine learning process running")
