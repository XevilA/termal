

import time
import datetime
import threading
import RPi.GPIO as GPIO
import Adafruit_DHT  # สำหรับเซนเซอร์อุณหภูมิ DHT (เช่น DHT22)
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd  # สำหรับจอ LCD

# กำหนดพิน GPIO
HEATER_PIN = 17       # พินควบคุมฮีตเตอร์ (ผ่าน SSR หรือ รีเลย์)
FAN_PIN = 18          # พินควบคุมพัดลม
TEMP_SENSOR_PIN = 4   # พินสำหรับเซนเซอร์อุณหภูมิ (DHT22)
BUTTON_START = 22     # ปุ่มเริ่มทำงาน
BUTTON_STOP = 23      # ปุ่มหยุดทำงาน
BUTTON_UP = 24        # ปุ่มเพิ่มค่า
BUTTON_DOWN = 25      # ปุ่มลดค่า
BUTTON_SELECT = 27    # ปุ่มเลือก

# กำหนดค่าเริ่มต้น
DEFAULT_TARGET_TEMP = 60.0  # อุณหภูมิเป้าหมายเริ่มต้น (องศาเซลเซียส)
DEFAULT_DURATION = 30       # ระยะเวลาทำงานเริ่มต้น (นาที)
TEMP_TOLERANCE = 2.0        # ค่าความคลาดเคลื่อนของอุณหภูมิที่ยอมรับได้

# ตัวแปรสถานะ
running = False
current_temp = 0.0
target_temp = DEFAULT_TARGET_TEMP
duration = DEFAULT_DURATION
remaining_time = 0
menu_state = 0  # 0: หน้าหลัก, 1: ตั้งอุณหภูมิ, 2: ตั้งเวลา

# ตั้งค่า GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ตั้งค่า output pins
GPIO.setup(HEATER_PIN, GPIO.OUT)
GPIO.setup(FAN_PIN, GPIO.OUT)

