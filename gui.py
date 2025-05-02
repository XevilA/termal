import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import time
import RPi.GPIO as GPIO
import Adafruit_DHT
from w1thermsensor import W1ThermSensor # สำหรับ DS18B20

# --- การตั้งค่าฮาร์ดแวร์ ---
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4        # ตั้งค่า GPIO pin สำหรับ DHT22 data
HEATER_PIN = 17    # ตั้งค่า GPIO pin สำหรับควบคุม Heater Relay
FAN_PIN = 27       # ตั้งค่า GPIO pin สำหรับควบคุม Fan Relay
# DS18B20 จะถูกค้นหาอัตโนมัติโดย w1thermsensor

# ตั้งค่าโหมด GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) # ปิดคำเตือน GPIO

# ตั้งค่า Output pins สำหรับ Heater และ Fan
GPIO.setup(HEATER_PIN, GPIO.OUT, initial=GPIO.LOW) # เริ่มต้น Heater ปิด
GPIO.setup(FAN_PIN, GPIO.OUT, initial=GPIO.LOW)    # เริ่มต้น Fan ปิด

# ตัวแปร Global สำหรับควบคุม Thread และสถานะ
control_active = False
control_thread = None
target_temp_global = 0.0
duration_seconds_global = 0

# --- ฟังก์ชันฮาร์ดแวร์ ---
def read_dht22():
    """อ่านค่าอุณหภูมิและความชื้นจาก DHT22"""
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if temperature is not None:
        return temperature
    else:
        print("เกิดข้อผิดพลาดในการอ่านค่า DHT22")
        return None # หรือค่าอื่นที่บ่งบอกว่าผิดพลาด

def read_ds18b20():
    """อ่านค่าอุณหภูมิจาก DS18B20 ตัวแรกที่พบ"""
    try:
        sensor = W1ThermSensor() # ค้นหาเซ็นเซอร์อัตโนมัติ
        temperature = sensor.get_temperature()
        return temperature
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการอ่านค่า DS18B20: {e}")
        return None

def heater_on():
    """เปิด Heater"""
    GPIO.output(HEATER_PIN, GPIO.HIGH)
    print("Heater ON")

def heater_off():
    """ปิด Heater"""
    GPIO.output(HEATER_PIN, GPIO.LOW)
    print("Heater OFF")

def fan_on():
    """เปิด Fan"""
    GPIO.output(FAN_PIN, GPIO.HIGH)
    print("Fan ON")

def fan_off():
    """ปิด Fan"""
    GPIO.output(FAN_PIN, GPIO.LOW)
    print("Fan OFF")

# --- ฟังก์ชันควบคุมหลัก (ทำงานใน Thread แยก) ---
def control_loop():
    """ลอจิกการควบคุมอุณหภูมิ"""
    global control_active, target_temp_global, duration_seconds_global

    start_time = time.time()
    end_time = start_time + duration_seconds_global

    print(f"เริ่มการควบคุม: เป้าหมาย={target_temp_global}°C, ระยะเวลา={duration_seconds_global/3600:.1f} ชม.")

    while control_active and time.time() < end_time:
        current_temp_dht = read_dht22()
        current_temp_ds = read_ds18b20() # อ่านค่า DS18B20 ด้วย

        if current_temp_dht is not None:
            # อัปเดต GUI (ใช้ window.after เพื่อความปลอดภัยของ Thread)
            window.after(0, update_gui_temps, current_temp_dht, current_temp_ds)

            # ลอจิกควบคุม Heater
            if current_temp_dht < target_temp_global:
                heater_on()
            else:
                heater_off()

            # (ตัวอย่าง: เพิ่มลอจิกควบคุมพัดลมที่นี่ ถ้าต้องการ)
            # if current_temp_dht > target_temp_global + 2: # เช่น เปิดพัดลมถ้าอุณหภูมิสูงกว่าเป้าหมาย 2 องศา
            #     fan_on()
            # else:
            #     fan_off()

        else:
            # หากอ่านค่า DHT22 ไม่ได้ ให้ปิด Heater เพื่อความปลอดภัย
            heater_off()
            print("ไม่สามารถอ่านค่า DHT22, หยุดการทำงาน Heater ชั่วคราว")

        time.sleep(2) # หน่วงเวลา 2 วินาที ก่อนวนรอบถัดไป

    # สิ้นสุดการทำงาน (หมดเวลา หรือ ถูกสั่งหยุด)
    heater_off()
    fan_off()
    control_active = False
    print("สิ้นสุดการควบคุม")
    # อัปเดต GUI เพื่อเปิดใช้งานปุ่มและ Combobox อีกครั้ง
    window.after(0, enable_controls)
    # แสดงข้อความเมื่อทำงานเสร็จ
    messagebox.showinfo("เสร็จสิ้น", "กระบวนการควบคุมอุณหภูมิเสร็จสิ้นแล้ว")


