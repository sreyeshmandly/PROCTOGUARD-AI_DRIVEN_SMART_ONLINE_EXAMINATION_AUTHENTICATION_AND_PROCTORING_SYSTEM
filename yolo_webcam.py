import cv2
from ultralytics import YOLO
import numpy as np
import tkinter as tk
from tkinter import messagebox

# Load the saved YOLO model from your local system
model_path = 'yolov8_saved_model.pt' 
model = YOLO(model_path)  # Load the YOLO model


# Variables to track the previous x-coordinate and height of the person's head
previous_x = None
previous_height = None

# Function to show a pop-up alert for phone detection
def show_alert():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showinfo("Alert", "Cell Phone Detected!")
    root.destroy()

# Live webcam detection function
def live_webcam_detection():
    global previous_x, previous_height,cam  # Use the global variables to track across frames
    cam = cv2.VideoCapture(0)  # Use '0' for default webcam or adjust accordingly
    head_orientation = ""
    label="Null"

    print("Press 'q' to exit the webcam window")

    while cam.isOpened():
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Convert to RGB format for YOLO
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run YOLO model prediction on the frame
        results = model.predict(rgb_frame, stream=True)  # Use stream=True to iterate over results

        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get class ID and confidence score
                class_id = int(box.cls[0])  # Extract the class ID from the result
                confidence = float(box.conf[0])

                # Filter to only detect "person" (class_id == 0) and "cell phone" (class_id == 67)
                if class_id in [0, 67]:  # 0: person, 67: cell phone in COCO dataset
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Draw bounding box
                    color = (0, 255, 0) if class_id == 0 else (0, 0, 255)  # Green for person, red for cell phone
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    # Define label text based on the class
                    label = "" if class_id == 0 else "Cell Phone"
                    label_text = f"{label} {confidence:.2f}"

                    # Draw label text above the bounding box
                    cv2.putText(frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    # If the detected object is a person, perform head movement detection
                    if class_id == 0:
                        # Calculate the current x-coordinate of the head (use the center of the bounding box)
                        current_x = (x1 + x2) // 2

                        # Calculate the height of the bounding box
                        current_height = y2 - y1

                        # Determine head movement direction
                        head_orientation = "Straight"

                        # Determine left or right movement based on previous and current x-coordinates
                        if previous_x is not None:
                            if current_x > previous_x + 20:  # Threshold to avoid small jitters
                                head_orientation = "Right"
                            elif current_x < previous_x - 20:
                                head_orientation = "Left"

                        # Determine looking down movement based on height change
                        if previous_height is not None:
                            if current_height < previous_height - 15:  # Threshold to detect looking down
                                head_orientation = "Down"

                        # Update the previous x-coordinate and height
                        previous_x = current_x
                        previous_height = current_height

                        # Display head orientation on the frame
                        cv2.putText(frame, f"Head: {head_orientation}", (x1, y1 - 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                    # Alert when phone is detected
                    if class_id == 67:  # If the class is 'cell phone'
                        # show_alert()  # Trigger the alert function
                        cam.release()
                        cv2.destroyAllWindows()

        # Show the frame with detections
        cv2.imshow("YOLOv8 Live Detection (Person, Cell Phone, Head Movement)", frame)

        # Press 'q' to exit the webcam window
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    return head_orientation, label


