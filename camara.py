import cv2
import numpy as np

# Abrir la cámara web predeterminada
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: No se pudo abrir la cámara.")
    exit()

# Leer el primer fotograma para inicializar
ret, frame = cap.read()
if not ret:
    print("Error al leer el fotograma de la cámara.")
    exit()

# Voltear la imagen como espejo y convertir a escala de grises
frame = cv2.flip(frame, 1)
prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)

prev_center = None
direction = "Quieto"

print("Iniciando detector. Mueve tu mano frente a la cámara. Presiona 'ESC' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Voltear horizontalmente para efecto espejo
    frame = cv2.flip(frame, 1)
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Calcular la diferencia absoluta entre el fotograma actual y el anterior
    diff = cv2.absdiff(prev_gray, gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Encontrar contornos de las áreas con movimiento
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    current_center = None
    max_area = 0

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 5000:  # Filtrar ruido pequeño (puedes ajustarlo si es necesario)
            if area > max_area:
                max_area = area
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    current_center = (cX, cY)

    # Determinar la dirección comparando la posición anterior y la actual
    if prev_center is not None and current_center is not None:
        dx = current_center[0] - prev_center[0]
        dy = current_center[1] - prev_center[1]
        threshold_move = 12  # Sensibilidad del movimiento

        if abs(dx) > abs(dy):
            if dx > threshold_move:
                direction = "Derecha"
            elif dx < -threshold_move:
                direction = "Izquierda"
        else:
            if dy > threshold_move:
                direction = "Abajo"
            elif dy < -threshold_move:
                direction = "Arriba"

    # Dibujar el punto de seguimiento en la pantalla
    if current_center is not None:
        prev_center = current_center
        cv2.circle(frame, current_center, 8, (0, 0, 255), -1)

    # Mostrar el texto de la dirección detectada en la ventana
    cv2.putText(frame, f"Movimiento: {direction}", (30, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    cv2.imshow("Detector de Movimiento - Python", frame)
    prev_gray = gray.copy()

    # Salir presionando la tecla ESC (código 27)
    if cv2.waitKey(30) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()