# --- ฟังก์ชัน GUI ---
def update_gui_temps(dht_temp, ds_temp):
    """อัปเดต Label อุณหภูมิใน GUI"""
    if dht_temp is not None:
        label_current_temp_dht.config(text=f"{dht_temp:.2f} °C")
    else:
        label_current_temp_dht.config(text="Error")

    if ds_temp is not None:
        label_current_temp_ds.config(text=f"{ds_temp:.2f} °C")
    else:
        label_current_temp_ds.config(text="Error")

def start_process():
    """เมื่อกดปุ่ม Start"""
    global control_active, control_thread, target_temp_global, duration_seconds_global

    if control_active:
        messagebox.showwarning("กำลังทำงาน", "ระบบกำลังทำงานอยู่")
        return

    try:
        target_temp_str = combo_target_temp.get()
        work_hours_str = combo_work_hours.get()

        if not target_temp_str or not work_hours_str:
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณาเลือกอุณหภูมิและระยะเวลาให้ครบถ้วน")
            return

        target_temp_global = float(target_temp_str)
        duration_hours = int(work_hours_str)
        duration_seconds_global = duration_hours * 3600 # แปลงชั่วโมงเป็นวินาที

        info = f"ตั้งอุณหภูมิเป้าหมาย: {target_temp_global} °C\n" \
               f"เวลาทำงาน: {duration_hours} ชั่วโมง"
        # messagebox.showinfo("ข้อมูลการทำงาน", info) # แสดงข้อมูลก่อนเริ่มก็ได้

        # ปิดการใช้งานปุ่มและ Combobox ขณะทำงาน
        disable_controls()

        # เริ่ม Thread การควบคุม
        control_active = True
        control_thread = threading.Thread(target=control_loop, daemon=True) # daemon=True เพื่อให้ thread ปิดตามโปรแกรมหลัก
        control_thread.start()

    except ValueError:
        messagebox.showerror("ข้อผิดพลาด", "ค่าอุณหภูมิหรือเวลาไม่ถูกต้อง")
        enable_controls() # เปิดใช้งาน control หากมีข้อผิดพลาด

def stop_process():
    """(ทางเลือก) เมื่อกดปุ่ม Stop"""
    global control_active
    if control_active:
        control_active = False # ส่งสัญญาณให้ Thread หยุดทำงาน
        print("กำลังหยุดการทำงาน...")
        # ไม่ต้องรอ thread join เพราะ heater/fan จะถูกปิดใน loop สุดท้าย หรือตอน cleanup
        # enable_controls() # จะถูกเรียกจาก control_loop เมื่อจบ
    else:
        messagebox.showinfo("สถานะ", "ระบบไม่ได้กำลังทำงาน")


def disable_controls():
    """ปิดการใช้งานปุ่มและ Combobox"""
    btn_start.config(state="disabled", bg="#cccccc")
    # btn_stop.config(state="normal", bg="#ff6347") # เปิดใช้งานปุ่ม Stop (ถ้ามี)
    combo_target_temp.config(state="disabled")
    combo_work_hours.config(state="disabled")

def enable_controls():
    """เปิดการใช้งานปุ่มและ Combobox"""
    btn_start.config(state="normal", bg="#32cd32")
    # btn_stop.config(state="disabled", bg="#cccccc") # ปิดใช้งานปุ่ม Stop (ถ้ามี)
    combo_target_temp.config(state="readonly")
    combo_work_hours.config(state="readonly")

def on_closing():
    """ฟังก์ชันเมื่อปิดหน้าต่าง GUI"""
    global control_active
    if control_active:
        if messagebox.askokcancel("ปิดโปรแกรม", "ระบบกำลังทำงานอยู่ ต้องการปิดโปรแกรมและหยุดการทำงานหรือไม่?"):
            control_active = False # ส่งสัญญาณให้ Thread หยุด
            # รอสักครู่เพื่อให้ thread มีโอกาสปิด heater/fan ก่อน cleanup
            time.sleep(0.5)
            GPIO.cleanup() # ทำความสะอาด GPIO
            window.destroy()
        else:
            return # ไม่ปิดโปรแกรม
    else:
        GPIO.cleanup() # ทำความสะอาด GPIO
        window.destroy()

# --- สร้างหน้าต่างหลัก GUI ---
window = tk.Tk()
window.title("Temperature Control System (RPi)")
window.geometry("500x500") # ขยายขนาดหน้าต่างเล็กน้อย
window.configure(bg="#f0f8ff")

