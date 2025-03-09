import time
import board
import digitalio
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import Adafruit_DHT
import RPi.GPIO as GPIO

# ตั้งค่าขา GPIO สำหรับปุ่มกด
BUTTON_UP = 17
BUTTON_DOWN = 27
BUTTON_SELECT = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_UP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_SELECT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ตั้งค่าขาเซ็นเซอร์ DHT22
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

# ตั้งค่า LCD
i2c = board.I2C()
lcd_columns = 16
lcd_rows = 2
lcd = character_lcd.Character_LCD_I2C(i2c, lcd_columns, lcd_rows)

# ค่าเริ่มต้น
DEFAULT_TEMP = 60.0  # อุณหภูมิตั้งต้น (องศาเซลเซียส)
DEFAULT_DURATION = 1  # เวลาเริ่มต้น (ชั่วโมง)
target_temp = DEFAULT_TEMP
duration = DEFAULT_DURATION
menu_state = 0  # 0 = แสดงผล, 1 = ตั้งอุณหภูมิ, 2 = ตั้งเวลา
heater_on = False

# ฟังก์ชันอัปเดตหน้าจอ LCD
def update_display():
    lcd.clear()
    if menu_state == 0:  # หน้าจอหลัก
        current_temp = read_temperature()
        lcd.message = f"Temp: {current_temp:.1f}C\nTime: {duration}h | {target_temp}C"
    elif menu_state == 1:  # ตั้งค่าอุณหภูมิ
        lcd.message = "Set Temp:\n{:.1f} C".format(target_temp)
    elif menu_state == 2:  # ตั้งค่าเวลา
        lcd.message = "Set Time:\n{} Hours".format(duration)

# ฟังก์ชันอ่านอุณหภูมิจากเซ็นเซอร์ DHT22
def read_temperature():
    humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
    return temperature if temperature else 0.0

# ฟังก์ชันเริ่มกระบวนการให้ความร้อน
def heating_process():
    global heater_on
    heater_on = True
    start_time = time.time()
    end_time = start_time + (duration * 3600)  # คำนวณเวลาสิ้นสุด (ชั่วโมง -> วินาที)

    while time.time() < end_time:
        current_temp = read_temperature()
        remaining_time = int((end_time - time.time()) / 3600)  # แสดงเวลาที่เหลือเป็นชั่วโมง
        lcd.clear()
        lcd.message = f"Temp: {current_temp:.1f}C\nTime Left: {remaining_time}h"
        if current_temp >= target_temp:
            break  # หยุดให้ความร้อนเมื่อถึงอุณหภูมิที่ตั้งค่า
        time.sleep(5)

    heater_on = False
    lcd.clear()
    lcd.message = "Process Done!"
    time.sleep(2)
    update_display()

# ฟังก์ชันจัดการปุ่มกด
def handle_buttons():
    global menu_state, target_temp, duration

    if not GPIO.input(BUTTON_SELECT):  # เปลี่ยนโหมดการตั้งค่า
        menu_state = (menu_state + 1) % 3
        update_display()
        time.sleep(0.3)

    if not GPIO.input(BUTTON_UP):  # เพิ่มค่า
        if menu_state == 1:  # ปรับอุณหภูมิ
            target_temp += 1.0
        elif menu_state == 2:  # ปรับเวลา (เป็นชั่วโมง)
            duration += 1
        update_display()
        time.sleep(0.2)

    if not GPIO.input(BUTTON_DOWN):  # ลดค่า
        if menu_state == 1 and target_temp > 1.0:  # ปรับอุณหภูมิ (ต่ำสุด 1°C)
            target_temp -= 1.0
        elif menu_state == 2 and duration > 1:  # ปรับเวลา (ต่ำสุด 1 ชั่วโมง)
            duration -= 1
        update_display()
        time.sleep(0.2)

# เริ่มทำงาน
update_display()
try:
    while True:
        handle_buttons()
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
    lcd.clear()
