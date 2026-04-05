from __future__ import annotations
import datetime
import time
import schedule

from app.config import Settings, prepare_data_workspace

def run_fall_analysis_task() -> None:
    """Executa os processos de análise de queda"""

    # TODO: Implementar a lógica de análise de queda

    # Etapas para análise da queda:
    # 1. Captura do dataset mais antigo de poses
    
    # 2. Tratamento do dataset (reconhecimento dos diferentes usuários, calculo de métricas de movimento individual, etc)
    
    # 2.1. Se for reconhecido que no dataset as movimentações e velocidades são menores que 1, 
    # o processo de análise pode ser descartado e prosseguir para o próximo dataset
    
    # 3. Aplicação do algoritmo de reconhecimento de queda (RNN)
    
    # 4. Tratamento da situação analisada
    
    # 4.1. Se a queda for detectada, captura do frame da queda (mesmo nome do dataset de poses analisado)
    
    # 4.1.1 Aplicação do YOLO Detect para reconhecimento do ambiente envolvido
    
    # 4.1.2 Registro do evento de queda (JSON com as informações da queda)
    
    # 4.1.3 Publicação do evento de queda para a API externa
    
    # 4.2. Se a queda não for detectada, o dataset de poses deve ser descartado juntamente com a captura do frame 

    now = datetime.datetime.now()
    print(f"My task is running at {now}")

def run_analysis(settings: Settings) -> None:
    """Prepara diretório de dados e executa modelos de postura / quedas."""
    prepare_data_workspace(settings, reset=False)

    schedule.every(settings.pose_csv_window_seconds).seconds.do(run_fall_analysis_task)
    while True:
        schedule.run_pending()
        time.sleep(1)

    print("Machine learning process running")
