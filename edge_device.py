"""
Edge Device with Improved Car Detection
Uses motion detection + contour analysis for better bounding boxes.
"""

import json
import base64
import time
import sys
import os
from datetime import datetime

import cv2
import numpy as np
import paho.mqtt.client as mqtt


# Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_VIDEO = "video/stream"
MQTT_TOPIC_ANALYTICS = "analytics/data"
MQTT_TOPIC_ALERTS = "analytics/alerts"

FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 8

ALERT_OBJECTS = ["person", "car", "truck", "bus"]
CONFIDENCE_THRESHOLD = 0.5

VIDEO_SOURCE = None


class CarDetector:
    """Simple but effective car/vehicle detector using background subtraction and contours."""
    
    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )
        self.min_area = 2000  # Minimum contour area
        self.frame_count = 0
        
    def detect(self, frame):
        """Detect vehicles and objects in frame."""
        detections = []
        height, width = frame.shape[:2]
        
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(frame)
        
        # Remove shadows (gray pixels become black)
        _, fg_mask = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # Skip very small or very thin detections
            if w < 30 or h < 30:
                continue
            
            # Classify based on aspect ratio and size
            aspect_ratio = w / h
            
            # Determine object type based on shape
            if aspect_ratio > 1.5 and area > 8000:
                label = "car"
                confidence = min(0.65 + (area / 100000), 0.95)
            elif aspect_ratio > 2.0 and area > 15000:
                label = "truck"
                confidence = min(0.60 + (area / 150000), 0.90)
            elif aspect_ratio < 0.7 and h > w:
                label = "person"
                confidence = min(0.55 + (area / 30000), 0.85)
            elif area > 5000:
                label = "vehicle"
                confidence = min(0.50 + (area / 80000), 0.80)
            else:
                continue
            
            detections.append({
                "label": label,
                "confidence": round(confidence, 2),
                "bbox": {
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h
                }
            })
        
        # Limit to top 10 detections by area
        detections = sorted(detections, key=lambda d: d["bbox"]["width"] * d["bbox"]["height"], reverse=True)[:10]
        
        self.frame_count += 1
        return detections


