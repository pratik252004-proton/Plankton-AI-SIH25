import cv2
import numpy as np
from PIL import Image
from typing import Generator, Tuple, List
import tempfile
import os

class VideoProcessor:
    """Video processing utilities for plankton detection"""
    
    def __init__(self, video_path: str):
        """
        Initialize video processor
        
        Args:
            video_path: Path to video file
        """
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration = self.frame_count / self.fps if self.fps > 0 else 0
    
    def get_video_info(self) -> dict:
        """Get video metadata"""
        return {
            'fps': self.fps,
            'frame_count': self.frame_count,
            'width': self.width,
            'height': self.height,
            'duration_seconds': self.duration,
            'duration_formatted': self._format_duration(self.duration)
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration as MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def extract_frames(self, 
                      sample_rate: int = 1, 
                      max_frames: int = None) -> Generator[Tuple[int, np.ndarray], None, None]:
        """
        Extract frames from video
        
        Args:
            sample_rate: Extract every Nth frame (1 = all frames, 30 = 1 per second at 30fps)
            max_frames: Maximum number of frames to extract
            
        Yields:
            Tuple of (frame_number, frame_image)
        """
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to start
        
        frame_idx = 0
        extracted_count = 0
        
        while True:
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            if frame_idx % sample_rate == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                yield frame_idx, frame_rgb
                
                extracted_count += 1
                
                if max_frames and extracted_count >= max_frames:
                    break
            
            frame_idx += 1
    
    def extract_frame_at_time(self, time_seconds: float) -> np.ndarray:
        """
        Extract a single frame at specific time
        
        Args:
            time_seconds: Time in seconds
            
        Returns:
            Frame as numpy array (RGB)
        """
        frame_number = int(time_seconds * self.fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = self.cap.read()
        if not ret:
            raise ValueError(f"Could not extract frame at {time_seconds}s")
        
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    def extract_frames_pil(self, 
                          sample_rate: int = 1,
                          max_frames: int = None) -> Generator[Tuple[int, Image.Image, float], None, None]:
        """
        Extract frames as PIL Images with timestamps
        
        Args:
            sample_rate: Extract every Nth frame
            max_frames: Maximum number of frames to extract
            
        Yields:
            Tuple of (frame_number, PIL_Image, timestamp_seconds)
        """
        for frame_idx, frame_array in self.extract_frames(sample_rate, max_frames):
            pil_image = Image.fromarray(frame_array)
            timestamp = frame_idx / self.fps if self.fps > 0 else 0
            yield frame_idx, pil_image, timestamp
    
    def save_frame(self, frame: np.ndarray, output_path: str):
        """Save frame to file"""
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, frame_bgr)
    
    def create_annotated_video(self, 
                              frames_with_annotations: List[Tuple[np.ndarray, str]],
                              output_path: str,
                              fps: int = None):
        """
        Create video with annotations
        
        Args:
            frames_with_annotations: List of (frame, annotation_text) tuples
            output_path: Output video path
            fps: Output FPS (uses input FPS if None)
        """
        if not frames_with_annotations:
            return
        
        output_fps = fps if fps else self.fps
        
        # Get frame dimensions from first frame
        first_frame = frames_with_annotations[0][0]
        height, width = first_frame.shape[:2]
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, output_fps, (width, height))
        
        for frame, annotation in frames_with_annotations:
            # Add text annotation
            annotated_frame = frame.copy()
            cv2.putText(annotated_frame, annotation, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Convert RGB to BGR for video writer
            frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
            out.write(frame_bgr)
        
        out.release()
    
    def close(self):
        """Explicitly release video capture"""
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def __del__(self):
        """Release video capture"""
        self.close()
