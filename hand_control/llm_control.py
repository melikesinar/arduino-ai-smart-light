import os
import time
import serial
from google import genai


# --------------------------------------------------
# AYARLAR
# --------------------------------------------------

COM_PORT = "COM6"
BAUD_RATE = 9600

# SENDE ÇALIŞAN MODEL NEYSE ONU BURAYA YAZ
MODEL = "gemini-3.8-flash"


# --------------------------------------------------
# GEMINI
# --------------------------------------------------

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("GEMINI_API_KEY bulunamadi!")
    exit()

client = genai.Client(api_key=api_key)


# --------------------------------------------------
# ARDUINO
# --------------------------------------------------

ser = serial.Serial(COM_PORT, BAUD_RATE)

time.sleep(2)

print("Arduino baglantisi hazir.")


# --------------------------------------------------
# SISTEM TALIMATI
# --------------------------------------------------

SYSTEM_PROMPT = """
Sen normal bir sohbet asistanisin.

Ayni zamanda kullanicinin lamba kontrol komutlarini anlayabilirsin.

Her cevabini MUTLAKA su formatta ver:

ACTION: 1
REPLY: cevabin

veya:

ACTION: 0
REPLY: cevabin

veya:

ACTION: NONE
REPLY: cevabin


ACTION kurallari:

1 = Kullanici lambanin/isigin acilmasini istiyor.
0 = Kullanici lambanin/isigin kapanmasini istiyor.
NONE = Lamba ile ilgili herhangi bir eylem gerekmiyor.


Dolayli ifadeleri de anlayabilirsin.

Ornek:

Kullanici: Lambayi yak
ACTION: 1
REPLY: Tabii, lambayi aciyorum.

Kullanici: Ortam cok karanlik
ACTION: 1
REPLY: Haklisin, biraz aydinlatalim.

Kullanici: Isigi sondur
ACTION: 0
REPLY: Tabii, isigi kapatiyorum.

Kullanici: Cok aydinlik oldu
ACTION: 0
REPLY: Tamam, lambayi kapatiyorum.

Kullanici: Cok acim
ACTION: NONE
REPLY: Bir seyler yemek iyi gelebilir. Ne tarz bir sey yemek istiyorsun?

Kullanici: Bugun hava nasil?
ACTION: NONE
REPLY: Hava durumunu ogrenmek icin konum bilgisi gerekir.


Normal sohbet sorularina normal sekilde cevap ver.

Onemli:
ACTION satiri her zaman sadece 1, 0 veya NONE olmali.
REPLY satirinda kullaniciya verecegin normal cevabi yaz.
"""


# --------------------------------------------------
# CHAT OTURUMU
# --------------------------------------------------

chat = client.chats.create(
    model=MODEL,
    config={
        "system_instruction": SYSTEM_PROMPT
    }
)


# --------------------------------------------------
# GEMINI CEVABINI AYRISTIR
# --------------------------------------------------

def parse_response(text):

    action = "NONE"
    reply = text

    lines = text.strip().splitlines()

    reply_lines = []
    reading_reply = False

    for line in lines:

        if line.startswith("ACTION:"):

            value = line.replace("ACTION:", "").strip()

            if value in ["1", "0", "NONE"]:
                action = value

        elif line.startswith("REPLY:"):

            reading_reply = True
            reply_lines.append(
                line.replace("REPLY:", "", 1).strip()
            )

        elif reading_reply:

            reply_lines.append(line)

    if reply_lines:
        reply = "\n".join(reply_lines).strip()

    return action, reply


# --------------------------------------------------
# PROGRAM
# --------------------------------------------------

print()
print("--------------------------------")
print("Gemini + Arduino Asistani")
print("--------------------------------")
print("Cikmak icin: exit")
print()


while True:

    user_text = input("Sen: ").strip()

    if user_text.lower() in [
        "exit",
        "quit",
        "cik",
        "çık"
    ]:
        break

    if not user_text:
        continue

    try:

        # AYNI CHAT KULLANILIYOR
        # Bu yüzden önceki mesajları hatırlıyor
        response = chat.send_message(user_text)

        raw_answer = response.text.strip()

        action, reply = parse_response(raw_answer)

        print()
        print("Gemini:", reply)


        # ------------------------------------------
        # ARDUINO KOMUTU
        # ------------------------------------------

        if action == "1":

            ser.write(b"1")
            print("[Arduino] Lamba acildi.")

        elif action == "0":

            ser.write(b"0")
            print("[Arduino] Lamba kapatildi.")

        # NONE ise Arduino'ya hiçbir şey gönderme


        print()

    except Exception as e:

        print("Hata:", e)


ser.close()

print("Program kapatildi.")