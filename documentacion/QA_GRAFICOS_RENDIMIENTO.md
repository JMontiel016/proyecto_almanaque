# Auditoría QA: gráficos, inferencia y rendimiento

## Entregado
- Escenario vectorial con degradado, montañas, parallax, nubes, sol, suelo, cactus y dinosaurios redondeados.
- Animación con Ticker únicamente durante juego no pausado, conservando RepaintBoundary.
- Detección: tobillos en lugar de exigir puntas del pie y calibración reiniciable.
- Pruebas automáticas de salto sin cámara: `python -m unittest discover -s servidor/pruebas -p 'test_optimizacion_pose.py' -v`.

## Prueba Android (pendiente de un equipo físico)
1. Instalar herramientas Flutter/Android y conectar el teléfono por USB.
2. Ejecutar `cd aplicacion && flutter pub get && flutter analyze && flutter test && flutter run --profile`.
3. Jugar una ronda con un cuerpo visible, grabando los resultados de `bash medir_android.sh`.
4. Repetir sobre la versión anterior con el **mismo teléfono**, iluminación, red y duración.
5. Comparar FPS, fotogramas lentos (jank), CPU, RAM, latencia de detección y temperaturas.

## Casos manuales críticos
| Caso | Resultado esperado |
| --- | --- |
| Abrir cámara y denegar permiso | Mensaje claro y ningún bloqueo |
| Cámara frontal / posterior | Calibración renovada y articulaciones alineadas |
| Persona fuera de cuadro >1.5 s | Se descarta referencia anterior |
| Saltar una vez | Un solo evento |
| Agacharse sin despegar pies | No sumar salto |
| Cambiar de aplicación | Cámara liberada y reabierta al volver |
| Servidor desconectado | Mensaje de error recuperable |
| 2 jugadores o más | Puntuación y obstáculos sincronizados |

## Limitaciones
No se ha ejecutado una build real en Android ni una medición de FPS/CPU/RAM en dispositivo.
Las pruebas agregadas necesitan ejecutarse y comprobarse; el script sólo recoge métricas auténticas.
El proyecto contiene `venv/` versionado; excluirlo de futuras distribuciones y retirarlo del repositorio
en una revisión específica, sin eliminar dependencias del sistema del usuario.
