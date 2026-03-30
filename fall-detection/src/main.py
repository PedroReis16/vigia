import cv2

# 1. Inicializar a webcam (0 é geralmente a câmera padrão)
cap = cv2.VideoCapture(0)

while True:
    # 2. Ler o frame (retorna booleano e a imagem)
    ret, frame = cap.read()

    if not ret:
        break

    height, width = frame.shape[:2]
    
    x1 = int(width * 0.05) # 5% do frame para cada lado (esquerda)
    x2 = int(width * 0.95) # 5% do frame para cada lado (direita)
    y1 = int(height * 0.05) # 5% do frame para cada lado (topo)
    y2 = int(height * 0.95) # 5% do frame para cada lado (base)

    roi = frame[y1:y2, x1:x2]

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # 3. Exibir o frame
    cv2.imshow('Webcam', frame)

    # 4. Parar ao pressionar 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 5. Liberar recursos
cap.release()
cv2.destroyAllWindows()
