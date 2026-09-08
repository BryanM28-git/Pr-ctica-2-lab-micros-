import serial
import time
import requests
import re
import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
import os

# CREDENCIALES LLM
API_KEY = 'TU_API_KEY_AQUI'
API_URL = 'https://api.deepseek.com/v1/chat/completions'

# COMUNICACIÓN SERIAL
PUERTO_COM = 'COM6' 
BAUD_RATE = 115200

# GESTIÓN DE EXCEPCIONES: Previene cierres abruptos si el hardware no está conectado
try:
    esp32 = serial.Serial(PUERTO_COM, BAUD_RATE, timeout=1)
    time.sleep(2) 
except Exception as e:
    print(f"[ERROR] Puerto {PUERTO_COM} inaccesible. Verifique hardware: {e}")
    exit()

def extraer_rpm_con_ia(mensaje_voz):
    # INGENIERÍA DE PROMPTS: Se acota la respuesta del modelo para evitar 
    # procesamiento adicional complejo y obtener un string directamente convertible a int.
    headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
    instruccion = "Extrae solo la cantidad de RPM solicitada. Responde un entero. 'apagar' = 0."
    data = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'system', 'content': instruccion}, {'role': 'user', 'content': mensaje_voz}]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception: return None

def comunicar_con_placa(rpm_objetivo):
    # RX/TX SERIAL: Transmite setpoint con salto de línea (\n) como delimitador de trama
    try:
        esp32.write(f"{rpm_objetivo}\n".encode('utf-8'))
        time.sleep(0.1) 
        
        if esp32.in_waiting > 0:
            respuesta = esp32.readline().decode('utf-8').strip()
            if "RPM_MEDIDA:" in respuesta:
                return respuesta.split(":")[1]
        return "Leyendo ADC..."
    except Exception as e: return f"Error RX/TX: {e}"

def capturar_audio_usuario():
    # ADQUISICIÓN DE AUDIO LOCAL: Muestreo a 44.1kHz para máxima compatibilidad con el motor STT de Google
    fs = 44100
    archivo_temp = "buffer_audio.wav"
    
    grabacion = sd.rec(int(4 * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    write(archivo_temp, fs, grabacion)
    
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(archivo_temp) as source:
            texto = recognizer.recognize_google(recognizer.record(source), language='es-CO')
            return texto
    except sr.UnknownValueError: return None
    finally:
        if os.path.exists(archivo_temp): os.remove(archivo_temp)

def main():
    while True:
        input("\n[ Presione ENTER para hablar ]")
        mensaje = capturar_audio_usuario()
        if not mensaje: continue

        if 'salir' in mensaje.lower() or 'apagar' in mensaje.lower():
            comunicar_con_placa(0)
            esp32.close()
            break 

        respuesta_llm = extraer_rpm_con_ia(mensaje)
        
        # EXPRESIONES REGULARES (RegEx): Aísla estrictamente dígitos de la respuesta de la IA (\d+)
        if respuesta_llm and (numeros := re.findall(r'\d+', respuesta_llm)):
            setpoint_rpm = int(numeros[0])
            feedback_adc = comunicar_con_placa(setpoint_rpm)
            print(f"[*] Setpoint TX: {setpoint_rpm} RPM | Feedback RX: {feedback_adc} RPM")

if __name__ == "__main__":
    main()

