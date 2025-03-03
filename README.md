# คู่มือการติดตั้งระบบตู้อบลมร้อนอัตโนมัติด้วย Raspberry Pi 5

คู่มือนี้จะอธิบายวิธีการติดตั้งและใช้งานระบบตู้อบลมร้อนอัตโนมัติที่ควบคุมด้วย Raspberry Pi 5 ซึ่งจะควบคุมอุณหภูมิตามที่กำหนด และทำงานตามเวลาที่ตั้งไว้

## สารบัญ

1. [อุปกรณ์ที่ต้องใช้](#อุปกรณ์ที่ต้องใช้)
2. [การติดตั้งระบบปฏิบัติการและแพ็คเกจ](#การติดตั้งระบบปฏิบัติการและแพ็คเกจ)
3. [การต่อวงจร](#การต่อวงจร)
4. [การติดตั้งโค้ด](#การติดตั้งโค้ด)
5. [การใช้งาน](#การใช้งาน)
6. [การแก้ไขปัญหา](#การแก้ไขปัญหา)
7. [การปรับแต่งเพิ่มเติม](#การปรับแต่งเพิ่มเติม)

## อุปกรณ์ที่ต้องใช้

1. **Raspberry Pi 5** พร้อม SD Card (อย่างน้อย 16GB)
2. **จอ LCD แบบ Character** (16x2 หรือ 20x4)
3. **เซนเซอร์อุณหภูมิ DHT22** หรือ DS18B20
4. **ชุดรีเลย์ (Relay Module)** หรือ SSR (Solid State Relay) สำหรับควบคุมฮีตเตอร์
5. **ฮีตเตอร์ไฟฟ้า**
6. **พัดลมระบายอากาศ**
7. **ปุ่มกด 5 ปุ่ม** (Start, Stop, Up, Down, Select)
8. **แหล่งจ่ายไฟ** สำหรับ Raspberry Pi และวงจรควบคุม
9. **เบรกเกอร์** สำหรับตัดไฟฟ้าเมื่อเกิดเหตุผิดปกติ
10. **สายไฟ** และ **ตู้ควบคุม**

## การติดตั้งระบบปฏิบัติการและแพ็คเกจ

### 1. ติดตั้ง Raspberry Pi OS

1. ดาวน์โหลด Raspberry Pi Imager จาก [raspberrypi.org/software](https://www.raspberrypi.org/software/)
2. เปิดโปรแกรมและเลือกติดตั้ง Raspberry Pi OS (32-bit หรือ 64-bit)
3. เลือก SD Card และทำการติดตั้ง
4. เสียบ SD Card เข้ากับ Raspberry Pi และเปิดเครื่อง
5. ทำการตั้งค่าเริ่มต้น (ตั้งค่า WiFi, รหัสผ่าน, และอื่นๆ)

### 2. อัพเดตระบบและติดตั้งแพ็คเกจที่จำเป็น

เปิด Terminal และรันคำสั่งต่อไปนี้:

```bash
# อัพเดตระบบ
sudo apt update
sudo apt upgrade -y

# ติดตั้งแพ็คเกจที่จำเป็น
sudo apt install python3-pip python3-dev python3-setuptools git -y

# ติดตั้ง Python libraries
sudo pip3 install RPi.GPIO Adafruit_DHT adafruit-circuitpython-charlcd

# ติดตั้ง I2C เซอร์วิส (ถ้าใช้จอ LCD แบบ I2C)
sudo apt-get install -y python3-smbus i2c-tools
sudo pip3 install adafruit-circuitpython-charlcd_i2c

# เปิดใช้งาน I2C และ SPI
sudo raspi-config
```

ใน raspi-config ให้เลือก:
1. Interface Options
2. เปิดใช้งาน I2C, SPI, และ 1-Wire (ถ้าใช้เซนเซอร์ DS18B20)

### 3. ทดสอบการติดตั้ง

```bash
# ทดสอบว่า Python libraries ติดตั้งสำเร็จ
python3 -c "import RPi.GPIO as GPIO; print('GPIO OK')"
python3 -c "import Adafruit_DHT; print('DHT Sensor OK')"
python3 -c "import board; import digitalio; import adafruit_character_lcd.character_lcd as characterlcd; print('LCD OK')"
```

ถ้าไม่มี error แสดงว่าติดตั้งสำเร็จแล้ว

## การต่อวงจร

### การต่อวงจรเซนเซอร์อุณหภูมิ DHT22

| DHT22 Pin | Raspberry Pi Pin |
|-----------|------------------|
| VCC       | 3.3V (Pin 1)     |
| Data      | GPIO 4 (Pin 7)   |
| GND       | GND (Pin 6)      |

อย่าลืมต่อตัวต้านทาน Pull-up 10kΩ ระหว่าง VCC และ Data

### การต่อวงจร LCD แบบ Character (16x2)

| LCD Pin | Raspberry Pi Pin   |
|---------|-------------------|
| RS      | GPIO 26 (Pin 37)  |
| E       | GPIO 19 (Pin 35)  |
| D4      | GPIO 13 (Pin 33)  |
| D5      | GPIO 6 (Pin 31)   |
| D6      | GPIO 5 (Pin 29)   |
| D7      | GPIO 11 (Pin 23)  |
| VSS     | GND (Pin 39)      |
| VDD     | 5V (Pin 2)        |
| V0      | ตัวปรับความสว่าง (ต่อผ่านตัวต้านทาน 10kΩ ไปยัง GND) |
| A       | 5V (แบ็คไลท์)     |
| K       | GND (แบ็คไลท์)    |

### การต่อวงจรปุ่มกด

| ปุ่ม      | Raspberry Pi Pin  |
|----------|------------------|
| START    | GPIO 22 (Pin 15) |
| STOP     | GPIO 23 (Pin 16) |
| UP       | GPIO 24 (Pin 18) |
| DOWN     | GPIO 25 (Pin 22) |
| SELECT   | GPIO 27 (Pin 13) |

ต่อปลายอีกด้านของปุ่มเข้ากับ GND และใช้ Pull-up resistor 10kΩ ต่อระหว่างขาสัญญาณและ 3.3V

### การต่อวงจรรีเลย์/SSR

| อุปกรณ์  | Raspberry Pi Pin |
|---------|------------------|
| ฮีตเตอร์  | GPIO 17 (Pin 11) |
| พัดลม    | GPIO 18 (Pin 12) |

**คำเตือน**: การต่อวงจรที่ทำงานกับไฟฟ้าแรงดันสูงควรดำเนินการโดยช่างไฟฟ้าที่มีความชำนาญเท่านั้น!

#### วงจรป้องกัน

1. ใช้ **Optocoupler** เพื่อแยกวงจรไฟฟ้าแรงดันสูงออกจาก Raspberry Pi
2. ติดตั้ง **เบรกเกอร์** เพื่อป้องกันกระแสไฟฟ้าเกิน
3. ติดตั้ง **Fuse** เพื่อป้องกันไฟฟ้าลัดวงจร

## การติดตั้งโค้ด

1. สร้างไฟล์ Python ใหม่:

```bash
cd ~
mkdir hot_air_oven
cd hot_air_oven
nano hot_air_oven.py
```

2. คัดลอกโค้ดต่อไปนี้ลงในไฟล์:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import datetime
import threading
import RPi.GPIO as GPIO
import Adafruit_DHT
import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

# กำหนดพิน GPIO
HEATER_PIN = 17
FAN_PIN = 18
TEMP_SENSOR_PIN = 4
BUTTON_START = 22
BUTTON_STOP = 23
BUTTON_UP = 24
BUTTON_DOWN = 25
BUTTON_SELECT = 27

# กำหนดค่าเริ่มต้น
DEFAULT_TARGET_TEMP = 60.0
DEFAULT_DURATION = 30
TEMP_TOLERANCE = 2.0

# ตัวแปรสถานะ
running = False
current_temp = 0.0
target_temp = DEFAULT_TARGET_TEMP
duration = DEFAULT_DURATION
remaining_time = 0
menu_state = 0

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
    end_time = start_time + (duration * 60)
    
    while running and time.time() < end_time:
        current_temp = read_temperature()
        remaining_time = int((end_time - time.time()) / 60)
        
        # ตรวจสอบและควบคุมอุณหภูมิ
        if current_temp < target_temp - TEMP_TOLERANCE:
            control_heater(True)
        elif current_temp > target_temp + TEMP_TOLERANCE:
            control_heater(False)
        
        update_display()
        time.sleep(1)
    
    control_heater(False)
    control_fan(False)
    running = False
    remaining_time = 0
    update_display()
    
    lcd.clear()
    lcd.message = "  เสร็จสิ้น!\n"
    time.sleep(3)
    update_display()

# ฟังก์ชั่นอัพเดตหน้าจอ
def update_display():
    lcd.clear()
    
    if menu_state == 0:
        if running:
            lcd.message = f"Temp: {current_temp:.1f}C\nTime left: {remaining_time}m"
        else:
            lcd.message = f"Temp: {current_temp:.1f}C\nReady to start"
    elif menu_state == 1:
        lcd.message = "Set temperature:\n{:.1f}C".format(target_temp)
    elif menu_state == 2:
        lcd.message = "Set duration:\n{} minutes".format(duration)

# ฟังก์ชั่นเริ่มทำงาน
def start_heating():
    global running
    
    if not running:
        running = True
        control_fan(True)
        
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
    
    if not GPIO.input(BUTTON_SELECT):
        global menu_state
        menu_state = (menu_state + 1) % 3
        update_display()
        time.sleep(0.3)
    
    if not GPIO.input(BUTTON_UP):
        if menu_state == 1:
            target_temp += 1.0
        elif menu_state == 2:
            duration += 5
        update_display()
        time.sleep(0.2)
    
    if not GPIO.input(BUTTON_DOWN):
        if menu_state == 1 and target_temp > 1.0:
            target_temp -= 1.0
        elif menu_state == 2 and duration > 5:
            duration -= 5
        update_display()
        time.sleep(0.2)
    
    if not GPIO.input(BUTTON_START):
        start_heating()
        time.sleep(0.3)
    
    if not GPIO.input(BUTTON_STOP):
        stop_heating()
        time.sleep(0.3)

# ฟังก์ชั่นทำความสะอาด GPIO
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
        
        current_temp = read_temperature()
        update_display()
        
        while True:
            if not running:
                current_temp = read_temperature()
                update_display()
            
            handle_buttons()
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
```

3. บันทึกไฟล์และออกจาก nano โดยกด `Ctrl+X`, ตามด้วย `Y` และ `Enter`

4. ทำให้ไฟล์สามารถรันได้:

```bash
chmod +x hot_air_oven.py
```

5. ทดสอบรันโปรแกรม:

```bash
python3 hot_air_oven.py
```

## การตั้งค่าให้รันอัตโนมัติเมื่อเปิดเครื่อง

1. สร้างไฟล์ service สำหรับ systemd:

```bash
sudo nano /etc/systemd/system/hot-air-oven.service
```

2. เพิ่มข้อมูลต่อไปนี้:

```
[Unit]
Description=Hot Air Oven Automatic Control
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/hot_air_oven
ExecStart=/usr/bin/python3 /home/pi/hot_air_oven/hot_air_oven.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

3. บันทึกและออกจาก nano

4. เปิดใช้งาน service:

```bash
sudo systemctl enable hot-air-oven.service
sudo systemctl start hot-air-oven.service
```

5. ตรวจสอบสถานะ:

```bash
sudo systemctl status hot-air-oven.service
```

## การใช้งาน

1. **เริ่มใช้งาน**:
   - กดปุ่ม SELECT เพื่อเลือกระหว่างหน้าหลัก, ตั้งอุณหภูมิ, และตั้งเวลา
   - ใช้ปุ่ม UP/DOWN เพื่อปรับค่าอุณหภูมิหรือเวลา
   - กดปุ่ม START เพื่อเริ่มการทำงาน
   - กดปุ่ม STOP เพื่อหยุดการทำงาน

2. **ระหว่างการทำงาน**:
   - จอ LCD จะแสดงอุณหภูมิปัจจุบันและเวลาที่เหลือ
   - ระบบจะควบคุมอุณหภูมิให้อยู่ในช่วงที่กำหนด
   - เมื่อครบเวลา ระบบจะปิดการทำงานอัตโนมัติ

## การแก้ไขปัญหา

### อุณหภูมิไม่ถูกต้อง

1. ตรวจสอบการเชื่อมต่อของเซนเซอร์
2. ลองเปลี่ยนเซนเซอร์ใหม่
3. ปรับแก้โค้ดในส่วนของฟังก์ชัน `read_temperature()`

### จอ LCD ไม่แสดงผล

1. ตรวจสอบการเชื่อมต่อของจอ LCD
2. ตรวจสอบความสว่างของจอ (ปรับตัวต้านทานที่ขา V0)
3. ตรวจสอบว่าได้ติดตั้งไลบรารีครบถ้วนแล้ว

### ฮีตเตอร์ไม่ทำงาน

1. ตรวจสอบการเชื่อมต่อของรีเลย์หรือ SSR
2. ตรวจสอบฟิวส์และเบรกเกอร์
3. ตรวจสอบค่า GPIO ในไฟล์โค้ด

### ปุ่มกดไม่ทำงาน

1. ตรวจสอบการเชื่อมต่อของปุ่มกด
2. ตรวจสอบว่าได้ต่อ Pull-up resistor ถูกต้อง
3. ตรวจสอบค่า GPIO ในไฟล์โค้ด

## การปรับแต่งเพิ่มเติม

### เพิ่มระบบแจ้งเตือน

```python
# เพิ่มในส่วนของการกำหนดพิน
BUZZER_PIN = 16

# เพิ่มในส่วนตั้งค่า GPIO
GPIO.setup(BUZZER_PIN, GPIO.OUT)
buzzer = GPIO.PWM(BUZZER_PIN, 440)

# เพิ่มฟังก์ชั่นเสียงเตือน
def sound_alert(duration=1):
    buzzer.start(50)
    time.sleep(duration)
    buzzer.stop()

# เรียกใช้ฟังก์ชั่นเมื่อต้องการแจ้งเตือน เช่น เมื่อทำงานเสร็จ
sound_alert(2)
```

### เพิ่มการบันทึกข้อมูล

```python
# เพิ่มในส่วนของ imports
import csv
from datetime import datetime

# เพิ่มฟังก์ชั่นบันทึกข้อมูล
def log_data(temp, target, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('temperature_log.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, temp, target, status])

# เรียกใช้ในลูปการทำงาน
log_data(current_temp, target_temp, "running" if running else "stopped")
```

### เพิ่มการควบคุมผ่านเว็บ

1. ติดตั้ง Flask:

```bash
sudo pip3 install flask
```

2. สร้างไฟล์เว็บเซิร์ฟเวอร์:

```python
from flask import Flask, render_template, request, jsonify
import threading
import time

app = Flask(__name__)

# ตัวแปรสถานะ (เชื่อมต่อกับตัวแปรในโปรแกรมหลัก)
# ...

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify({
        'temperature': current_temp,
        'target': target_temp,
        'running': running,
        'remaining': remaining_time
    })

@app.route('/api/control', methods=['POST'])
def control():
    global target_temp, duration
    
    if 'target' in request.json:
        target_temp = float(request.json['target'])
    
    if 'duration' in request.json:
        duration = int(request.json['duration'])
    
    if 'action' in request.json:
        if request.json['action'] == 'start':
            start_heating()
        elif request.json['action'] == 'stop':
            stop_heating()
    
    return jsonify({'success': True})

def web_server():
    app.run(host='0.0.0.0', port=8080)

# เริ่มเว็บเซิร์ฟเวอร์ในเธรดแยก
server_thread = threading.Thread(target=web_server)
server_thread.daemon = True
server_thread.start()
```

## ข้อควรระวัง

1. **ความปลอดภัยทางไฟฟ้า**: ระบบนี้ทำงานกับไฟฟ้าแรงดันสูง ควรติดตั้งโดยผู้เชี่ยวชาญเท่านั้น
2. **การระบายความร้อน**: ตรวจสอบให้แน่ใจว่ามีการระบายความร้อนที่เพียงพอสำหรับตู้ควบคุม
3. **อุณหภูมิ**: ระวังอย่าให้ Raspberry Pi สัมผัสกับความร้อนสูงเกินไป
4. **การสำรองข้อมูล**: ควรสำรองข้อมูลไว้ในกรณีที่ SD Card เสียหาย

## สรุป

ระบบตู้อบลมร้อนอัตโนมัติที่ควบคุมด้วย Raspberry Pi 5 นี้สามารถใช้ควบคุมอุณหภูมิและเวลาในการอบได้อย่างแม่นยำ ทำให้ผลลัพธ์ที่ได้มีคุณภาพสม่ำเสมอ นอกจากนี้ยังสามารถปรับแต่งเพิ่มเติมได้ตามความต้องการ เช่น เพิ่มระบบแจ้งเตือน การบันทึกข้อมูล หรือการควบคุมผ่านเว็บ

การใช้งานระบบนี้จะช่วยประหยัดเวลาและลดข้อผิดพลาดที่อาจเกิดจากการควบคุมด้วยมือ
