import serial
import time

# =========================
# CRC8
# =========================
def crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8C
            else:
                crc >>= 1
    return crc & 0xFF


# =========================
# little endian
# =========================
def to_4byte_le(val):
    return val.to_bytes(4, byteorder="little", signed=True)


def from_4byte_le(data):
    return int.from_bytes(data, byteorder="little", signed=True)


# =========================
# パケット生成
# =========================
def make_packet(cmd, dev, d1=0, d2=0, d3=0):

    pkt = bytearray()

    pkt.append(cmd)
    pkt.append(dev)

    pkt += to_4byte_le(d1)
    pkt += to_4byte_le(d2)
    pkt += to_4byte_le(d3)

    pkt.append(crc8(pkt))

    return pkt


# =========================
# status packet
# =========================
def make_status_packet(dev):

    pkt = bytearray([0x40, dev, 0x00])
    pkt.append(crc8(pkt))

    return pkt


# =========================
# 送信表示
# =========================
def send_packet(ser, pkt):

    print("TX:", " ".join(f"{b:02X}" for b in pkt))
    ser.write(pkt)


# =========================
# 状態解析
# =========================
def parse_status(rx):

    if len(rx) < 17:
        print("invalid packet")
        return

    rpm = from_4byte_le(rx[4:8]) / 100
    position = from_4byte_le(rx[8:12])
    current = from_4byte_le(rx[12:16]) / 100

    print(f"RPM     : {rpm} rpm")
    print(f"Current : {current} mA")
    print(f"Position: {position}")
    print("-----------------------")


# =========================
# 設定
# =========================
PORT = "COM3"
ID = 0

ser = serial.Serial(PORT,115200,timeout=0.5)

time.sleep(1)


# =========================
# モータON
# =========================
pkt = make_packet(0x00, ID, 1)
send_packet(ser, pkt)

ser.read(32)


# =========================
# speed mode
# =========================
pkt = make_packet(0x01, ID, 1)
send_packet(ser, pkt)

ser.read(32)


# =========================
# 100rpm
# =========================
rpm = 100
current = 500

pkt = make_packet(0x20, ID, rpm*100, current*100, 0)
send_packet(ser, pkt)

print("Motor running at", rpm, "rpm\n")


# =========================
# モニター
# =========================
for i in range(20):

    pkt = make_status_packet(ID)
    send_packet(ser, pkt)

    rx = ser.read(32)

    if rx:

        print("RX:", " ".join(f"{b:02X}" for b in rx))

        parse_status(rx)

    time.sleep(0.5)


# =========================
# stop
# =========================
pkt = make_packet(0x20, ID, 0, 0, 0)
send_packet(ser, pkt)

# =========================
# ⑤ OFF
# =========================
pkt = make_packet(0x00, ID, 0, 0, 0)
send_packet(ser, pkt)

ser.close()
