import cv2
import numpy as np
import RPi.GPIO as GPIO
import time

ENA = 17
IN1 = 27
IN2 = 22

ENB = 13
IN3 = 5
IN4 = 6

pos = [0, 0]

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)

GPIO.setup(ENB, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

speed_x = 5
speed_y = 5

pwmA = GPIO.PWM(ENA, speed_x)
pwmB = GPIO.PWM(ENB, speed_y)

pwmA.start(0)
pwmB.start(0)

def stop():
	pwmA.ChangeDutyCycle(0)
	pwmB.ChangeDutyCycle(0)

def up(speed):
	pwmA.ChangeDutyCycle(speed)
	GPIO.output(IN1, GPIO.HIGH)
	GPIO.output(IN2, GPIO.LOW)

def down(speed):
	pwmA.ChangeDutyCycle(speed)
	GPIO.output(IN1, GPIO.LOW)
	GPIO.output(IN2, GPIO.HIGH)

def right(speed):
	pwmB.ChangeDutyCycle(speed)
	GPIO.output(IN3, GPIO.HIGH)
	GPIO.output(IN4, GPIO.LOW)

def left(speed):
	pwmB.ChangeDutyCycle(speed)
	GPIO.output(IN3, GPIO.LOW)
	GPIO.output(IN4, GPIO.HIGH)

def detect_red(frame):
	hsv_frame = frame #cv2.cvtColor(frame), cv2.COLOR_BGR2RGB )

	lower_red = np.array([90, 90, 160])
	upper_red = np.array([130, 130, 190])

	red_mask = cv2.inRange(hsv_frame, lower_red, upper_red)

	red_mask = cv2.GaussianBlur(red_mask, (5, 5), 0)

	contours, _ = cv2.findContours(red_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	
	if contours:

		largest_contour = max(contours, key = cv2.contourArea)

		M = cv2.moments(largest_contour)
		if M["m00"] != 0:
			cx = int(M["m10"] / M["m00"])
			cy = int(M["m01"] / M["m00"])
			return (cx, cy), largest_contour
	return None, None

click_x = 0
click_y = 0

def click_event(event, x, y, flags, param):
	if event == cv2.EVENT_LBUTTONDOWN:
		global click_x
		global click_y
		cv2.circle(param, (x, y), 5, (0, 255, 0), 2)
		click_x = x
		click_y = y


cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
	print("Error")
	exit()

cv2.namedWindow("Red Point Tracking")

ret, frame = cap.read()
frame = frame[59:346, 121:406]

position, contour = detect_red(frame)

if position is not None:
	click_x, click_y = position

cv2.setMouseCallback("Red Point Tracking", click_event, param = frame)

while True:
	ret, frame = cap.read()

	frame = frame[59:346, 121:406]

	if not ret:
		print("Failed")
		break

	position, contour = detect_red(frame)

	if position is not None:
		cx, cy = position

		cv2.circle(frame, (cx, cy), 10, (0, 255, 0), 2)
		cv2.circle(frame, (click_x, click_y), 10, (255, 0, 0), 2)
		cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)

		error_x = abs(cx - click_x)
		error_y = abs(cy - click_y)

		speed_x = min(20, 3 + 0.25 * error_x)
		speed_y = min(20, 3 + 0.25 * error_y)


		if(cx > click_x + 2 or cx < click_x - 2):
			if cx < click_x:
				down(speed_x)
			elif cx > click_x:
				up(speed_x)
		else:
			stop()
			click_x = cx

		if(cy > click_y + 2 or cy < click_y - 2):
			if cy < click_y:
				right(speed_y)
			elif cy > click_y:
				left(speed_y)
		else:
			stop()
			click_y = cy

		#cv2.putText(frame, f"{cx}, {cy}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

	cv2.imshow("Red Point Tracking", frame)
	if cv2.waitKey(1) & 0xFF == ord("q"):
		break

cap.release()
cv2.destroyAllWindows()
