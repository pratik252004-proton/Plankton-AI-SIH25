"""
Detection Logger - Saves plankton detection results to database
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class DetectionLogger:
    """Log plankton detections to SQLite database"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize detection logger
        
        Args:
            db_path: Path to database file (default: ../database/detection_db.db)
        """
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "database" / "detection_db.db")
        
        self.db_path = db_path
        self._create_table()
    
    def _create_table(self):
        """Create detections table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_name TEXT NOT NULL,
                species TEXT NOT NULL,
                confidence REAL NOT NULL,
                detection_datetime TEXT NOT NULL,
                location TEXT,
                ai_prediction TEXT,
                verified BOOLEAN DEFAULT 1,
                corrected_by_user BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_detection(
        self, 
        image_name: str, 
        species: str, 
        confidence: float,
        location: Optional[str] = None,
        ai_prediction: Optional[str] = None,
        verified: bool = True,
        corrected_by_user: bool = False
    ) -> int:
        """
        Log a detection to the database
        
        Args:
            image_name: Name of the image file
            species: Final verified species name
            confidence: Confidence score (0-1)
            location: Optional location information
            ai_prediction: Original AI prediction (for accuracy tracking)
            verified: Whether this detection was verified by user
            corrected_by_user: Whether user corrected the AI prediction
            
        Returns:
            ID of the inserted record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        detection_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # If no AI prediction provided, assume it's the same as species
        if ai_prediction is None:
            ai_prediction = species
        
        cursor.execute("""
            INSERT INTO detections 
            (image_name, species, confidence, detection_datetime, location, 
             ai_prediction, verified, corrected_by_user)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (image_name, species, confidence, detection_datetime, location,
              ai_prediction, verified, corrected_by_user))
        
        detection_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return detection_id
    
    def get_recent_detections(self, limit: int = 10):
        """Get recent detections"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, image_name, species, confidence, detection_datetime, location
            FROM detections
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return results
    
    def get_detection_count(self) -> int:
        """Get total number of detections"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM detections")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count


# Singleton instance
_logger_instance = None

def get_detection_logger() -> DetectionLogger:
    """Get or create detection logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = DetectionLogger()
    return _logger_instance
