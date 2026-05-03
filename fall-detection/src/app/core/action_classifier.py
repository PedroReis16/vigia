import datetime
import queue

from app.core.fall_classifier import FallClassifier

def _send_notification() -> None:
    """Envia notificação para o usuário"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"Notificação enviada para o usuário em {now}")

def run_classifier(buffer_queue: queue.Queue) -> None:
    """Consome janelas prontas de captura, iniciando o processo de classificação"""

    fall_classifier = FallClassifier()

    # gru_model = Model() -> Carrega o modelo GRU

    try:


        while True:
            try:
                pid, window = buffer_queue.get(timeout=1.0)

                pred = fall_classifier.predict(window[0])
                if pred is not None:
                    print(f"Predição para o ID '{pid}': {pred['label']} com probabilidade {pred['prob_deitado']}")
                    _send_notification()
            except queue.Empty:
                continue # fila vazia, espera próxima janela

    except KeyboardInterrupt:
        pass