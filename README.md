# Sistema de Control de Velocidad por Voz (ESP32 + Python)

Repositorio desarrollado para la práctica de Conversión Análogo-Digital y Digital-Análogo de la asignatura Micros y Laboratorio (Universidad Militar Nueva Granada).

Este proyecto implementa un sistema HMI por voz para controlar la velocidad de un motor DC. El procesamiento de lenguaje natural (NLP) extrae el setpoint numérico (RPM) y lo transmite por comunicación serial al ESP32. El microcontrolador ejecuta el control PWM y adquiere la señal de velocidad real a través de un convertidor frecuencia-voltaje (LM331) conectado al ADC, mostrando los datos dinámicamente en una pantalla LCD I2C.

## Arquitectura del Hardware
* Microcontrolador ESP32 (Lógica de control y adquisición).
* Convertidor Frecuencia-Voltaje LM331 (Acondicionamiento de señal del encoder).
* Driver L298N (Etapa de potencia transitoria controlada por PWM).
* Pantalla LCD 16x2 con módulo I2C (Interfaz de retroalimentación local).

## Requisitos y Dependencias
Para ejecutar el servidor local en el PC, se requiere un entorno virtual con Python 3 y las siguientes librerías:
* `pyserial`: Comunicación bidireccional PC-ESP32.
* `sounddevice` y `scipy`: Captura y empaquetado de audio del micrófono local.
* `SpeechRecognition`: Transcripción STT (Speech-to-Text).
* `requests`: Consumo de la API LLM (DeepSeek) para extracción de parámetros.

## Ejecución del Sistema
1. Cargar el script `main.py` y la librería de la LCD en la memoria del ESP32.
2. Cerrar el IDE de MicroPython (Thonny/Pymakr) para liberar el puerto COM.
3. Configurar el puerto COM correcto y la API Key en el script de Python.
4. Ejecutar el script de Python e interactuar por voz.

