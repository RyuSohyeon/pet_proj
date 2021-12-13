# 웹서버 프로그램 웹 브라우저에서 http://localhost:5000/로 접속하면 
# index.html을 실행하고 버튼을 이용하여 LED 작동시킴

from flask import Flask, request
from flask import render_template, Response
import RPi.GPIO as GPIO
import time
from picamera import camera
import spidev
import threading
from camera import Camera

app = Flask(__name__)
GPIO.setmode(GPIO.BCM)                   

# 초인종
btn_pin = 15
num = 0
GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(6, GPIO.OUT) # PWM 인스턴스 p를 만들고  GPIO 18번을 PWM 핀으로 설정, 주파수  = 100Hz
p = GPIO.PWM(6, 100)  
Frq = [ 392, 330 ] # 4옥타브 도~시 , 5옥타브 도의 주파수 
speed = 0.5 # 음과 음 사이 연주시간 설정 (0.5초)

# 조도센서
ldr_channel = 0
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 100000

# 모터 구현
m_pin = 18
GPIO.setup(m_pin, GPIO.OUT) 
servo = GPIO.PWM(m_pin, 50)         # Hz (서보모터 PWM 동작을 위한 주파수)
servo.start(0)

# LED 구현
led_pin = 16 
light = 0                   
move = 4                  
GPIO.setup(led_pin, GPIO.OUT, initial=GPIO.LOW) 

# 불필요한 warning 제거, GPIO핀의 번호 ah드 설정
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# 웹사이트
@app.route("/")
def home():
    return render_template('index.html')

# 초인종
def button_callback(channel):
    global num 
    if num == 0:
        for fr in Frq:
            print("fr")
            p.start(10)  # PWM 시작 , 듀티사이클 10 (충분
            p.ChangeFrequency(fr)    #주파수를 fr로 변경
            time.sleep(speed)       #speed 초만큼 딜레이 (0.5s)
        p.stop()   
GPIO.add_event_detect(btn_pin,GPIO.RISING,callback=button_callback, bouncetime=300)      

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/feed")
def feed():
    try:
        return "1"
    except:
        pass        

    return "0"

@app.route("/motor")
def motor():
    try:
        servo.start(0)
        servo.ChangeDutyCycle(7.5)         # 서보 모터를 90도로 회전
        time.sleep(1)
        servo.ChangeDutyCycle(12.5)          # 서보 모터를 180도로 회전
        time.sleep(1)
        return "ok" 
    except :
        servo.stop()
        return "fail"

@app.route("/led")
def led():
    adcnum = ldr_channel
    if adcnum > 7 or adcnum:
        ldr_value = -1
    else:
        r = spi.xfer2([1,8+adcnum<<4,0])
        data = ((r[1]&3)<<8)+r[2]
        ldr_value = data
    print("----------")
    print("LDR Value: %d" % ldr_value)
    time.sleep(0.5)
    if ldr_value < 400:
        try:
            GPIO.output(led_pin, GPIO.HIGH)
            return "ok"
        except :
            return "fail"
    else:
        try:
            GPIO.output(led_pin, GPIO.LOW)
            return "ok"
        except :
            return "fail"

@app.route("/bell")
def bell():
    global num
    if num == 0:
        try:
            num = 1
            return "ok"
        except :
            return "fail"
    elif num == 1:
        try:
            num = 0
            return "ok"
        except :
            return "fail"

if __name__ == "__main__":
    app.run(host="0.0.0.0")
   

