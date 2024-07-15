import serial
import threading
import time
import datetime

COMMAND_BUFFER_MAX = 5
command_buffer = 0

# 直接指定されたポートとボーレートでシリアル接続を設定
ser = serial.Serial("/dev/cu.wchusbserial120", 115200, timeout=1, write_timeout=1)

# 造形対象のGcode
# gcode = [
# "G28",
# "G1 F1000",
# "G1 X50",
# "G1 Y50",
# "G1 X100 Y100",
# "M84"
# ]

gcode = [
"G28",
"G1 X100 F1000",
"G1 X50 F500",
"M84"
]

# gcode = [
# "G28",
# "G1 F1000",
# "G1 Z100",
# "G1 X100",
# "M84"
# ]




# 3Dプリンタに接続
def connect():
    try:
        # ser.open()
        print("Serial port opened!")
    except Exception as e:
        print(f"Error when opening serial port: {e}")
        return None
    return ser

# 造形プロセス制御
def printing():
    global command_buffer
    gcode_printing = list(gcode)  # コピーしてから処理

    while gcode_printing:
        g = gcode_printing.pop(0)
        serial_send(g.strip())

    print("DONE")
    command_buffer = 0

# シリアル読み込み
def serial_read():
    global command_buffer

    while True:
        time.sleep(0.001)
        try:
            data = ser.readline()
            if data:
                ret = data.decode('utf-8').strip()
                print(datetime.datetime.now(), " <<< RECV ", ret)
                if "ok" in ret:
                    command_buffer -= 1
                    command_buffer = max(command_buffer, 0)
        except serial.SerialException:
            print("SerialException occurred, stopping read")
            return
        except TypeError:
            print("Disconnect occurred, closing port")
            ser.close()
            return

# シリアル送信
def serial_send(data: str):
    global command_buffer

    if not data or data.startswith(';'):
        return

    data = data.split(';')[0] + '\r'  # コメントを削除し、改行を追加
    start_time = time.time()

    while time.time() - start_time < 100:  # タイムアウト100秒
        if command_buffer < COMMAND_BUFFER_MAX:
            command_buffer += 1
            try:
                ser.write(data.encode('utf-8'))
                print(datetime.datetime.now(), " SEND >>> ", data.strip())
                return True
            except serial.SerialException:
                print("SerialException during send")
                return False
            except TypeError:
                print("Type error during send, closing port")
                ser.close()
                return False
        time.sleep(0.01)

    print("Time out")
    command_buffer -= 1
    return False

# スレッド処理
def start_reading():
    threading.Thread(target=serial_read).start()

def start_printing():
    threading.Thread(target=printing).start()

# メイン関数
if __name__ == "__main__":
    if connect():
        start_reading()
        start_printing()
