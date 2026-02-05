# Raspberry Pi Video Analytics Simulation

A complete simulation of a Raspberry Pi edge device performing video analytics with **fully mocked hardware**. No physical camera or Raspberry Pi required!

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Python Edge Device                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Mock Camera  │───▶│  Inference   │───▶│ MQTT Publish │      │
│  │ (Synthetic)  │    │ (Detection)  │    │              │      │
│  └──────────────┘    └──────────────┘    └──────┬───────┘      │
└─────────────────────────────────────────────────┼───────────────┘
                                                  │
                        MQTT Topics:              │
                        • video/stream            │
                        • analytics/data          ▼
                        • analytics/alerts    
┌─────────────────────────────────────────────────┴───────────────┐
│                    Node-RED Gateway                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ MQTT Broker  │───▶│  Dashboard   │───▶│   Alerts     │      │
│  │ (Aedes:1883) │    │  (Live UI)   │    │  (Toasts)    │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js 14+** with npm
- **Node-RED** installed globally

## 🚀 Quick Start

### 1. Install Python Dependencies

```powershell
cd c:\Users\lenovo\Desktop\spotmines-project
pip install -r requirements.txt
```

### 2. Install Node-RED (if not already installed)

```powershell
npm install -g node-red
```

### 3. Install Node-RED Dashboard Modules

```powershell
cd %USERPROFILE%\.node-red
npm install node-red-dashboard node-red-contrib-aedes
```

### 4. Start Node-RED with the Flow

```powershell
cd c:\Users\lenovo\Desktop\spotmines-project
node-red flows.json
```

Wait until you see: `Started flows`

### 5. Start the Edge Device Simulation

Open a **new terminal** and run:

```powershell
cd c:\Users\lenovo\Desktop\spotmines-project
python edge_device.py
```

You should see:
```
============================================================
    RASPBERRY PI VIDEO ANALYTICS SIMULATION
============================================================
[System] Starting edge device simulation...
[MQTT] Connected to broker at localhost:1883
[Camera] Mock camera initialized (640x480 @ 5fps)
[System] Running inference loop at 5 FPS...
------------------------------------------------------------
[Stats] Frames: 10 | Alerts: 3 | Objects in view: 4
[Alert] ALERT: PERSON detected with 85% confidence!
```

### 6. Open the Dashboard

Open your browser to: **http://localhost:1880/ui**

## 📁 Project Structure

```
spotmines-project/
├── edge_device.py      # Main edge device simulation
├── mock_camera.py      # Synthetic camera frame generator
├── flows.json          # Node-RED flow configuration
├── labels.txt          # COCO class labels
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## 🎯 Features

| Feature | Description |
|---------|-------------|
| **Mock Camera** | Generates synthetic frames with moving objects |
| **Object Detection** | Simulates detection of persons, cars, dogs, etc. |
| **Live Video Stream** | Real-time video display on dashboard |
| **Analytics Table** | Shows detected objects with confidence scores |
| **Object Count Chart** | Line chart tracking objects over time |
| **Alert System** | Toast notifications when specific objects detected |
| **MQTT Communication** | Full pub/sub messaging between components |

## 🔧 Configuration

Edit `edge_device.py` to customize:

```python
# Frame settings
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 5

# Objects that trigger alerts
ALERT_OBJECTS = ["person", "car", "dog"]
CONFIDENCE_THRESHOLD = 0.5
```

## 📊 MQTT Topics

| Topic | Payload | Description |
|-------|---------|-------------|
| `video/stream` | Base64 JPEG | Encoded video frames |
| `analytics/data` | JSON | Detection results with bboxes |
| `analytics/alerts` | JSON | Alert notifications |

## 🧪 Testing

### Test Mock Camera

```powershell
python -c "from mock_camera import MockCamera; mc = MockCamera(); frame, dets = mc.get_frame(); print(f'Frame shape: {frame.shape}, Detections: {len(dets)}')"
```

### Test MQTT Connectivity

1. Start Node-RED: `node-red flows.json`
2. Run edge device: `python edge_device.py`
3. Watch console for `[MQTT] Connected` message

## ❗ Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 1880 in use | Kill existing: `taskkill /F /IM node.exe` |
| MQTT connection failed | Ensure Node-RED started first |
| No video on dashboard | Check browser console for errors |
| Missing modules | Run npm install commands in `.node-red` folder |

## 📜 License

MIT License - Free for educational and commercial use.