# หัวข้อหลัก
label_header = tk.Label(window, text="Temperature Control", font=("Helvetica", 20, "bold"), bg="#f0f8ff", fg="#333")
label_header.pack(pady=15)

# --- แสดงอุณหภูมิปัจจุบัน ---
frame_temps = tk.Frame(window, bg="#f0f8ff")
frame_temps.pack(pady=10)

# DHT22 Temperature Display
frame_dht = tk.Frame(frame_temps, bg="#f0f8ff", bd=1, relief="solid")
frame_dht.pack(side="left", padx=10, pady=5)
tk.Label(frame_dht, text="อุณหภูมิ DHT22", font=("Arial", 14), bg="#f0f8ff").pack(pady=(5,0))
label_current_temp_dht = tk.Label(frame_dht, text="-- °C", font=("Arial", 24, "bold"), fg="red", bg="#f0f8ff", width=7)
label_current_temp_dht.pack(pady=(0,10), padx=10)

# DS18B20 Temperature Display
frame_ds = tk.Frame(frame_temps, bg="#f0f8ff", bd=1, relief="solid")
frame_ds.pack(side="left", padx=10, pady=5)
tk.Label(frame_ds, text="อุณหภูมิ DS18B20", font=("Arial", 14), bg="#f0f8ff").pack(pady=(5,0))
label_current_temp_ds = tk.Label(frame_ds, text="-- °C", font=("Arial", 24, "bold"), fg="blue", bg="#f0f8ff", width=7)
label_current_temp_ds.pack(pady=(0,10), padx=10)

# --- กรอบตั้งค่า ---
frame_settings = tk.Frame(window, bg="#e0f0ff", bd=2, relief="groove") # เพิ่มกรอบให้ส่วนตั้งค่า
frame_settings.pack(pady=15, padx=20, fill="x")

# กรอบตั้งอุณหภูมิ
frame_temp_set = tk.Frame(frame_settings, bg="#e0f0ff")
frame_temp_set.pack(pady=10, fill="x", padx=10)
tk.Label(frame_temp_set, text="อุณหภูมิเป้าหมาย (°C):", font=("Arial", 12), bg="#e0f0ff").pack(side="left", padx=5)
combo_target_temp = ttk.Combobox(frame_temp_set, values=[70, 80, 90, 100, 110, 120], font=("Arial", 12), width=5, state="readonly")
combo_target_temp.pack(side="left")
combo_target_temp.set("90") # ตั้งค่าเริ่มต้น

# กรอบตั้งชั่วโมงทำงาน
frame_hours_set = tk.Frame(frame_settings, bg="#e0f0ff")
frame_hours_set.pack(pady=10, fill="x", padx=10)
tk.Label(frame_hours_set, text="เวลาทำงาน (ชั่วโมง):", font=("Arial", 12), bg="#e0f0ff").pack(side="left", padx=5)
combo_work_hours = ttk.Combobox(frame_hours_set, values=[1, 2, 3, 4, 5, 6, 7, 8], font=("Arial", 12), width=5, state="readonly")
combo_work_hours.pack(side="left")
combo_work_hours.set("1") # ตั้งค่าเริ่มต้น

# --- ปุ่มควบคุม ---
frame_buttons = tk.Frame(window, bg="#f0f8ff")
frame_buttons.pack(pady=20)

# ปุ่มเริ่มทำงาน
btn_start = tk.Button(frame_buttons, text="เริ่มทำงาน", font=("Arial", 14, "bold"), bg="#32cd32", fg="white", padx=15, pady=5, command=start_process)
btn_start.pack(side="left", padx=10)

# (ทางเลือก) ปุ่มหยุดทำงาน - ยกเลิกคอมเมนต์ถ้าต้องการใช้งาน
# btn_stop = tk.Button(frame_buttons, text="หยุดทำงาน", font=("Arial", 14, "bold"), bg="#cccccc", fg="white", padx=15, pady=5, command=stop_process, state="disabled")
# btn_stop.pack(side="left", padx=10)

# --- เริ่มต้นการทำงาน ---
# ฟังก์ชันอัพเดตอุณหภูมิเริ่มต้น (อ่านค่าครั้งแรก)
def initial_temp_update():
    temp_dht = read_dht22()
    temp_ds = read_ds18b20()
    update_gui_temps(temp_dht, temp_ds)

initial_temp_update() # เรียกใช้เพื่อแสดงค่าเริ่มต้นทันที

# จัดการการปิดหน้าต่าง
window.protocol("WM_DELETE_WINDOW", on_closing)

# เริ่มลูป GUI หลัก
window.mainloop()
