import serial
import time

# =========================
# CRC8 (Poly 0x8C)
# =========================
def crc8(data):
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x01:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
    return crc & 0xFF

# =========================
# 4byte little endian
# =========================
def to_4byte_le(value):
    return value.to_bytes(4, byteorder='little', signed=True)

# =========================
# パケット生成
# =========================
def make_packet(cmd, dev_id, d1=0, d2=0, d3=0):
    packet = bytearray()
    packet.append(cmd)
    packet.append(dev_id)
    packet += to_4byte_le(d1)
    packet += to_4byte_le(d2)
    packet += to_4byte_le(d3)
    packet.append(crc8(packet))
    return packet

# =========================
# 送受信表示
# =========================
def send_and_receive(ser, packet):
    print("TX:", " ".join(f"{b:02X}" for b in packet))
    ser.write(packet)
    ##time.sleep(0.05)
    response = ser.read(32)
    if response:
        print("RX:", " ".join(f"{b:02X}" for b in response))
    else:
        print("RX: no response")
    print("--------------------------------")

# =========================
# 設定
# =========================
PORT = "COM3"
MOTOR_IDS = [0, 1, 2, 3, 4]   # ←ID確認

ser = serial.Serial(PORT, 115200, timeout=0.5)
time.sleep(1)

# =========================
# ① 全モータON
# =========================
for dev in MOTOR_IDS:
    send_and_receive(ser, make_packet(0x00, dev, 1))

# =========================
# ② Positionモード
#    ※モード番号は仕様に合わせて変更
# =========================
for dev in MOTOR_IDS:
    send_and_receive(ser, make_packet(0x01, dev, 2))  # ←Positionモード：２

# =========================
# ③ 角度指令（0x22）
# Data1 = deg × 100
# Data2 = mA × 100　　最大電流
# Data3 = 0
# =========================
deg = 0
current_mA = 500

deg_value = deg * 100
current_value = current_mA * 100

for dev in MOTOR_IDS:
    send_and_receive(
        ser,
        make_packet(0x22, dev, deg_value, current_value, 0)
    )

print("All motors running at", deg, "deg")

time.sleep(5)

# =========================
# ⑤ OFF
# =========================
for dev in MOTOR_IDS:
    send_and_receive(ser, make_packet(0x00, dev, 0))

ser.close()
print("All motors stopped.")
