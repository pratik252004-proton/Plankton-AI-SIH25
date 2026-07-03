"""
Video annotation utilities for plankton detection visualization
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import List, Tuple, Dict
import tempfile
import os


class VideoAnnotator:
    """Create annotated videos with detection overlays"""
    
    def __init__(self, font_scale: float = 0.8, thickness: int = 2):
        """
        Initialize video annotator
        
        Args:
            font_scale: Scale for text annotations
            thickness: Line thickness for boxes and text
        """
        self.font_scale = font_scale
        self.thickness = thickness
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Color palette for different species (BGR format for OpenCV)
        self.colors = [
            (255, 0, 0),      # Blue
            (0, 255, 0),      # Green
            (0, 0, 255),      # Red
            (255, 255, 0),    # Cyan
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Yellow
            (128, 0, 128),    # Purple
            (255, 165, 0),    # Orange
            (0, 128, 128),    # Teal
            (128, 128, 0),    # Olive
        ]
        self.species_color_map = {}
    
    def get_species_color(self, species: str) -> Tuple[int, int, int]:
        """Get consistent color for a species"""
        if species not in self.species_color_map:
            color_idx = len(self.species_color_map) % len(self.colors)
            self.species_color_map[species] = self.colors[color_idx]
        return self.species_color_map[species]
    
    def draw_detection_box(self, 
                          frame: np.ndarray, 
                          species: str, 
                          confidence: float,
                          box_type: str = 'full') -> np.ndarray:
        """
        Draw detection box and label on frame
        
        Args:
            frame: Frame as numpy array (RGB)
            species: Detected species name
            confidence: Confidence score
            box_type: 'full' (whole frame), 'center' (center box), or custom bbox
            
        Returns:
            Annotated frame
        """
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        height, width = frame_bgr.shape[:2]
        
        # Get color for this species
        color = self.get_species_color(species)
        
        # Determine bounding box coordinates
        if box_type == 'full':
            # Full frame with margin
            margin = 10
            x1, y1 = margin, margin
            x2, y2 = width - margin, height - margin
        elif box_type == 'center':
            # Center 60% of frame
            w_margin = int(width * 0.2)
            h_margin = int(height * 0.2)
            x1, y1 = w_margin, h_margin
            x2, y2 = width - w_margin, height - h_margin
        else:
            # Default to full frame
            x1, y1 = 10, 10
            x2, y2 = width - 10, height - 10
        
        # Draw bounding box
        cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), color, self.thickness)
        
        # Prepare label text
        label = f"{species}"
        conf_text = f"{confidence:.1%}"
        
        # Calculate text size for background
        (label_w, label_h), _ = cv2.getTextSize(label, self.font, self.font_scale, self.thickness)
        (conf_w, conf_h), _ = cv2.getTextSize(conf_text, self.font, self.font_scale * 0.7, self.thickness - 1)
        
        # Draw background rectangle for text
        bg_y1 = max(y1 - label_h - conf_h - 20, 0)
        bg_y2 = y1
        bg_x2 = x1 + max(label_w, conf_w) + 20
        
        # Semi-transparent background
        overlay = frame_bgr.copy()
        cv2.rectangle(overlay, (x1, bg_y1), (bg_x2, bg_y2), color, -1)
        cv2.addWeighted(overlay, 0.7, frame_bgr, 0.3, 0, frame_bgr)
        
        # Draw text
        text_y = bg_y1 + label_h + 5
        cv2.putText(frame_bgr, label, (x1 + 5, text_y), 
                   self.font, self.font_scale, (255, 255, 255), self.thickness)
        
        conf_y = text_y + conf_h + 5
        cv2.putText(frame_bgr, conf_text, (x1 + 5, conf_y), 
                   self.font, self.font_scale * 0.7, (255, 255, 255), self.thickness - 1)
        
        # Convert back to RGB
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    
    def create_annotated_video(self,
                              frames_with_detections: List[Tuple[np.ndarray, str, float, float]],
                              output_path: str,
                              fps: float = 30.0,
                              codec: str = 'avc1') -> str:
        """
        Create annotated video from frames with detections
        
        Args:
            frames_with_detections: List of (frame, species, confidence, timestamp) tuples
            output_path: Output video path
            fps: Output video FPS
            codec: Video codec ('avc1' for H.264, 'mp4v' for MPEG-4)
            
        Returns:
            Path to created video
        """
        if not frames_with_detections:
            raise ValueError("No frames provided")
        
        # Get frame dimensions from first frame
        first_frame = frames_with_detections[0][0]
        height, width = first_frame.shape[:2]
        
        # Try H.264 codec first (best browser compatibility)
        fourcc = cv2.VideoWriter_fourcc(*codec)
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # If H.264 fails, fallback to mp4v
        if not out.isOpened():
            print(f"Warning: {codec} codec failed, trying mp4v...")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            raise ValueError(f"Could not create video writer for {output_path}")
        
        # Process each frame
        for frame, species, confidence, timestamp in frames_with_detections:
            # Annotate frame
            annotated = self.draw_detection_box(frame, species, confidence, box_type='center')
            
            # Add timestamp
            annotated_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            time_text = f"t={timestamp:.2f}s"
            cv2.putText(annotated_bgr, time_text, (10, height - 10),
                       self.font, 0.6, (255, 255, 255), 2)
            
            # Write frame
            out.write(annotated_bgr)
        
        out.release()
        return output_path
    
    def create_side_by_side_video(self,
                                 original_frames: List[np.ndarray],
                                 annotated_frames: List[np.ndarray],
                                 output_path: str,
                                 fps: float = 30.0) -> str:
        """
        Create side-by-side comparison video
        
        Args:
            original_frames: List of original frames
            annotated_frames: List of annotated frames
            output_path: Output video path
            fps: Output FPS
            
        Returns:
            Path to created video
        """
        if len(original_frames) != len(annotated_frames):
            raise ValueError("Original and annotated frame counts must match")
        
        if not original_frames:
            raise ValueError("No frames provided")
        
        # Get dimensions
        height, width = original_frames[0].shape[:2]
        combined_width = width * 2
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (combined_width, height))
        
        # Process frames
        for orig, annot in zip(original_frames, annotated_frames):
            # Convert to BGR
            orig_bgr = cv2.cvtColor(orig, cv2.COLOR_RGB2BGR)
            annot_bgr = cv2.cvtColor(annot, cv2.COLOR_RGB2BGR)
            
            # Combine horizontally
            combined = np.hstack([orig_bgr, annot_bgr])
            
            # Add labels
            cv2.putText(combined, "Original", (10, 30),
                       self.font, 0.8, (255, 255, 255), 2)
            cv2.putText(combined, "Detected", (width + 10, 30),
                       self.font, 0.8, (255, 255, 255), 2)
            
            out.write(combined)
        
        out.release()
        return output_path
    
    def add_legend(self, 
                  frame: np.ndarray, 
                  species_counts: Dict[str, int],
                  position: str = 'bottom-right') -> np.ndarray:
        """
        Add species legend to frame
        
        Args:
            frame: Frame as numpy array (RGB)
            species_counts: Dictionary of species -> count
            position: Legend position
            
        Returns:
            Frame with legend
        """
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        height, width = frame_bgr.shape[:2]
        
        # Filter species with counts > 0
        active_species = {k: v for k, v in species_counts.items() if v > 0}
        
        if not active_species:
            return frame
        
        # Calculate legend dimensions
        line_height = 30
        legend_height = len(active_species) * line_height + 40
        legend_width = 250
        
        # Determine position
        if position == 'bottom-right':
            x = width - legend_width - 10
            y = height - legend_height - 10
        elif position == 'top-right':
            x = width - legend_width - 10
            y = 10
        elif position == 'bottom-left':
            x = 10
            y = height - legend_height - 10
        else:  # top-left
            x = 10
            y = 10
        
        # Draw semi-transparent background
        overlay = frame_bgr.copy()
        cv2.rectangle(overlay, (x, y), (x + legend_width, y + legend_height), 
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame_bgr, 0.3, 0, frame_bgr)
        
        # Draw title
        cv2.putText(frame_bgr, "Detected Species", (x + 10, y + 25),
                   self.font, 0.6, (255, 255, 255), 2)
        
        # Draw species list
        current_y = y + 50
        for species, count in sorted(active_species.items(), key=lambda x: x[1], reverse=True):
            color = self.get_species_color(species)
            
            # Draw color box
            cv2.rectangle(frame_bgr, (x + 10, current_y - 15), 
                         (x + 30, current_y), color, -1)
            
            # Draw text
            text = f"{species[:20]}: {count}"
            cv2.putText(frame_bgr, text, (x + 40, current_y),
                       self.font, 0.5, (255, 255, 255), 1)
            
            current_y += line_height
        
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
