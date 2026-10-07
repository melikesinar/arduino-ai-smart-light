const int RELAY_PIN = 7;

void setup() {
    pinMode(RELAY_PIN, OUTPUT);

    // Röle active-low olduğu için başlangıçta kapalı
    digitalWrite(RELAY_PIN, HIGH);

    // Python ile seri haberleşme
    Serial.begin(9600);
}

void loop() {
    if (Serial.available()) {

        char command = Serial.read();

        // Python "1" gönderirse röleyi aç
        if (command == '1') {
            digitalWrite(RELAY_PIN, LOW);
        }

        // Python "0" gönderirse röleyi kapat
        if (command == '0') {
            digitalWrite(RELAY_PIN, HIGH);
        }
    }
}