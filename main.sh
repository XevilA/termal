#!/bin/bash

# อัพเดท RPI
echo "กำลังอัปเดตระบบ RPI..."
sudo apt update -y
sudo apt upgrade -y

# ติดตั้ง dependencies ที่จำเป็น
echo "ติดตั้ง dependencies..."
sudo apt install python3-pip python3-dev python3-rpi.gpio -y

# ติดตั้งไลบรารีที่จำเป็นสำหรับเซ็นเซอร์และ LCD
echo "ติดตั้งไลบรารีที่จำเป็น..."
sudo pip3 uninstall -y RPi.GPIO  # ลบ RPi.GPIO รุ่นเก่า (ถ้ามี)
sudo pip3 install Adafruit_DHT --install-option="--force-pi"
sudo pip3 install adafruit-circuitpython-charlcd

# ให้คำแนะนำการติดตั้ง
echo "ติดตั้งเสร็จสิ้นแล้ว!"
echo "คุณสามารถเริ่มใช้งานระบบได้แล้ว!"

# แสดงคำแนะนำในการสร้าง Virtual Environment (ถ้าต้องการ)
echo "หากต้องการใช้ Virtual Environment, สามารถสร้างได้โดยใช้คำสั่ง:"
echo "python3 -m venv myenv"
echo "source myenv/bin/activate"
