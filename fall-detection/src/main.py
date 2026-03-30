import cv2

# 1. Inicializar a webcam (0 é geralmente a câmera padrão)
cap = cv2.VideoCapture(0)

while True:
    # 2. Ler o frame (retorna booleano e a imagem)
    ret, frame = cap.read()

    if not ret:
        break

    # 3. Exibir o frame
    cv2.imshow('Webcam', frame)

    # 4. Parar ao pressionar 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 5. Liberar recursos
cap.release()
cv2.destroyAllWindows()