class EdgeDevice:
    """Edge device with improved detection and MQTT publishing."""
    
    def __init__(self, video_source=None):
        self.video_source = video_source
        self.camera = None
        self.detector = CarDetector()
        self.mqtt_client = None
        self.running = False
        self.detection_count = 0
        self.alert_count = 0
        
    def setup_mqtt(self):
        """Initialize MQTT client."""
        self.mqtt_client = mqtt.Client(client_id="edge_device_v2")
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print(f"[MQTT] ✓ Connected to {MQTT_BROKER}:{MQTT_PORT}")
            else:
                print(f"[MQTT] ✗ Connection failed (code {rc})")
        
        self.mqtt_client.on_connect = on_connect
        
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            print(f"[MQTT] ✗ Failed: {e}")
            return False
    
    def setup_camera(self):
        """Initialize video source."""
        if self.video_source and os.path.exists(self.video_source):
            self.camera = cv2.VideoCapture(self.video_source)
            if self.camera.isOpened():
                fps = self.camera.get(cv2.CAP_PROP_FPS)
                w = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                frames = int(self.camera.get(cv2.CAP_PROP_FRAME_COUNT))
                print(f"[Video] ✓ Loaded: {os.path.basename(self.video_source)}")
                print(f"[Video]   {w}x{h} @ {fps:.0f}fps, {frames} frames")
                return True
        
        # Fallback to webcam
        self.camera = cv2.VideoCapture(0)
        if self.camera.isOpened():
            print("[Camera] ✓ Using webcam")
            return True
        
        print("[Error] ✗ No video source available")
        return False
    
    def draw_detections(self, frame, detections):
        """Draw beautiful bounding boxes on frame."""
        overlay = frame.copy()
        
        for det in detections:
            bbox = det["bbox"]
            label = det["label"]
            conf = det["confidence"]
            
            x1, y1 = bbox["x"], bbox["y"]
            x2, y2 = x1 + bbox["width"], y1 + bbox["height"]
            
            # Colors by type
            colors = {
                "car": (0, 255, 100),      # Green
                "truck": (255, 150, 0),     # Orange
                "bus": (255, 100, 255),     # Pink
                "person": (100, 200, 255),  # Light blue
                "vehicle": (255, 255, 0),   # Yellow
            }
            color = colors.get(label, (255, 255, 255))
            
            # Draw filled rectangle with transparency
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            
            # Draw solid border
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            
            # Draw corner accents
            corner_len = min(20, bbox["width"] // 4, bbox["height"] // 4)
            cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, 4)
            cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, 4)
            cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, 4)
            cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, 4)
            cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, 4)
            cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, 4)
            cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, 4)
            cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, 4)
            
            # Label background
            label_text = f"{label.upper()} {conf:.0%}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (text_w, text_h), baseline = cv2.getTextSize(label_text, font, font_scale, thickness)
            
            # Draw label box
            cv2.rectangle(frame, (x1, y1 - text_h - 10), (x1 + text_w + 10, y1), color, -1)
            cv2.putText(frame, label_text, (x1 + 5, y1 - 5), font, font_scale, (0, 0, 0), thickness)
        
        # Blend overlay for semi-transparent boxes
        frame = cv2.addWeighted(overlay, 0.15, frame, 0.85, 0)
        
        # Add HUD overlay
        h, w = frame.shape[:2]
        
        # Top bar
        cv2.rectangle(frame, (0, 0), (w, 40), (20, 20, 20), -1)
        
        # Status text
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, f"LIVE | {timestamp}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 100), 2)
        cv2.putText(frame, f"Objects: {len(detections)}", (w - 150, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
        
        # Recording indicator
        if self.detection_count % 2 == 0:
            cv2.circle(frame, (w - 180, 22), 8, (0, 0, 255), -1)
        
        return frame
    
    def publish_frame(self, frame):
        """Publish frame to MQTT."""
        try:
            frame_resized = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            _, buffer = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 75])
            self.mqtt_client.publish(MQTT_TOPIC_VIDEO, base64.b64encode(buffer).decode())
            return True
        except Exception as e:
            return False
    
    def publish_analytics(self, detections):
        """Publish detection data."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "frame_id": self.detection_count,
            "object_count": len(detections),
            "detections": detections
        }
        self.mqtt_client.publish(MQTT_TOPIC_ANALYTICS, json.dumps(data))
    
    def check_alerts(self, detections):
        """Check and publish alerts."""
        for det in detections:
            if det["label"] in ALERT_OBJECTS and det["confidence"] >= CONFIDENCE_THRESHOLD:
                alert = {
                    "timestamp": datetime.now().isoformat(),
                    "object": det["label"],
                    "confidence": det["confidence"],
                    "message": f"{det['label'].upper()} detected ({det['confidence']:.0%})"
                }
                self.mqtt_client.publish(MQTT_TOPIC_ALERTS, json.dumps(alert))
                self.alert_count += 1
                print(f"[Alert] 🚨 {alert['message']}")
    
    def run(self):
        """Main loop."""
        print("\n" + "="*50)
        print("  VIDEO ANALYTICS - EDGE DEVICE v2.0")
        print("="*50)
        
        if not self.setup_mqtt():
            print("\n[Tip] Start Node-RED first: node-red flows.json")
            return
        
        if not self.setup_camera():
            return
        
        time.sleep(1)
        self.running = True
        
        print(f"\n[Running] Processing at {FPS} FPS... (Ctrl+C to stop)")
        print("-"*50)
        
        try:
            while self.running:
                start = time.time()
                
                ret, frame = self.camera.read()
                if not ret:
                    # Loop video
                    self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # Detect objects
                detections = self.detector.detect(frame)
                
                # Draw and publish
                frame_annotated = self.draw_detections(frame.copy(), detections)
                self.publish_frame(frame_annotated)
                self.publish_analytics(detections)
                self.check_alerts(detections)
                
                self.detection_count += 1
                
                if self.detection_count % 20 == 0:
                    print(f"[Stats] Frames: {self.detection_count} | Alerts: {self.alert_count} | Objects: {len(detections)}")
                
                # Frame rate control
                elapsed = time.time() - start
                time.sleep(max(0, (1.0 / FPS) - elapsed))
                
        except KeyboardInterrupt:
            print("\n\n[Stopping]...")
        finally:
            if self.camera:
                self.camera.release()
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            
            print(f"\n[Summary] Frames: {self.detection_count} | Alerts: {self.alert_count}")


def main():
    video = sys.argv[1] if len(sys.argv) > 1 else VIDEO_SOURCE
    EdgeDevice(video_source=video).run()


if __name__ == "__main__":
    main()
