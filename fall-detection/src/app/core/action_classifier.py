import datetime
import queue



def _send_notification() -> None:
    """Envia notificação para o usuário"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"Notificação enviada para o usuário em {now}")

def run_classifier(buffer_queue: queue.Queue) -> None:
    """Consome janelas prontas de captura, iniciando o processo de classificação"""
    

    # gru_model = Model() -> Carrega o modelo GRU

    while True:
        try:
            pid, window = buffer_queue.get(timeout=1.0)

            # Envia para o modelo
            results = []
            print(f"Janela recebida para o ID '{pid}'")
            _send_notification()

        except queue.Empty:
            continue # fila vazia, espera próxima janela