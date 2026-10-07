import os
import time
import serial
import speech_recognition as sr
from google import genai


# --------------------------------------------------
# AYARLAR
# --------------------------------------------------

COM_PORT = "COM6"
BAUD_RATE = 9600

# Sende çalışan Gemini modeli neyse onu kullan
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

Kurallar:

1 = Kullanici lambanin/isigin acilmasini istiyor.
0 = Kullanici lambanin/isigin kapanmasini istiyor.
NONE = Lamba ile ilgili herhangi bir eylem gerekmiyor.

Ornekler:

Kullanici: Lambayi ac
ACTION: 1
REPLY: Tabii, lambayi aciyorum.

Kullanici: Ortam cok karanlik
ACTION: 1
REPLY: Tabii, ortami aydinlatiyorum.

Kullanici: Isigi kapat
ACTION: 0
REPLY: Tabii, isigi kapatiyorum.

Kullanici: Cok acim
ACTION: NONE
REPLY: Bir seyler yemek iyi gelebilir.

Sadece ACTION satirinda 1, 0 veya NONE kullan.
"""


# --------------------------------------------------
# CHAT
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
# GEMINI RETRY
# --------------------------------------------------

def send_with_retry(user_text):

    delays = [2, 4, 8]

    for delay in delays:

        try:
            return chat.send_message(user_text)

        except Exception as e:

            error_text = str(e)

            if "503" in error_text or "UNAVAILABLE" in error_text:

                print(
                    f"Gemini yogun. "
                    f"{delay} saniye sonra tekrar deneniyor..."
                )

                time.sleep(delay)

            else:
                raise

    raise Exception("Gemini servisine ulasilamadi.")


# --------------------------------------------------
# SES TANIMA
# --------------------------------------------------

recognizer = sr.Recognizer()

microphone = sr.Microphone()


def listen():

    with microphone as source:

        print()
        print("Dinliyorum...")

        # Ortam gurultusunu kisa sure olcer
        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.7
        )

        try:

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

        except sr.WaitTimeoutError:

            print("Konusma algilanmadi.")
            return None


    try:

        text = recognizer.recognize_google(
            audio,
            language="tr-TR"
        )

        return text

    except sr.UnknownValueError:

        print("Ne soylediginizi anlayamadim.")
        return None

    except sr.RequestError as e:

        print("Speech Recognition hatasi:", e)
        return None


# --------------------------------------------------
# ANA PROGRAM
# --------------------------------------------------

print()
print("--------------------------------")
print("Sesli Gemini + Arduino Asistani")
print("--------------------------------")
print()
print("ENTER -> konus")
print("q     -> cik")
print()

try:
    while True:

        command = input(
            "\nKonusmak icin ENTER, cikmak icin q: "
        ).strip().lower()

        if command in ["q", "exit", "quit", "cik", "çık"]:
            print("Program kapatiliyor...")
            break

        user_text = listen()

        if not user_text:
            continue

        print()
        print("Algilanan metin:", user_text)

        try:
            response = send_with_retry(user_text)

            action, reply = parse_response(
                response.text.strip()
            )

            print("Gemini:", reply)

            if action == "1":
                ser.write(b"1")
                print("[Arduino] Lamba acildi.")

            elif action == "0":
                ser.write(b"0")
                print("[Arduino] Lamba kapatildi.")

            else:
                print("[Arduino] Islem yapilmadi.")

        except Exception as e:
            print("Hata:", e)

except KeyboardInterrupt:
    print("\nCtrl+C algilandi. Program kapatiliyor...")

finally:
    ser.close()
    print("Seri port kapatildi.")

   