import sys
import select
import time
from machine import Pin, Timer, PWM, ADC, I2C
from micropython_i2c_lcd import I2cLcd 

# SALIDAS Y ENTRADAS DE CONTROL
# Se usa PWM a 1kHz para la etapa de potencia preliminar
motor_pwm = PWM(Pin(25), freq=1000)
motor_pwm.duty(0)

# ADQUISICIÓN DE SEÑAL (ADC)
# Atenuación de 11dB para adaptar el rango de lectura a 0 - 3.3V, ideal para el LM331
adc_lm331 = ADC(Pin(34))
adc_lm331.atten(ADC.ATTN_11DB) 

# INTERFAZ I2C
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = I2cLcd(i2c, 0x27, 2, 16) 

# VARIABLES DE ESTADO Y CALIBRACIÓN
rpm_actuales = 0
rpm_deseadas = 0
MAX_RPM_MOTOR = 3000
factor_calibracion = 1000 # Constante de transferencia V -> RPM

def actualizar_lecturas(timer):
    # INTERRUPCIÓN POR HARDWARE: 
    # Esta función se ejecuta independientemente del hilo principal para garantizar
    # el refresco de la pantalla y la lectura del ADC sin retardos bloqueantes.
    global rpm_actuales
    
    voltaje = adc_lm331.read() * (3.3 / 4095.0)
    rpm_actuales = int(voltaje * factor_calibracion)
    
    lcd.move_to(0, 0)
    lcd.putstr(f"Obj: {rpm_deseadas} RPM   ")
    lcd.move_to(0, 1)
    lcd.putstr(f"Act: {rpm_actuales} RPM   ")

# Configuración del Timer para muestreo a 2Hz (500ms)
timer = Timer(0)
timer.init(period=500, mode=Timer.PERIODIC, callback=actualizar_lecturas)

# COMUNICACIÓN ASÍNCRONA
# Se instancia un objeto de polling para leer el puerto serial (sys.stdin) 
# evitando que el microcontrolador se detenga esperando datos.
poll = select.poll()
poll.register(sys.stdin, select.POLLIN)

lcd.clear()
lcd.putstr("Sistema Listo")

try:
    while True:
        # Revisa el buffer sin bloquear (timeout = 0)
        if poll.poll(0):
            comando_recibido = sys.stdin.readline().strip()
            
            if comando_recibido.isdigit():
                # Saturación de control para proteger la planta (motor)
                rpm_deseadas = max(0, min(MAX_RPM_MOTOR, int(comando_recibido)))
                
                # Mapeo de setpoint a ciclo de trabajo (0-1023)
                motor_pwm.duty(int((rpm_deseadas / MAX_RPM_MOTOR) * 1023))
                
                # Feedback de lazo al PC
                print(f"RPM_MEDIDA:{rpm_actuales}")
                
        time.sleep(0.05)
        
except KeyboardInterrupt:
    timer.deinit()
    motor_pwm.duty(0)