# ตั้งค่า input pins พร้อม pull-up resistors
GPIO.setup(BUTTON_START, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_STOP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_UP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_SELECT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ตั้งค่าจอ LCD
lcd_rs = digitalio.DigitalInOut(board.D26)
lcd_en = digitalio.DigitalInOut(board.D19)
lcd_d4 = digitalio.DigitalInOut(board.D13)
lcd_d5 = digitalio.DigitalInOut(board.D6)
lcd_d6 = digitalio.DigitalInOut(board.D5)
lcd_d7 = digitalio.DigitalInOut(board.D11)
lcd_columns = 16
lcd_rows = 2

lcd = characterlcd.Character_LCD_Mono(
    lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, 
    lcd_columns, lcd_rows
)

# ฟังก์ชั่นอ่านอุณหภูมิ
def read_temperature():
    sensor = Adafruit_DHT.DHT22
    humidity, temperature = Adafruit_DHT.read_retry(sensor, TEMP_SENSOR_PIN)
    
    if humidity is not None and temperature is not None:
        return temperature
    else:
        # หากอ่านไม่สำเร็จ คืนค่าเดิม
        return current_temp

# ฟังก์ชั่นควบคุมฮีตเตอร์
def control_heater(state):
    GPIO.output(HEATER_PIN, state)

# ฟังก์ชั่นควบคุมพัดลม
def control_fan(state):
    GPIO.output(FAN_PIN, state)

# ฟังก์ชั่นการทำงานหลัก
def heating_process():
    global running, current_temp, remaining_time
    
    start_time = time.time()
    end_time = start_time + (duration * 60)  # แปลงเป็นวินาที
    
    while running and time.time() < end_time:
        current_temp = read_temperature()
        remaining_time = int((end_time - time.time()) / 60)  # แปลงเป็นนาที
        
        # ตรวจสอบและควบคุมอุณหภูมิ
        if current_temp < target_temp - TEMP_TOLERANCE:
            # อุณหภูมิต่ำกว่าเป้าหมาย - เปิดฮีตเตอร์
            control_heater(True)
        elif current_temp > target_temp + TEMP_TOLERANCE:
            # อุณหภูมิสูงกว่าเป้าหมาย - ปิดฮีตเตอร์
            control_heater(False)
        
        # อัพเดตหน้าจอ
        update_display()
        
        # หน่วงเวลาเพื่อลดการอ่านค่าถี่เกินไป
        time.sleep(1)
    
    # เมื่อเสร็จสิ้นการทำงาน ปิดทุกอย่าง
    control_heater(False)
    control_fan(False)
    running = False
    remaining_time = 0
    update_display()
    
    # แจ้งเตือนเมื่อเสร็จสิ้น
    lcd.clear()
    lcd.message = "  เสร็จสิ้น!\n"
    time.sleep(3)
    update_display()

# ฟังก์ชั่นอัพเดตหน้าจอ
def update_display():
    lcd.clear()
    
    if menu_state == 0:  # หน้าหลัก
        if running:
            lcd.message = f"Temp: {current_temp:.1f}C\nTime left: {remaining_time}m"
        else:
            lcd.message = f"Temp: {current_temp:.1f}C\nReady to start"
    elif menu_state == 1:  # ตั้งอุณหภูมิ
        lcd.message = "Set temperature:\n{:.1f}C".format(target_temp)
    elif menu_state == 2:  # ตั้งเวลา
        lcd.message = "Set duration:\n{} minutes".format(duration)

# ฟังก์ชั่นเริ่มทำงาน
def start_heating():
    global running
    
    if not running:
        running = True
        control_fan(True)  # เปิดพัดลม
        
        # เริ่มการทำงานในเธรดแยก
        heating_thread = threading.Thread(target=heating_process)
        heating_thread.daemon = True
        heating_thread.start()

# ฟังก์ชั่นหยุดทำงาน
def stop_heating():
    global running
    
    running = False
    control_heater(False)
    control_fan(False)
    update_display()

# ฟังก์ชั่นจัดการปุ่มกด
def handle_buttons():
    global menu_state, target_temp, duration
    
    # ตรวจสอบปุ่ม SELECT เพื่อเปลี่ยนเมนู
    if not GPIO.input(BUTTON_SELECT):
        global menu_state
        menu_state = (menu_state + 1) % 3
        update_display()
        time.sleep(0.3)  # ป้องกันการกดซ้ำ
    
    # ตรวจสอบปุ่ม UP
    if not GPIO.input(BUTTON_UP):
        if menu_state == 1:  # ตั้งอุณหภูมิ
            target_temp += 1.0
        elif menu_state == 2:  # ตั้งเวลา
            duration += 5
        update_display()
        time.sleep(0.2)  # ป้องกันการกดซ้ำ
    
    # ตรวจสอบปุ่ม DOWN
    if not GPIO.input(BUTTON_DOWN):
        if menu_state == 1 and target_temp > 1.0:  # ตั้งอุณหภูมิ (ต่ำสุด 1 องศา)
            target_temp -= 1.0
        elif menu_state == 2 and duration > 5:  # ตั้งเวลา (ต่ำสุด 5 นาที)
            duration -= 5
        update_display()
        time.sleep(0.2)  # ป้องกันการกดซ้ำ
    
    # ตรวจสอบปุ่ม START
    if not GPIO.input(BUTTON_START):
        start_heating()
        time.sleep(0.3)  # ป้องกันการกดซ้ำ
    
    # ตรวจสอบปุ่ม STOP
    if not GPIO.input(BUTTON_STOP):
        stop_heating()
        time.sleep(0.3)  # ป้องกันการกดซ้ำ

# ฟังก์ชั่นทำความสะอาด GPIO เมื่อโปรแกรมจบการทำงาน
def cleanup():
    control_heater(False)
    control_fan(False)
    lcd.clear()
    GPIO.cleanup()

# ฟังก์ชั่นหลัก
def main():
    global current_temp
    
    try:
        lcd.clear()
        lcd.message = "ตู้อบลมร้อน\nกำลังเริ่มต้น..."
        time.sleep(2)
        
        # อ่านอุณหภูมิเริ่มต้น
        current_temp = read_temperature()
        update_display()
        
        # ลูปหลักของโปรแกรม
        while True:
            # อ่านอุณหภูมิปัจจุบัน (ถ้าไม่ได้กำลังทำงาน)
            if not running:
                current_temp = read_temperature()
                update_display()
            
            # ตรวจสอบปุ่มกด
            handle_buttons()
            
            # หน่วงเวลาเล็กน้อย
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
