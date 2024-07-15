import serial
from serial.tools import list_ports
import threading
import time,datetime

COMMAND_BUFFER_MAX = 5
event = threading.Event()
command_buffer = 0

ser = serial.Serial("/dev/cu.wchusbserial120", 115200) 
ser.timeout = 1
ser.write_timeout = 1

ser.baudrate = 115200 # 3Dプリンタによるけど大体これ
gcode_printing = [] # 造形中のGcode

# 造形対象のGcode
gcode = [
"G28",
"G1 F1000"
]

# gcode = [
# "G28",
# "G1 F1000",
# "G1 X50",
# "G1 Y50",
# "G1 X100 Y100",
# "M84"
# ]

# 3Dプリンタに接続
def connect():
    ports = list_ports.comports()    # ポートデータを取得
    devices = [info.device for info in ports]
    print(ports)

    if len(devices) == 0:
        print("error: device not found")
        return None
    elif len(devices) == 1:
        print("only found %s" % devices[0])
        ser.port = devices[0]
    else:
        for i in range(len(devices)):
            print("input %3d: open %s" % (i,devices[i]))
        print("input number of target port >> ",end="")
        num = 0 #int(input())
        ser.port = devices[num]

    try:
        ser.open()
        print("serial open!")
        return ser
    except:
        print("error when opening serial")
        return None

# 造形プロセス制御 ================================
def printing():
    global command_buffer

    # リストを一度コピーしてそこから順番に取り出す
    gcode_printing = list(gcode)

    # ここの部分
    while len(gcode_printing) > 0:
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
            print(data)
        except serial.SerialException as e:
            # There is no new data from serial port
            return None
            pass
        except TypeError as e:
            # Disconnect of USB->UART occured
            ser.port.close()
            return None
        
        if data != b'':
            ret = data.decode('utf-8')
            ret = ret.strip()
            print(datetime.datetime.now(), " <<< RECV ", ret)

            # 命令を処理し終えたら "ok" が返ってくる
            if ret.find("ok") != -1:
                command_buffer -= 1
                if command_buffer < 0:
                    command_buffer = 0
 
    # シリアル送信 ================================
def serial_send(data: str):
    global command_buffer

    data = data.strip()

    # 送信する必要のないGcodeの場合
    # ; 以降はコメント部分
    if len(data) == 0:
        return
    if data.find(";") == 0:
        return
    pos = data.find(";")

    # コメント以降を取り除く
    if pos != -1:
        data = data[:pos]

    # byte型に
    data = bytes(data+ "\r", encoding = "utf-8")

    start_time = time.time()
    while True:
        time.sleep(0.01)

        if command_buffer < COMMAND_BUFFER_MAX:
            command_buffer += 1
         
            try:
                ser.write(data)

            except serial.SerialException as e:
                #There is no new data from serial port
                print("E - serial.SerialException when sending")
                return None

            except TypeError as e:
                #Disconnect of USB->UART occured
                print("E - Type error when sending")
                ser.port.close()
                return None
            
            print(datetime.datetime.now(),   " SEND >>> ", data.decode('utf-8').strip())
            
            return True
        
        # 適当にタイムアウト処理
        if time.time() - start_time > 100:
            print("Time out")
            command_buffer -= 1
            print(data.decode('utf-8'))
            break

    return False

# スレッド処理
# シリアルの情報を読み続ける
def start_reading():
    thread_read = threading.Thread(target=serial_read)
    thread_read.start()

# スレッド処理
def start_printing():
    thread_print = threading.Thread(target=printing)
    thread_print.start()


# メイン関数
if __name__ == "__main__":
    connect()

    # プリンタからの応答を出力し続ける
    start_reading()
    # リストgcodeの内容を送り続ける
    start_printing()
