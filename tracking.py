import os
import time
import cv2
import math
import serial
import mediapipe as mp

# ==========================================
# CONFIGURATION
# ==========================================
# 1. Update this to match your ESP32's port!
COM_PORT = "COM5" 
BAUD_RATE = 115200

# 2. Make sure this file is in the same directory as your script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, 'hand_landmarker.task')

# ==========================================
# SERIAL SETUP
# ==========================================
try:
    arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # Give ESP32 a moment to reset after connecting
    print(f"Successfully connected to ESP32 on {COM_PORT}!")
except Exception as e:
    print(f"WARNING: Could not connect to {COM_PORT}. Running in vision-only mode.")
    arduino = None

# ==========================================
# MEDIAPIPE SETUP
# ==========================================
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode

latest_result = None

def print_result(result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global latest_result
    latest_result = result

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,
    num_hands=1, # Restrict to 1 hand for performance and clarity
    result_callback=print_result
)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def map_range(value, in_min, in_max, out_min, out_max):
    """Maps a value from one range to another, with clamping."""
    mapped = (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return int(max(min(mapped, max(out_min, out_max)), min(out_min, out_max)))

def draw_hand_landmarks(frame, hand_landmarks):
    """Draws dots and connecting lines on the hand."""
    height, width = frame.shape[:2]
    points = []
    
    for landmark in hand_landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        points.append((x, y))
        cv2.circle(frame, (x, y), 4, (255, 0, 0), -1)

    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),       # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),       # Index
        (5, 9), (9, 10), (10, 11), (11, 12),  # Middle
        (9, 13), (13, 14), (14, 15), (15, 16),# Ring
        (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
        (0, 17)                               # Palm base
    ]
    
    for start, end in connections:
        if start < len(points) and end < len(points):
            cv2.line(frame, points[start], points[end], (0, 255, 0), 2)

# ==========================================
# MAIN LOOP
# ==========================================
with HandLandmarker.create_from_options(options) as landmarker:
    cap = cv2.VideoCapture(1) # Change to 1 if using an external USB camera
    last_timestamp_ms = 0
    
    # Finger Landmark Pairs: (Tip, Base)
    finger_pairs = [
        (4, 2),   # Thumb
        (8, 5),   # Index
        (12, 9),  # Middle
        (16, 13), # Ring
        (20, 17)  # Pinky
    ]
    
    print("Press 'ESC' to exit.")

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue
            
        # Optimize image processing
        image.flags.writeable = False
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # Ensure strict monotonically increasing timestamps
        current_timestamp_ms = int(time.monotonic() * 1000)
        if current_timestamp_ms <= last_timestamp_ms:
            current_timestamp_ms = last_timestamp_ms + 1
        last_timestamp_ms = current_timestamp_ms
        
        # Run detection
        landmarker.detect_async(mp_image, current_timestamp_ms)
        
        image.flags.writeable = True
        
        # Process the results
        if latest_result and latest_result.hand_landmarks:
            for hand_landmarks in latest_result.hand_landmarks:
                draw_hand_landmarks(image, hand_landmarks)
                
                # Calculate palm size for normalization (Distance from Wrist 0 to Middle Base 9)
                wrist = hand_landmarks[0]
                middle_base = hand_landmarks[9]
                palm_size = math.hypot(middle_base.x - wrist.x, middle_base.y - wrist.y)
                
                # Prevent division by zero if palm size is perfectly 0 (rare but possible)
                if palm_size == 0:
                    palm_size = 0.001 
                
                servo_angles = []
                
                for tip_idx, base_idx in finger_pairs:
                    tip = hand_landmarks[tip_idx]
                    base = hand_landmarks[base_idx]
                    
                    # 1. Get raw distance between tip and base
                    raw_distance = math.hypot(tip.x - base.x, tip.y - base.y)
                    
                    # 2. Normalize it (makes it immune to how close you are to camera)
                    normalized_distance = raw_distance / palm_size
                    
                    # 3. Map to Servo Angle
                    # Normalization means: 
                    # ~1.0 = Finger is fully open (Tip is far from base)
                    # ~0.2 = Finger is fully closed (Tip is curled in)
                    # We map: Open (1.0) -> 0 degrees, Closed (0.2) -> 180 degrees
                    angle = map_range(normalized_distance, 1.0, 0.2, 0, 180)
                    servo_angles.append(str(angle))
                
                # Format string: "Thumb,Index,Middle,Ring,Pinky\n"
                serial_string = ",".join(servo_angles) + "\n"
                
                # Send to ESP32
                if arduino and arduino.is_open:
                    arduino.write(serial_string.encode())
                
                # Print to terminal
                print(f"Sent: {serial_string.strip()} | Palm Size: {palm_size:.3f}")

        # Display the webcam feed (flipped horizontally for a mirror effect)
        cv2.imshow('Hand Control', cv2.flip(image, 1))
        
        if cv2.waitKey(1) & 0xFF == 27: # Press ESC to break
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    if arduino:
        arduino.close()