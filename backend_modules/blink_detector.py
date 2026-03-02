import cv2
import numpy as np
import dlib
import mediapipe as mp
from scipy.spatial import distance
from collections import deque
import time
import os

class BlinkDetector:
    def __init__(self):
        # Use MediaPipe as primary (dlib has issues with Python 3.12)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.use_mediapipe = True
        
        # Initialize dlib (but won't use due to compatibility issues)
        try:
            self.detector = dlib.get_frontal_face_detector()
            predictor_path = "shape_predictor_68_face_landmarks.dat"
            if not os.path.exists(predictor_path):
                print("Downloading dlib shape predictor model...")
                self._download_shape_predictor()
            self.predictor = dlib.shape_predictor(predictor_path)
        except Exception as e:
            print(f"⚠️  Dlib initialization failed: {e}")
            print("   Using MediaPipe exclusively")
            self.detector = None
            self.predictor = None
        self.LEFT_EYE_POINTS = list(range(36, 42))
        self.RIGHT_EYE_POINTS = list(range(42, 48))
        self.LEFT_EYE_EAR_INDICES = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_EAR_INDICES = [362, 385, 387, 263, 373, 380]
        
        # Fixed threshold (no adaptive threshold)
        self.EAR_THRESHOLD = 0.20
        self.ear_history = deque(maxlen=30)
        self.EYE_AR_CONSEC_FRAMES = 1
        self.counter = 0
        self.blink_detected = False
        self.blink_start_time = 0
        self.brightness_history = deque(maxlen=10)
        self.use_enhancement = False
        
        # Duration thresholds for blink classification
        self.SHORT_BLINK_MAX = 0.3  # 0 to 0.3s = short blink (dot)
        self.LONG_BLINK_MIN = 0.5   # 0.5s and above = long blink (dash)

    def _download_shape_predictor(self):
        import urllib.request
        import bz2
        url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
        try:
            urllib.request.urlretrieve(url, "shape_predictor_68_face_landmarks.dat.bz2")
            with bz2.BZ2File("shape_predictor_68_face_landmarks.dat.bz2", 'rb') as f_in:
                with open("shape_predictor_68_face_landmarks.dat", 'wb') as f_out:
                    f_out.write(f_in.read())
            os.remove("shape_predictor_68_face_landmarks.dat.bz2")
            print("Shape predictor model downloaded successfully!")
        except Exception as e:
            print(f"Failed to download shape predictor: {e}. Please ensure internet connection or provide the file manually.")
            raise

    def enhance_frame(self, frame):
        if frame is None or len(frame.shape) != 3:
            return frame
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        self.brightness_history.append(brightness)
        avg_brightness = np.mean(self.brightness_history)
        self.use_enhancement = avg_brightness < 80
        if self.use_enhancement:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            lab[:,:,0] = clahe.apply(lab[:,:,0])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            if avg_brightness < 50:
                enhanced = cv2.convertScaleAbs(enhanced, alpha=1.3, beta=25)
            # Ensure uint8 format
            return np.ascontiguousarray(enhanced, dtype=np.uint8)
        return np.ascontiguousarray(frame, dtype=np.uint8)

    def eye_aspect_ratio_dlib(self, eye_landmarks):
        try:
            A = distance.euclidean(eye_landmarks[1], eye_landmarks[5])
            B = distance.euclidean(eye_landmarks[2], eye_landmarks[4])
            C = distance.euclidean(eye_landmarks[0], eye_landmarks[3])
            if C == 0: return 0
            return (A + B) / (2.0 * C)
        except IndexError:
            return 0

    def eye_aspect_ratio_mediapipe(self, eye_landmarks):
        try:
            A = distance.euclidean(eye_landmarks[1], eye_landmarks[5])
            B = distance.euclidean(eye_landmarks[2], eye_landmarks[4])
            C = distance.euclidean(eye_landmarks[0], eye_landmarks[3])
            if C == 0: return 0
            return (A + B) / (2.0 * C)
        except IndexError:
            return 0

    def get_eye_landmarks_mediapipe(self, landmarks, eye_indices, image_width, image_height):
        eye_points = []
        for idx in eye_indices:
            landmark = landmarks.landmark[idx]
            x = int(landmark.x * image_width)
            y = int(landmark.y * image_height)
            eye_points.append([x, y])
        return np.array(eye_points)

    def classify_blink_by_duration(self, duration):
        """Classify blink as 'dot' (short) or 'dash' (long) based on duration.
        
        Short blink (dot): 0 to 0.3 seconds
        Long blink (dash): 0.5 seconds and above
        Medium blink (0.3 to 0.5s): treated as dot by default
        """
        if duration <= self.SHORT_BLINK_MAX:
            return 'dot'
        elif duration >= self.LONG_BLINK_MIN:
            return 'dash'
        else:
            # Medium range - treat as short blink
            return 'dot'

    def detect_blink_dlib(self, frame):
        try:
            enhanced_frame = self.enhance_frame(frame)
            gray = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2GRAY)
            # Ensure gray is uint8 and contiguous for dlib
            gray = np.ascontiguousarray(gray, dtype=np.uint8)
            
            faces = self.detector(gray)
            if len(faces) > 0:
                face = faces[0]
                landmarks = self.predictor(gray, face)
                left_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in self.LEFT_EYE_POINTS])
                right_eye = np.array([(landmarks.part(i).x, landmarks.part(i).y) for i in self.RIGHT_EYE_POINTS])
                left_ear = self.eye_aspect_ratio_dlib(left_eye)
                right_ear = self.eye_aspect_ratio_dlib(right_eye)
                ear = (left_ear + right_ear) / 2.0
                return ear, True
            return None, False
        except Exception as e:
            print(f"Dlib detection error: {e}")
            return None, False

    def detect_blink_mediapipe(self, frame):
        try:
            with self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                min_detection_confidence=0.3,
                min_tracking_confidence=0.3) as face_mesh:

                enhanced_frame = self.enhance_frame(frame)
                rgb_frame = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2RGB)
                # Ensure correct format
                rgb_frame = np.ascontiguousarray(rgb_frame, dtype=np.uint8)
                rgb_frame.flags.writeable = False
                results = face_mesh.process(rgb_frame)
                rgb_frame.flags.writeable = True

                if results.multi_face_landmarks:
                    for face_landmarks in results.multi_face_landmarks:
                        h, w = enhanced_frame.shape[:2]
                        left_eye = self.get_eye_landmarks_mediapipe(face_landmarks, self.LEFT_EYE_EAR_INDICES, w, h)
                        right_eye = self.get_eye_landmarks_mediapipe(face_landmarks, self.RIGHT_EYE_EAR_INDICES, w, h)
                        left_ear = self.eye_aspect_ratio_mediapipe(left_eye)
                        right_ear = self.eye_aspect_ratio_mediapipe(right_eye)
                        ear = (left_ear + right_ear) / 2.0
                        return ear, True
            return None, False
        except Exception as e:
            print(f"MediaPipe detection error: {e}")
            return None, False

    def detect_blink(self, frame):
        # Validate frame
        if frame is None or len(frame.shape) != 3:
            print("⚠️  Invalid frame received")
            return None, None
            
        blink_info = None
        current_ear = None
        
        # Use MediaPipe as primary method
        ear, mp_success = self.detect_blink_mediapipe(frame)
        
        if not mp_success:
            if not hasattr(self, 'no_face_counter'):
                self.no_face_counter = 0
            self.no_face_counter += 1
            if self.no_face_counter % 100 == 0:
                print(f"⚠️  No face detected for {self.no_face_counter} frames")
            return None, None
        
        # Reset no face counter if face is detected
        if hasattr(self, 'no_face_counter'):
            self.no_face_counter = 0
            
        current_ear = ear
        # Store EAR history for monitoring (no adaptive threshold)
        if current_ear is not None:
            self.ear_history.append(current_ear)
        
        # Print debug info every 50 frames
        if hasattr(self, 'debug_counter'):
            self.debug_counter += 1
        else:
            self.debug_counter = 0
            
        if self.debug_counter % 50 == 0:
            print(f"EAR: {ear:.3f}, Fixed Threshold: {self.EAR_THRESHOLD:.3f}")
        
        # Use fixed threshold for blink detection
        if ear is not None and ear < self.EAR_THRESHOLD:
            self.counter += 1
            if not self.blink_detected:
                self.blink_start_time = time.time()
                self.blink_detected = True
        else:
            if self.counter >= self.EYE_AR_CONSEC_FRAMES and self.blink_detected:
                blink_duration = time.time() - self.blink_start_time
                if 0.05 < blink_duration < 3.0:
                    # Classify blink type by duration
                    blink_type = self.classify_blink_by_duration(blink_duration)
                    blink_info = {
                        'duration': blink_duration,
                        'type': blink_type,
                        'intensity': max(0.01, self.EAR_THRESHOLD - min(ear if ear else 0, self.EAR_THRESHOLD)),
                        'timestamp': time.time(),
                        'min_ear': ear if ear else 0,
                        'enhanced': self.use_enhancement
                    }
                    print(f"✓ {blink_type.upper()} blink: {blink_duration:.3f}s (EAR: {ear:.3f})")
            self.counter = 0
            self.blink_detected = False
        return blink_info, current_ear