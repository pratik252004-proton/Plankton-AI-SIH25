"""
AI Accuracy Analysis Tool
Analyzes AI predictions vs user corrections from the detection database
"""

import sqlite3
import pandas as pd
from pathlib import Path

def analyze_ai_accuracy():
    """Analyze AI prediction accuracy from database"""
    
    db_path = Path(__file__).parent / "database" / "detection_db.db"
    conn = sqlite3.connect(db_path)
    
    # Get all verified detections
    query = """
        SELECT 
            ai_prediction,
            species as verified_species,
            corrected_by_user,
            confidence,
            location,
            detection_datetime
        FROM detections
        WHERE verified = 1
        ORDER BY detection_datetime DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if len(df) == 0:
        print("No verified detections found in database.")
        return
    
    print("\n" + "="*70)
    print("AI PREDICTION ACCURACY ANALYSIS")
    print("="*70)
    
    # Overall statistics
    total = len(df)
    corrected = df['corrected_by_user'].sum()
    correct = total - corrected
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print(f"\n📊 Overall Statistics:")
    print(f"  Total Verified Detections: {total}")
    print(f"  ✅ AI Correct: {correct} ({correct/total*100:.1f}%)")
    print(f"  ❌ User Corrected: {corrected} ({corrected/total*100:.1f}%)")
    print(f"  🎯 AI Accuracy: {accuracy:.1f}%")
    
    # Accuracy by confidence level
    print(f"\n📈 Accuracy by Confidence Level:")
    bins = [0, 0.5, 0.7, 0.9, 1.0]
    labels = ['Low (0-50%)', 'Medium (50-70%)', 'High (70-90%)', 'Very High (90-100%)']
    df['confidence_bin'] = pd.cut(df['confidence'], bins=bins, labels=labels)
    
    for label in labels:
        subset = df[df['confidence_bin'] == label]
        if len(subset) > 0:
            subset_correct = len(subset[subset['corrected_by_user'] == 0])
            subset_accuracy = (subset_correct / len(subset) * 100)
            print(f"  {label:20} {len(subset):4} detections  →  {subset_accuracy:.1f}% accurate")
    
    # Most commonly corrected species
    if corrected > 0:
        print(f"\n❌ Most Commonly Corrected AI Predictions:")
        corrections = df[df['corrected_by_user'] == 1]
        correction_counts = corrections['ai_prediction'].value_counts().head(10)
        
        for species, count in correction_counts.items():
            print(f"  {species:30} → {count} corrections")
    
    # Species with perfect accuracy
    print(f"\n✅ Species with Perfect AI Accuracy:")
    species_accuracy = df.groupby('ai_prediction').agg({
        'corrected_by_user': ['count', 'sum']
    })
    species_accuracy.columns = ['total', 'corrections']
    species_accuracy['accuracy'] = ((species_accuracy['total'] - species_accuracy['corrections']) / species_accuracy['total'] * 100)
    
    perfect = species_accuracy[species_accuracy['accuracy'] == 100].sort_values('total', ascending=False).head(10)
    
    for species, row in perfect.iterrows():
        print(f"  {species:30} → {int(row['total'])} detections, 100% accurate")
    
    # Corrections by location
    if 'location' in df.columns and df['location'].notna().any():
        print(f"\n📍 Corrections by Location:")
        location_stats = df.groupby('location').agg({
            'corrected_by_user': ['count', 'sum']
        })
        location_stats.columns = ['total', 'corrections']
        location_stats['accuracy'] = ((location_stats['total'] - location_stats['corrections']) / location_stats['total'] * 100)
        
        for location, row in location_stats.iterrows():
            if pd.notna(location):
                print(f"  {location:30} → {int(row['total'])} detections, {row['accuracy']:.1f}% accurate")
    
    print("\n" + "="*70)
    print("💡 Tip: Use this data to identify species that need model retraining!")
    print("="*70 + "\n")

if __name__ == "__main__":
    analyze_ai_accuracy()
