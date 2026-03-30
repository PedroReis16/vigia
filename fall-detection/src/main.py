import cv2

from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()
DATA_PATH = os.getenv("DATA_PATH")
if DATA_PATH:
    FRAMES_DIR = os.path.join(DATA_PATH.rstrip("/"), "frames")
    os.makedirs(FRAMES_DIR, exist_ok=True)
else:
    FRAMES_DIR = None

# 1. Inicializar a webcam (0 é geralmente a câmera padrão)
cap = cv2.VideoCapture(0)

item = 0

while True:
    # 2. Ler o frame (retorna booleano e a imagem)
    ret, frame = cap.read()

    if not ret:
        break

    height, width = frame.shape[:2]

    x1 = int(width * 0.05)  # 5% do frame para cada lado (esquerda)
    x2 = int(width * 0.95)  # 5% do frame para cada lado (direita)
    y1 = int(height * 0.05)  # 5% do frame para cada lado (topo)
    y2 = int(height * 0.95)  # 5% do frame para cada lado (base)

    roi = frame[y1:y2, x1:x2]

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # 3. Exibir o frame
    cv2.imshow("Webcam", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("p"):
        if not FRAMES_DIR:
            print("DATA_PATH não definido no .env; não é possível salvar.")
        else:
            item += 1
            path = os.path.join(FRAMES_DIR, f"frame_{item}.png")
            print(f"Saving frame {item} -> {path}...")
            ok = cv2.imwrite(path, roi)
            if ok:
                print(f"Frame {item} saved!")
            else:
                item -= 1
                print(f"Falha ao salvar (cv2.imwrite retornou False): {path}")

    # 4. Parar ao pressionar 'q'
    if key == ord("q"):
        break

# 5. Liberar recursos
cap.release()
cv2.destroyAllWindows()
