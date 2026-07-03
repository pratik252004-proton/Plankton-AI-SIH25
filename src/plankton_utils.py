import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import io
from typing import Dict, List, Tuple
import pandas as pd
import json

class PlanktonVisualizer:
    """Visualization utilities for plankton detection results"""
    
    def __init__(self, dpi: int = 100):
        """
        Initialize visualizer
        
        Args:
            dpi: DPI for matplotlib figures
        """
        self.dpi = dpi
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def draw_prediction_on_image(self, 
                                 image: Image.Image,
                                 prediction: str,
                                 confidence: float,
                                 color: str = 'lime') -> Image.Image:
        """
        Draw prediction text on image
        
        Args:
            image: PIL Image
            prediction: Predicted class name
            confidence: Confidence score
            color: Text color
            
        Returns:
            Annotated PIL Image
        """
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Prepare text
        text = f"{prediction}"
        conf_text = f"Confidence: {confidence:.2%}"
        
        # Draw background rectangle
        bbox = draw.textbbox((10, 10), text, font=font)
        draw.rectangle(bbox, fill='black')
        
        # Draw text
        draw.text((10, 10), text, fill=color, font=font)
        draw.text((10, 40), conf_text, fill=color, font=font_small)
        
        return img_copy
    
    def create_species_bar_chart(self, 
                                 species_counts: Dict[str, int],
                                 top_n: int = 15,
                                 title: str = "Species Distribution") -> plt.Figure:
        """
        Create bar chart of species counts
        
        Args:
            species_counts: Dictionary of species -> count
            top_n: Show top N species
            title: Chart title
            
        Returns:
            Matplotlib figure
        """
        # Filter and sort
        filtered_counts = {k: v for k, v in species_counts.items() if v > 0}
        sorted_counts = dict(sorted(filtered_counts.items(), 
                                   key=lambda x: x[1], 
                                   reverse=True)[:top_n])
        
        if not sorted_counts:
            # Return empty figure
            fig, ax = plt.subplots(figsize=(10, 6), dpi=self.dpi)
            ax.text(0.5, 0.5, 'No detections', ha='center', va='center')
            ax.set_title(title)
            return fig
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8), dpi=self.dpi)
        
        species = list(sorted_counts.keys())
        counts = list(sorted_counts.values())
        
        bars = ax.barh(species, counts, color='steelblue', edgecolor='navy', alpha=0.8)
        
        # Add value labels
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(count, i, f' {count}', va='center', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Count', fontsize=12, fontweight='bold')
        ax.set_ylabel('Species', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_species_pie_chart(self,
                                 species_counts: Dict[str, int],
                                 top_n: int = 10,
                                 title: str = "Species Composition") -> plt.Figure:
        """
        Create pie chart of species proportions
        
        Args:
            species_counts: Dictionary of species -> count
            top_n: Show top N species, group rest as "Others"
            title: Chart title
            
        Returns:
            Matplotlib figure
        """
        # Filter and sort
        filtered_counts = {k: v for k, v in species_counts.items() if v > 0}
        sorted_counts = dict(sorted(filtered_counts.items(), 
                                   key=lambda x: x[1], 
                                   reverse=True))
        
        if not sorted_counts:
            fig, ax = plt.subplots(figsize=(8, 8), dpi=self.dpi)
            ax.text(0.5, 0.5, 'No detections', ha='center', va='center')
            ax.set_title(title)
            return fig
        
        # Get top N and group others
        top_species = dict(list(sorted_counts.items())[:top_n])
        
        if len(sorted_counts) > top_n:
            others_count = sum(list(sorted_counts.values())[top_n:])
            top_species['Others'] = others_count
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 10), dpi=self.dpi)
        
        species = list(top_species.keys())
        counts = list(top_species.values())
        
        # Create color palette
        colors = plt.cm.Set3(np.linspace(0, 1, len(species)))
        
        wedges, texts, autotexts = ax.pie(counts, labels=species, autopct='%1.1f%%',
                                          colors=colors, startangle=90,
                                          textprops={'fontsize': 10})
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        return fig
    
    def create_confidence_histogram(self,
                                    confidences: List[float],
                                    title: str = "Confidence Score Distribution") -> plt.Figure:
        """
        Create histogram of confidence scores
        
        Args:
            confidences: List of confidence scores
            title: Chart title
            
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(10, 6), dpi=self.dpi)
        
        if not confidences:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center')
            ax.set_title(title)
            return fig
        
        ax.hist(confidences, bins=20, color='steelblue', edgecolor='navy', alpha=0.7)
        
        # Add mean line
        mean_conf = np.mean(confidences)
        ax.axvline(mean_conf, color='red', linestyle='--', linewidth=2,
                  label=f'Mean: {mean_conf:.2%}')
        
        ax.set_xlabel('Confidence Score', fontsize=12, fontweight='bold')
        ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def fig_to_pil(self, fig: plt.Figure) -> Image.Image:
        """Convert matplotlib figure to PIL Image"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
        plt.close(fig)
        return img


class ResultsExporter:
    """Export detection results to various formats"""
    
    @staticmethod
    def to_csv(results: List[Dict], output_path: str):
        """
        Export results to CSV
        
        Args:
            results: List of detection dictionaries
            output_path: Output CSV path
        """
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
    
    @staticmethod
    def to_json(results: List[Dict], output_path: str, indent: int = 2):
        """
        Export results to JSON
        
        Args:
            results: List of detection dictionaries
            output_path: Output JSON path
            indent: JSON indentation
        """
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=indent)
    
    @staticmethod
    def create_summary_dict(species_counts: Dict[str, int],
                           confidences: List[float],
                           total_detections: int) -> Dict:
        """
        Create summary statistics dictionary
        
        Args:
            species_counts: Species count dictionary
            confidences: List of confidence scores
            total_detections: Total number of detections
            
        Returns:
            Summary dictionary
        """
        summary = {
            'total_detections': total_detections,
            'unique_species': len([k for k, v in species_counts.items() if v > 0]),
            'species_counts': species_counts,
            'confidence_stats': {
                'mean': float(np.mean(confidences)) if confidences else 0,
                'std': float(np.std(confidences)) if confidences else 0,
                'min': float(np.min(confidences)) if confidences else 0,
                'max': float(np.max(confidences)) if confidences else 0,
                'median': float(np.median(confidences)) if confidences else 0
            }
        }
        return summary
