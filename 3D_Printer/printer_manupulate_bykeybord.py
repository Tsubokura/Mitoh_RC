import serial
import threading
import time
from pynput.keyboard import Key, Listener

# シリアルポート設定
ser = serial.Serial("/dev/cu.wchusbserial120", 115200, timeout=1, write_timeout=1)

# 移動量設定
MOVE_DISTANCE = 100  # 通常の移動距離
MOVE_VEROCITY = 100  # 通常の移動速度
FACTOR = 10         # SHIFTキー押下時の倍率

# シリアル送信用バッファ
COMMAND_BUFFER_MAX = 5
command_buffer = 0

def serial_send(gcode):
    global command_buffer
    while command_buffer >= COMMAND_BUFFER_MAX:
        time.sleep(0.01)
    
    command_buffer += 1
    ser.write((gcode + '\r\n').encode('utf-8'))
    print(f"Sent Gcode: {gcode}")

def on_press(key):
    move = None
    shift_pressed = False

    if hasattr(key, 'char') and key.char in ['w', 's', 'a', 'd']:
        direction = key.char
    elif key == Key.shift:
        shift_pressed = True
    else:
        return

    if direction in ['w', 's']:
        axis = 'Z'
        if direction == 'w':
            verocity = MOVE_DISTANCE
        else:
            verocity = -MOVE_DISTANCE
    elif direction in ['a', 'd']:
        axis = 'X'
        if direction == 'a':
            verocity = -MOVE_DISTANCE
        else:
            verocity = MOVE_DISTANCE

    if shift_pressed:
        verocity *= FACTOR

    distance = MOVE_DISTANCE

    move = f"G1 {axis}{distance} F{verocity}"
    print("generate Gcode" + move)
    serial_send(move)

def on_release(key):
    if key == Key.esc:
        return False  # Stop listener

def start_keyboard_listener():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def serial_read():
    global command_buffer
    while True:
        try:
            data = ser.readline()
            if data:
                ret = data.decode('utf-8').strip()
                print(f"Received from printer: {ret}")
                if "ok" in ret:
                    command_buffer = max(command_buffer - 1, 0)
        except serial.SerialException:
            print("SerialException occurred, stopping read")
            return
        except TypeError:
            print("Disconnect occurred, closing port")
            ser.close()
            return

# スレッド処理
def start_reading():
    threading.Thread(target=serial_read).start()

if __name__ == "__main__":
    start_reading()
    start_keyboard_listener()
