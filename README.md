
# Arduino AI Smart Light

AI-powered smart lighting system built with Arduino Mega, Python, MediaPipe, Gemini API, and speech recognition.

The project allows a relay-controlled light to be controlled using:

- Hand gestures
- Natural language commands
- Voice commands

---

## Features

- Arduino Mega based relay control
- Serial communication between Python and Arduino
- Hand gesture recognition with MediaPipe
- Webcam input with OpenCV
- Natural language understanding with Gemini
- Turkish voice command support
- Simple ON / OFF command protocol
- Basic conversation support with Gemini
- Protection against repeated gesture commands

---

## System Architecture

```text
User
 │
 ├── Hand Gesture
 │       ↓
 │   MediaPipe
 │
 ├── Voice
 │       ↓
 │ Speech Recognition
 │
 └── Text
         ↓
       Gemini
         ↓
       Python
         ↓
 Serial Communication
         ↓
   Arduino Mega
         ↓
      Relay
         ↓
      Light
