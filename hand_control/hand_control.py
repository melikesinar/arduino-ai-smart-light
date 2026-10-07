import cv2
import mediapipe as mp
import serial
import time

# --------------------------------
# AYARLAR
# --------------------------------

COM_PORT = "COM6"   # Arduino hangi porttaysa onu yaz
BAUD_RATE = 9600

# Hareketin kaç kare üst üste görülmesi gerektiği
STABLE_FRAMES = 5


# --------------------------------
# ARDUINO BAĞLANTISI
# --------------------------------

ser = serial.Serial(COM_PORT, BAUD_RATE)

# Arduino seri port açılınca reset atabileceği için biraz bekliyoruz
time.sleep(2)

print("Arduino baglantisi hazir.")


# --------------------------------
# MEDIAPIPE
# --------------------------------

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)


# --------------------------------
# KAMERA
# --------------------------------

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Kamera acilamadi!")
    ser.close()
    exit()


# Son Arduino'ya gönderilen durum
last_sent_state = None

# Şu anda doğrulanmaya çalışılan hareket
candidate_state = None

# Aynı hareketin kaç karedir görüldüğü
stable_count = 0


while True:

    success, frame = cap.read()

    if not success:
        print("Kamera goruntusu alinamadi.")
        break

    # Kamera görüntüsünü ayna gibi göster
    frame = cv2.flip(frame, 1)

    # OpenCV BGR, MediaPipe RGB kullanır
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    result = hands.process(rgb)

    detected_state = None
    finger_count = 0


    if result.multi_hand_landmarks:

        hand_landmarks = result.multi_hand_landmarks[0]

        # El üzerindeki noktaları ve bağlantıları çiz
        mp_draw.draw_landmarks(
            frame,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS
        )

        lm = hand_landmarks.landmark


        # --------------------------------
        # AÇIK PARMAKLARI SAY
        # --------------------------------

        # İşaret parmağı
        if lm[8].y < lm[6].y:
            finger_count += 1

        # Orta parmak
        if lm[12].y < lm[10].y:
            finger_count += 1

        # Yüzük parmağı
        if lm[16].y < lm[14].y:
            finger_count += 1

        # Serçe
        if lm[20].y < lm[18].y:
            finger_count += 1


        # --------------------------------
        # EL HAREKETİNİ BELİRLE
        # --------------------------------

        # 4 parmak açıksa açık avuç kabul et
        if finger_count >= 4:

            detected_state = "OPEN"

            cv2.putText(
                frame,
                "ACIK AVUC",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

        # Hiç parmak açık değilse yumruk
        elif finger_count == 0:

            detected_state = "CLOSED"

            cv2.putText(
                frame,
                "YUMRUK",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )


        cv2.putText(
            frame,
            f"Acik Parmak: {finger_count}",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )


    # --------------------------------
    # TITREME / YANLIŞ ALGILAMA ENGELLEME
    # --------------------------------

    if detected_state is not None:

        if detected_state == candidate_state:
            stable_count += 1

        else:
            candidate_state = detected_state
            stable_count = 1


        # Aynı hareket 5 kare üst üste görülürse kabul et
        if stable_count >= STABLE_FRAMES:

            # Sadece durum değiştiğinde Arduino'ya gönder
            if detected_state != last_sent_state:

                if detected_state == "OPEN":

                    ser.write(b"1")
                    print("1 gonderildi -> ROLE AC")

                elif detected_state == "CLOSED":

                    ser.write(b"0")
                    print("0 gonderildi -> ROLE KAPAT")


                last_sent_state = detected_state


    else:
        candidate_state = None
        stable_count = 0


    # Kamera görüntüsünü göster
    cv2.imshow("El Kontrol", frame)


    # Klavyeden Q basınca programı kapat
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# --------------------------------
# PROGRAM KAPANIRKEN
# --------------------------------

cap.release()
cv2.destroyAllWindows()
hands.close()
ser.close()

print("Program kapatildi.")