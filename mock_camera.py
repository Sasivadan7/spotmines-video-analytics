"""
Mock Camera Module
Generates synthetic video frames with moving shapes to simulate USB camera input.
No physical hardware required.
"""

import numpy as np
import random
import time


class MockCamera:
    """Simulates a USB camera with synthetic video generation."""
    
    # Simulated objects that can appear in frames
    OBJECT_TYPES = [
        {"name": "person", "color": (255, 100, 100), "min_size": 80, "max_size": 150},
        {"name": "car", "color": (100, 100, 255), "min_size": 100, "max_size": 180},
        {"name": "dog", "color": (100, 255, 100), "min_size": 40, "max_size": 80},
        {"name": "cat", "color": (255, 255, 100), "min_size": 30, "max_size": 60},
        {"name": "chair", "color": (255, 100, 255), "min_size": 50, "max_size": 90},
        {"name": "bottle", "color": (100, 255, 255), "min_size": 20, "max_size": 50},
    ]
    
    def __init__(self, width=640, height=480, fps=10):
        self.width = width
        self.height = height
        self.fps = fps
        self.frame_delay = 1.0 / fps
        
        # Initialize moving objects
        self.objects = self._create_objects(random.randint(2, 5))
        self.frame_count = 0
        
    def _create_objects(self, count):
        """Create random objects with positions and velocities."""
        objects = []
        for _ in range(count):
            obj_type = random.choice(self.OBJECT_TYPES)
            size = random.randint(obj_type["min_size"], obj_type["max_size"])
            
            objects.append({
                "type": obj_type["name"],
                "color": obj_type["color"],
                "x": random.randint(0, self.width - size),
                "y": random.randint(0, self.height - size),
                "width": size,
                "height": int(size * random.uniform(0.8, 1.5)),
                "vx": random.uniform(-3, 3),
                "vy": random.uniform(-3, 3),
                "confidence": random.uniform(0.6, 0.99),
            })
        return objects
    
    def _update_positions(self):
        """Update object positions with bounce physics."""
        for obj in self.objects:
            # Update position
            obj["x"] += obj["vx"]
            obj["y"] += obj["vy"]
            
            # Bounce off walls
            if obj["x"] <= 0 or obj["x"] + obj["width"] >= self.width:
                obj["vx"] *= -1
                obj["x"] = max(0, min(obj["x"], self.width - obj["width"]))
            if obj["y"] <= 0 or obj["y"] + obj["height"] >= self.height:
                obj["vy"] *= -1
                obj["y"] = max(0, min(obj["y"], self.height - obj["height"]))
            
            # Occasionally change velocity
            if random.random() < 0.02:
                obj["vx"] = random.uniform(-3, 3)
                obj["vy"] = random.uniform(-3, 3)
    
    def _draw_frame(self):
        """Generate a frame with objects drawn on it."""
        # Create gradient background (simulates room lighting)
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for y in range(self.height):
            gray = int(40 + (y / self.height) * 30)
            frame[y, :] = [gray, gray + 5, gray + 10]
        
        # Add some noise for realism
        noise = np.random.randint(-10, 10, (self.height, self.width, 3), dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # Draw objects
        for obj in self.objects:
            x1, y1 = int(obj["x"]), int(obj["y"])
            x2, y2 = x1 + obj["width"], y1 + obj["height"]
            
            # Draw filled rectangle with gradient
            for y in range(y1, min(y2, self.height)):
                for x in range(x1, min(x2, self.width)):
                    blend = 0.7 + 0.3 * ((y - y1) / obj["height"])
                    frame[y, x] = [int(c * blend) for c in obj["color"]]
            
            # Draw border
            cv2_available = False
            try:
                import cv2
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
                cv2_available = True
            except ImportError:
                # Manual border drawing if cv2 not available
                frame[y1:y1+2, x1:x2] = [255, 255, 255]
                frame[y2-2:y2, x1:x2] = [255, 255, 255]
                frame[y1:y2, x1:x1+2] = [255, 255, 255]
                frame[y1:y2, x2-2:x2] = [255, 255, 255]
        
        return frame
    
    def get_frame(self):
        """Get current frame and object data."""
        self._update_positions()
        frame = self._draw_frame()
        self.frame_count += 1
        
        # Return frame and ground truth detections
        detections = []
        for obj in self.objects:
            detections.append({
                "label": obj["type"],
                "confidence": obj["confidence"],
                "bbox": {
                    "x": int(obj["x"]),
                    "y": int(obj["y"]),
                    "width": obj["width"],
                    "height": obj["height"]
                }
            })
        
        return frame, detections
    
    def frames(self):
        """Generator that yields frames continuously."""
        while True:
            frame, detections = self.get_frame()
            yield frame, detections
            time.sleep(self.frame_delay)
    
    def read(self):
        """OpenCV-compatible read() method."""
        frame, detections = self.get_frame()
        return True, frame
    
    def release(self):
        """OpenCV-compatible release() method."""
        pass
    
    def isOpened(self):
        """OpenCV-compatible isOpened() method."""
        return True


if __name__ == "__main__":
    # Test the mock camera
    print("Testing Mock Camera...")
    cam = MockCamera()
    
    for i in range(5):
        frame, detections = cam.get_frame()
        print(f"Frame {i+1}: Shape={frame.shape}, Objects={len(detections)}")
        for det in detections:
            print(f"  - {det['label']}: {det['confidence']:.2f}")
        time.sleep(0.5)
    
    print("\nMock Camera test complete!")
