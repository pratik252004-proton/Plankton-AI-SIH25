"""
Plankton Detection & Analysis System
Scientific web interface for automated plankton identification and counting
"""

import streamlit as st
import torch
import sys
import os
from pathlib import Path
import numpy as np
from PIL import Image
import tempfile
import pandas as pd
import json
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from model import get_model
from data_loader import get_dataloaders
from video_processor import VideoProcessor
from video_annotator import VideoAnnotator
from plankton_utils import PlanktonVisualizer, ResultsExporter
from torchvision import transforms

# Page configuration
st.set_page_config(
    page_title="Plankton Detection System",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for scientific look
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #1e3a8a;
        --secondary-color: #3b82f6;
        --accent-color: #10b981;
        --bg-dark: #0f172a;
        --bg-light: #1e293b;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: #e0e7ff;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #3b82f6;
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.5rem;
    }
    
    /* Info boxes */
    .info-box {
        background: #1e293b;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #451a03;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: #1e293b;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
    }
    
    /* File uploader */
    .uploadedFile {
        background: #1e293b;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #1e293b;
        border-radius: 6px 6px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #10b981 100%);
    }
    
    /* Dataframe styling */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Section headers */
    .section-header {
        color: #3b82f6;
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model_and_classes(model_path, data_dir=None):
    """Load model and class names (cached)"""
    try:
        # Try to load class names from JSON file first (for Docker/production)
        parent_dir = Path(__file__).parent.parent
        class_names_file = parent_dir / "checkpoints" / "class_names.json"
        
        if class_names_file.exists():
            # Load from JSON file
            import json
            with open(class_names_file, 'r') as f:
                classes = json.load(f)
            st.info(f"Loaded {len(classes)} classes from class_names.json")
        elif data_dir and os.path.exists(data_dir):
            # Fallback: Load from data directory
            _, _, _, classes, _ = get_dataloaders(data_dir, batch_size=1, sample_fraction=0.01)
            st.info(f"Loaded {len(classes)} classes from data directory")
        else:
            # Last resort: try to extract from model checkpoint
            checkpoint = torch.load(model_path, map_location='cpu')
            if isinstance(checkpoint, dict) and 'classes' in checkpoint:
                classes = checkpoint['classes']
                st.info(f"Loaded {len(classes)} classes from model checkpoint")
            else:
                raise ValueError("Could not find class names. Please create checkpoints/class_names.json file.")
        
        # Load model
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = get_model(len(classes), pretrained=False)
        
        # Load checkpoint
        checkpoint = torch.load(model_path, map_location=device)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        
        model.to(device)
        model.eval()
        
        return model, classes, device
    except Exception as e:
        st.error(f"Error loading model: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None, None, None



def get_transform():
    """Get image preprocessing transform"""
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])


def predict_image(model, image, device):
    """Predict class for a single image"""
    transform = get_transform()
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    img_tensor = transform(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(img_tensor)
        probabilities = torch.nn.functional.softmax(output, dim=1)
        confidence, predicted_idx = torch.max(probabilities, 1)
    
    return predicted_idx.item(), confidence.item(), probabilities.cpu().numpy()[0]


def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🔬 Marine Plankton Detection & Analysis System</h1>
        <p>Automated species identification and quantitative analysis using deep learning</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    st.sidebar.title("⚙️ System Configuration")
    
    # Model selection
    st.sidebar.markdown("### Model Selection")
    model_choice = st.sidebar.radio(
        "Select trained model:",
        ["best_model.pth", "epoch1.pth","epoch_3.pth"],
        help="Choose which trained model to use for inference"
    )
    
    # Model path - go up one directory from app folder
    parent_dir = Path(__file__).parent.parent
    model_path = parent_dir / "checkpoints" / model_choice
    data_dir = "d:/Plankton/101141/individual_images"
    
    # Load model
    with st.spinner("Loading model and class definitions..."):
        model, classes, device = load_model_and_classes(model_path, data_dir)
    
    if model is None:
        st.error("Failed to load model. Please check the model path and try again.")
        return
    
    # Model info
    st.sidebar.success(f"✓ Model loaded: {model_choice}")
    st.sidebar.info(f"Device: {device.upper()}")
    st.sidebar.info(f"Classes: {len(classes)}")
    
    # Processing parameters
    st.sidebar.markdown("### Processing Parameters")
    confidence_threshold = st.sidebar.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Minimum confidence score to accept a detection"
    )
    
    video_fps = st.sidebar.slider(
        "Video Frame Sampling (FPS)",
        min_value=0.5,
        max_value=5.0,
        value=1.0,
        step=0.5,
        help="Frames per second to extract from video"
    )
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📸 Image Analysis", 
        "🎥 Video Analysis", 
        "📊 Batch Processing",
        "💬 Chat with Database"
    ])
    
    # ==================== IMAGE ANALYSIS TAB ====================
    with tab1:
        st.markdown('<p class="section-header">Single/Multiple Image Analysis</p>', unsafe_allow_html=True)
        
        uploaded_images = st.file_uploader(
            "Upload plankton images",
            type=['png', 'jpg', 'jpeg', 'tiff', 'tif'],
            accept_multiple_files=True,
            help="Upload one or more images for analysis"
        )
        
        if uploaded_images:
            st.info(f"📁 {len(uploaded_images)} image(s) uploaded")
            
            # Location input with Varanasi as default
            st.markdown("### 📍 Location")
            location = st.text_input(
                "Sample Collection Location",
                value="Varanasi, Uttar Pradesh, India",
                placeholder="e.g., Varanasi, Uttar Pradesh, India",
                help="Enter the location where samples were collected"
            )
            
            if location:
                st.success(f"📍 Location: **{location}**")
            
            # Initialize session state for image analysis verification
            if 'image_results' not in st.session_state:
                st.session_state.image_results = []
            if 'image_data' not in st.session_state:
                st.session_state.image_data = {}
            if 'image_location' not in st.session_state:
                st.session_state.image_location = ""
            
            if st.button("🔍 Analyze Images", key="analyze_images"):
                # Clear previous results
                st.session_state.image_results = []
                st.session_state.image_data = {}
                st.session_state.image_location = location
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, uploaded_file in enumerate(uploaded_images):
                    status_text.text(f"Processing {idx+1}/{len(uploaded_images)}: {uploaded_file.name}")
                    
                    # Load image
                    image = Image.open(uploaded_file)
                    
                    # Store image for display
                    st.session_state.image_data[uploaded_file.name] = image.copy()
                    
                    # Predict
                    pred_idx, confidence, all_probs = predict_image(model, image, device)
                    predicted_class = classes[pred_idx]
                    
                    # Store results (NOT saved to DB yet - waiting for verification)
                    if confidence >= confidence_threshold:
                        st.session_state.image_results.append({
                            'image_name': uploaded_file.name,
                            'ai_prediction': predicted_class,
                            'confidence': confidence,
                            'verified_species': predicted_class,  # Default to AI prediction
                            'verification_status': 'pending',  # pending, verified, corrected
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    
                    progress_bar.progress((idx + 1) / len(uploaded_images))
                
                status_text.empty()
                progress_bar.empty()
                
                st.success(f"✅ Analysis complete! Please verify the results below.")
                st.rerun()
            
            # Display verification interface if results exist
            if st.session_state.image_results:
                st.markdown("---")
                st.markdown('<p class="section-header">🔍 Verify Detection Results</p>', unsafe_allow_html=True)
                
                # Verification progress
                total_results = len(st.session_state.image_results)
                verified_count = sum(1 for r in st.session_state.image_results 
                                   if r['verification_status'] in ['verified', 'corrected'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Detections", total_results)
                with col2:
                    st.metric("Verified", verified_count, delta=f"{verified_count/total_results*100:.0f}%" if total_results > 0 else "0%")
                
                # Display results in grid with verification buttons
                st.markdown("### 📋 Review Each Detection")
                cols_per_row = 3
                
                for i in range(0, len(st.session_state.image_results), cols_per_row):
                    cols = st.columns(cols_per_row)
                    
                    for j, col in enumerate(cols):
                        if i + j < len(st.session_state.image_results):
                            result = st.session_state.image_results[i + j]
                            result_idx = i + j
                            
                            with col:
                                # Display image
                                if result['image_name'] in st.session_state.image_data:
                                    img = st.session_state.image_data[result['image_name']]
                                    st.image(img, use_column_width=True)
                                
                                # Verification status indicator
                                if result['verification_status'] == 'verified':
                                    status_color = "#10b981"
                                    status_icon = "✅"
                                    status_text = "Verified"
                                elif result['verification_status'] == 'corrected':
                                    status_color = "#f59e0b"
                                    status_icon = "✏️"
                                    status_text = "Corrected"
                                else:
                                    status_color = "#6b7280"
                                    status_icon = "⏳"
                                    status_text = "Pending"
                                
                                # Display detection info
                                confidence_color = "#10b981" if result['confidence'] > 0.8 else "#f59e0b" if result['confidence'] > 0.6 else "#ef4444"
                                
                                st.markdown(f"""
                                <div style="background: #1e293b; padding: 0.8rem; border-radius: 8px; 
                                            border-left: 4px solid {status_color}; margin-top: -1rem;">
                                    <div style="color: {status_color}; font-weight: bold; margin-bottom: 0.5rem;">
                                        {status_icon} {status_text}
                                    </div>
                                    <strong style="color: #3b82f6;">🤖 AI: {result['ai_prediction']}</strong><br>
                                    <small style="color: #94a3b8;">
                                        📊 Confidence: <span style="color: {confidence_color};">{result['confidence']:.1%}</span><br>
                                        📁 {result['image_name'][:20]}...
                                    </small>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Verification buttons (only if pending)
                                if result['verification_status'] == 'pending':
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    
                                    btn_col1, btn_col2 = st.columns(2)
                                    
                                    with btn_col1:
                                        if st.button("✅ Correct", key=f"img_verify_{result_idx}", use_container_width=True):
                                            st.session_state.image_results[result_idx]['verification_status'] = 'verified'
                                            st.rerun()
                                    
                                    with btn_col2:
                                        if st.button("❌ Wrong", key=f"img_wrong_{result_idx}", use_container_width=True):
                                            st.session_state.image_results[result_idx]['verification_status'] = 'correcting'
                                            st.rerun()
                                
                                # Correction interface
                                elif result['verification_status'] == 'correcting':
                                    st.markdown("<br>", unsafe_allow_html=True)
                                    
                                    # Add "Custom/Unknown" option to species list
                                    species_options = ["🆕 Custom/Unknown Species"] + classes
                                    
                                    corrected_species = st.selectbox(
                                        "Select correct species:",
                                        options=species_options,
                                        key=f"img_correct_species_{result_idx}",
                                        index=0
                                    )
                                    
                                    # If custom species selected, show text input
                                    final_species = corrected_species
                                    if corrected_species == "🆕 Custom/Unknown Species":
                                        custom_name = st.text_input(
                                            "Enter species name:",
                                            key=f"img_custom_species_{result_idx}",
                                            placeholder="e.g., Copepod sp. nov."
                                        )
                                        if custom_name:
                                            final_species = custom_name
                                        else:
                                            st.warning("⚠️ Please enter a species name")
                                    
                                    # Only enable save button if valid species selected
                                    can_save = (corrected_species != "🆕 Custom/Unknown Species") or (corrected_species == "🆕 Custom/Unknown Species" and custom_name)
                                    
                                    if st.button("💾 Save Correction", key=f"img_save_correction_{result_idx}", use_container_width=True, disabled=not can_save):
                                        st.session_state.image_results[result_idx]['verified_species'] = final_species
                                        st.session_state.image_results[result_idx]['verification_status'] = 'corrected'
                                        st.rerun()
                                
                                # Show final verified species if corrected
                                elif result['verification_status'] == 'corrected':
                                    st.markdown(f"""
                                    <div style="background: #0f172a; padding: 0.5rem; border-radius: 4px; margin-top: 0.5rem;">
                                        <small style="color: #10b981;">✓ Verified as: <strong>{result['verified_species']}</strong></small>
                                    </div>
                                    """, unsafe_allow_html=True)
                
                # Save to database button
                if verified_count > 0:
                    st.markdown("---")
                    st.markdown('<p class="section-header">💾 Save Verified Results</p>', unsafe_allow_html=True)
                    
                    st.info(f"📊 **{verified_count}** results ready to save to database")
                    
                    if st.button("💾 Save All Verified Results to Database", key="save_image_results", type="primary"):
                        from detection_logger import get_detection_logger
                        logger = get_detection_logger()
                        
                        saved_count = 0
                        verified_results = [r for r in st.session_state.image_results 
                                          if r['verification_status'] in ['verified', 'corrected']]
                        
                        for result in verified_results:
                            try:
                                logger.log_detection(
                                    image_name=result['image_name'],
                                    species=result['verified_species'],
                                    confidence=float(result['confidence']),
                                    location=st.session_state.image_location if st.session_state.image_location else None,
                                    ai_prediction=result['ai_prediction'],
                                    verified=True,
                                    corrected_by_user=(result['verification_status'] == 'corrected')
                                )
                                saved_count += 1
                            except Exception as e:
                                st.warning(f"⚠️ Failed to save {result['image_name']}: {e}")
                        
                        st.success(f"✅ Successfully saved **{saved_count}** verified detections to database!")
                        
                        # Calculate statistics for verified results
                        species_counts = {}
                        confidences = []
                        for result in verified_results:
                            species = result['verified_species']
                            species_counts[species] = species_counts.get(species, 0) + 1
                            confidences.append(result['confidence'])
                        
                        total_detected = sum(species_counts.values())
                        unique_species = len(species_counts)
                        avg_confidence = np.mean(confidences) if confidences else 0
                        
                        # Display results summary
                        st.markdown("---")
                        st.markdown('<p class="section-header">Analysis Results</p>', unsafe_allow_html=True)
                        
                        # Summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown(f"""
                            <div class="metric-card">
                                <p class="metric-value">{len(st.session_state.image_results)}</p>
                                <p class="metric-label">Images Processed</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div class="metric-card">
                                <p class="metric-value">{total_detected}</p>
                                <p class="metric-label">Total Detections</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col3:
                            st.markdown(f"""
                            <div class="metric-card">
                                <p class="metric-value">{unique_species}</p>
                                <p class="metric-label">Unique Species</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col4:
                            st.markdown(f"""
                            <div class="metric-card">
                                <p class="metric-value">{avg_confidence:.1%}</p>
                                <p class="metric-label">Avg Confidence</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Visualizations
                        if total_detected > 0:
                            # Enhanced Species Distribution Dashboard
                            st.markdown('<p class="section-header">📊 Species Distribution Dashboard</p>', unsafe_allow_html=True)
                            
                            viz = PlanktonVisualizer()
                            
                            # 2-column layout for charts
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 📈 Top Species (Bar Chart)")
                                fig_bar = viz.create_species_bar_chart(species_counts, top_n=15)
                                st.pyplot(fig_bar)
                            
                            with col2:
                                st.markdown("#### 🥧 Species Composition (Pie Chart)")
                                fig_pie = viz.create_species_pie_chart(species_counts, top_n=10)
                                st.pyplot(fig_pie)
                            
                            # Detailed results table
                            st.markdown("---")
                            st.markdown('<p class="section-header">📋 Detailed Results Table</p>', unsafe_allow_html=True)
                            df = pd.DataFrame(verified_results)
                            st.dataframe(df, use_container_width=True)
                            
                            # Export options
                            st.markdown('<p class="section-header">📥 Export Results</p>', unsafe_allow_html=True)
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                csv_data = df.to_csv(index=False)
                                st.download_button(
                                    "📥 Download CSV",
                                    csv_data,
                                    "plankton_results.csv",
                                    "text/csv"
                                )
                            
                            with col2:
                                json_data = df.to_json(orient='records', indent=2)
                                st.download_button(
                                    "📥 Download JSON",
                                    json_data,
                                    "plankton_results.json",
                                    "application/json"
                                )
                            
                            with col3:
                                # Summary statistics
                                summary = ResultsExporter.create_summary_dict(
                                    species_counts, confidences, total_detected
                                )
                                summary_json = json.dumps(summary, indent=2)
                                st.download_button(
                                    "📥 Download Summary",
                                    summary_json,
                                    "plankton_summary.json",
                                    "application/json"
                                )
                            
                            # Clear results button
                            if st.button("🔄 Clear Results & Start New Analysis", key="clear_image_results"):
                                st.session_state.image_results = []
                                st.session_state.image_data = {}
                                st.session_state.image_location = ""
                                st.rerun()
        
        # Recent Detections from Database
        st.markdown("---")
        st.markdown('<p class="section-header">📊 Recent Detections from Database</p>', unsafe_allow_html=True)
        
        try:
            from detection_logger import get_detection_logger
            logger = get_detection_logger()
            
            total_detections = logger.get_detection_count()
            st.info(f"💾 Total detections in database: **{total_detections}**")
            
            if total_detections > 0:
                recent = logger.get_recent_detections(limit=10)
                
                if recent:
                    df_recent = pd.DataFrame(recent, columns=[
                        "ID", "Image", "Species", "Confidence", "DateTime", "Location"
                    ])
                    st.dataframe(df_recent, use_container_width=True)
                else:
                    st.info("No recent detections found")
            else:
                st.info("No detections logged yet. Analyze some images to start logging!")
        except Exception as e:
            st.warning(f"⚠️ Could not load detection history: {e}")
    
    # ==================== VIDEO ANALYSIS TAB ====================
    with tab2:
        st.markdown('<p class="section-header">Video Frame-by-Frame Analysis</p>', unsafe_allow_html=True)
        
        uploaded_video = st.file_uploader(
            "Upload plankton video",
            type=['mp4', 'avi', 'mov'],
            help="Upload a video for frame-by-frame analysis"
        )
        
        if uploaded_video:
            # Save video temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(uploaded_video.read())
                video_path = tmp_file.name
            
            try:
                # Get video info
                video_proc = VideoProcessor(video_path)
                video_info = video_proc.get_video_info()
                
                # Display video info
                st.markdown('<div class="info-box">', unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Duration", video_info['duration_formatted'])
                col2.metric("FPS", f"{video_info['fps']:.1f}")
                col3.metric("Frames", video_info['frame_count'])
                col4.metric("Resolution", f"{video_info['width']}x{video_info['height']}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Calculate frame sampling
                sample_rate = int(video_info['fps'] / video_fps)
                estimated_frames = video_info['frame_count'] // sample_rate
                
                st.info(f"📊 Will process approximately {estimated_frames} frames at {video_fps} FPS sampling rate")
                
                if st.button("🎬 Analyze Video", key="analyze_video"):
                    results = []
                    species_counts = {cls: 0 for cls in classes}
                    confidences = []
                    frame_results = []
                    frames_for_video = []  # Store frames for annotated video
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Process frames
                    frame_count = 0
                    for frame_idx, pil_image, timestamp in video_proc.extract_frames_pil(sample_rate=sample_rate):
                        status_text.text(f"Processing frame {frame_count+1}/{estimated_frames} (t={timestamp:.2f}s)")
                        
                        # Convert PIL to numpy for storage
                        frame_array = np.array(pil_image)
                        
                        # Predict
                        pred_idx, confidence, all_probs = predict_image(model, pil_image, device)
                        predicted_class = classes[pred_idx]
                        
                        # Store frame with detection info for video generation
                        frames_for_video.append((frame_array, predicted_class, confidence, timestamp))
                        
                        if confidence >= confidence_threshold:
                            species_counts[predicted_class] += 1
                            confidences.append(confidence)
                            
                            frame_results.append({
                                'frame': frame_idx,
                                'timestamp': f"{timestamp:.2f}s",
                                'species': predicted_class,
                                'confidence': confidence
                            })
                        
                        frame_count += 1
                        progress_bar.progress(min(frame_count / estimated_frames, 1.0))
                    
                    status_text.empty()
                    progress_bar.empty()
                    
                    # Display results (similar to image analysis)
                    st.markdown('<p class="section-header">Video Analysis Results</p>', unsafe_allow_html=True)
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    total_detected = sum(species_counts.values())
                    unique_species = len([v for v in species_counts.values() if v > 0])
                    avg_confidence = np.mean(confidences) if confidences else 0
                    
                    with col1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <p class="metric-value">{frame_count}</p>
                            <p class="metric-label">Frames Analyzed</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="metric-card">
                            <p class="metric-value">{total_detected}</p>
                            <p class="metric-label">Total Detections</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                        <div class="metric-card">
                            <p class="metric-value">{unique_species}</p>
                            <p class="metric-label">Unique Species</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        st.markdown(f"""
                        <div class="metric-card">
                            <p class="metric-value">{avg_confidence:.1%}</p>
                            <p class="metric-label">Avg Confidence</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if total_detected > 0:
                        # Visualizations
                        st.markdown('<p class="section-header">Species Distribution</p>', unsafe_allow_html=True)
                        
                        viz = PlanktonVisualizer()
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_bar = viz.create_species_bar_chart(species_counts, top_n=15)
                            st.pyplot(fig_bar)
                        
                        with col2:
                            fig_pie = viz.create_species_pie_chart(species_counts, top_n=10)
                            st.pyplot(fig_pie)
                        
                        # Timeline view
                        st.markdown('<p class="section-header">Detection Timeline</p>', unsafe_allow_html=True)
                        df_frames = pd.DataFrame(frame_results)
                        st.dataframe(df_frames, use_container_width=True)
                        
                        # Export
                        st.markdown('<p class="section-header">Export Results</p>', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            csv_data = df_frames.to_csv(index=False)
                            st.download_button(
                                "📥 Download Timeline CSV",
                                csv_data,
                                "video_timeline.csv",
                                "text/csv"
                            )
                        
                        with col2:
                            summary = ResultsExporter.create_summary_dict(
                                species_counts, confidences, total_detected
                            )
                            summary['video_info'] = video_info
                            summary_json = json.dumps(summary, indent=2)
                            st.download_button(
                                "📥 Download Summary",
                                summary_json,
                                "video_summary.json",
                                "application/json"
                            )
                        
                        # Generate annotated video with detections
                        if frames_for_video:
                            st.markdown('<p class="section-header">📹 Annotated Video Playback</p>', unsafe_allow_html=True)
                            
                            with st.spinner("Generating annotated video with bounding boxes..."):
                                # Create annotator
                                annotator = VideoAnnotator()
                                
                                # Generate annotated video with unique filename
                                import time
                                timestamp = int(time.time())
                                annotated_video_path = os.path.join(tempfile.gettempdir(), f'plankton_annotated_{timestamp}.mp4')
                                
                                try:
                                    annotator.create_annotated_video(
                                        frames_for_video,
                                        annotated_video_path,
                                        fps=video_fps
                                    )
                                    
                                    # Verify video was created
                                    if not os.path.exists(annotated_video_path):
                                        st.error("Failed to create annotated video file")
                                    elif os.path.getsize(annotated_video_path) == 0:
                                        st.error("Annotated video file is empty")
                                    else:
                                        # Display video player
                                        st.success("✅ Annotated video generated successfully!")
                                        
                                        col1, col2 = st.columns([2, 1])
                                        
                                        with col1:
                                            # Read video file and display
                                            with open(annotated_video_path, 'rb') as video_file:
                                                video_bytes = video_file.read()
                                            st.video(video_bytes)
                                            st.caption("🎬 Video with species detection bounding boxes and labels")
                                        
                                        with col2:
                                            st.markdown("""
                                            **Video Features:**
                                            - 🎯 Bounding boxes around detections
                                            - 🏷️ Species labels with confidence
                                            - ⏱️ Timestamp overlay
                                            - 🎨 Color-coded by species
                                            """)
                                            
                                            # Download button for annotated video
                                            st.download_button(
                                                "📥 Download Annotated Video",
                                                video_bytes,
                                                "plankton_annotated.mp4",
                                                "video/mp4",
                                                key="download_annotated_video"
                                            )
                                
                                except Exception as e:
                                    st.error(f"Error generating annotated video: {str(e)}")
                                    import traceback
                                    st.code(traceback.format_exc())
                                
                                finally:
                                    # Cleanup annotated video file after a delay
                                    # (Streamlit needs time to serve the file)
                                    pass  # Don't delete immediately, let temp dir cleanup handle it
                    
                    else:
                        st.warning("⚠️ No detections above confidence threshold.")
                
            finally:
                # Cleanup - explicitly close video processor first
                if 'video_proc' in locals():
                    video_proc.close()
                
                # Now safe to delete the temporary file
                if os.path.exists(video_path):
                    try:
                        os.unlink(video_path)
                    except PermissionError:
                        # If still locked, just pass - it will be cleaned up later
                        pass
    
    # ==================== SQL AGENT CHAT TAB ====================
    with tab4:
        st.markdown('<p class="section-header">💬 Chat with Database</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
            <strong>🤖 Intelligent Multi-Database SQL Agent</strong><br>
            Ask questions in plain English! The AI automatically routes your query to the right database:<br><br>
            <strong style="color: #3b82f6;">🔵 Detection Database (detection_db.db)</strong> - Live detection logs with dates, locations, confidence<br>
            <strong style="color: #8b5cf6;">🟣 Species Data (data.db)</strong> - Static species counts and classifications<br><br>
            <em>Example: "Show detections from last week" → Detection DB | "List all species" → Species Data</em>
        </div>
        """, unsafe_allow_html=True)
        
        # Hardcoded API key - Replace with your actual Groq API key
        GROQ_API_KEY = "YOUR_GROQ_API_KEY_HERE"  # ← Put your API key here
        
        if GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
            st.warning("⚠️ Please set your Groq API key in the code (line ~730 in streamlit_app.py)")
            st.info("💡 Get your free API key at: https://console.groq.com/keys")
        else:
            try:
                from sql_agent import create_plankton_agent
                
                # Create agent (cached in session state)
                if 'sql_agent' not in st.session_state:
                    with st.spinner("🔄 Initializing SQL Agent..."):
                        st.session_state.sql_agent = create_plankton_agent(groq_api_key=GROQ_API_KEY)
                    st.success("✅ SQL Agent ready!")
                
                agent = st.session_state.sql_agent
                
                # Initialize chat history
                if 'chat_history' not in st.session_state:
                    st.session_state.chat_history = []
                
                # Example questions in sidebar
                with st.sidebar:
                    st.markdown("---")
                    st.markdown("### 💡 Example Questions")
                    example_questions = agent.get_example_questions()
                    for i, question in enumerate(example_questions[:5]):
                        if st.button(f"📝 {question}", key=f"example_{i}", use_container_width=True):
                            st.session_state.current_question = question
                            st.rerun()
                    
                    if st.button("🗑️ Clear Chat", use_container_width=True):
                        st.session_state.chat_history = []
                        st.rerun()
                
                # Display chat history
                st.markdown("### 💬 Conversation")
                for message in st.session_state.chat_history:
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div style="background: #1e293b; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #3b82f6;">
                            <strong>👤 You:</strong><br>{message["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: #0f172a; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #10b981;">
                            <strong>🤖 Assistant:</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if message.get("success"):
                            # Show which database was used
                            if message.get("database_used"):
                                db_color = "#3b82f6" if "detection" in message["database_used"].lower() else "#8b5cf6"
                                st.markdown(f"""
                                <div style="background: {db_color}; padding: 0.3rem 0.6rem; border-radius: 4px; 
                                            display: inline-block; margin-bottom: 0.5rem; font-size: 0.85rem;">
                                    🗄️ <strong>Database:</strong> {message["database_used"]}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown(message["content"])
                            if message.get("sql_query") and message["sql_query"] != "SQL query not available":
                                with st.expander("📝 View SQL Query"):
                                    st.code(message["sql_query"], language="sql")
                        else:
                            st.error(f"❌ Error: {message.get('error', 'Unknown error')}")
                
                # Input area
                st.markdown("---")
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    user_question = st.text_input(
                        "Ask a question",
                        placeholder="e.g., What are the top 10 most common species?",
                        key="user_input",
                        value=st.session_state.get('current_question', ''),
                        label_visibility="collapsed"
                    )
                
                with col2:
                    send_button = st.button("📤 Send", use_container_width=True, type="primary")
                
                # Clear current_question after use
                if 'current_question' in st.session_state:
                    del st.session_state.current_question
                
                # Process question
                if send_button and user_question:
                    # Add user message
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": user_question
                    })
                    
                    # Query database
                    with st.spinner("🤔 Thinking..."):
                        result = agent.query(user_question)
                    
                    # Add assistant response
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": result.get("answer", "No answer generated"),
                        "sql_query": result.get("sql_query"),
                        "success": result.get("success"),
                        "error": result.get("error"),
                        "database_used": result.get("database_used")
                    })
                    
                    st.rerun()
                
                # Database info
                if st.checkbox("ℹ️ Show Database Schema"):
                    st.markdown("### 📊 Database Schema")
                    schema_info = agent.get_schema_info()
                    st.code(schema_info, language="sql")
                    
                    st.markdown("### 📋 Sample Data")
                    sample_data = agent.get_sample_data()
                    if sample_data:
                        df_sample = pd.DataFrame(sample_data, columns=["ID", "Image", "Species", "Confidence", "DateTime", "Location", "Created At"])
                        st.dataframe(df_sample, use_container_width=True)
            
            except ImportError as e:
                import traceback
                st.error(f"❌ Error importing SQL agent: {e}")
                st.code(traceback.format_exc(), language="python")
                st.info("💡 Make sure sql_agent.py is in the app directory and has no syntax errors")
            except Exception as e:
                import traceback
                st.error(f"❌ Error initializing SQL agent: {e}")
                st.code(traceback.format_exc(), language="python")
                st.info("💡 Check your Groq API key and database path")
    
    # ==================== BATCH PROCESSING TAB ====================
    with tab3:
        st.markdown('<p class="section-header">Batch Processing</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
        <h4>📦 Batch Processing Features:</h4>
        <ul>
            <li>Upload multiple images from field collection</li>
            <li>AI analyzes all images automatically</li>
            <li>Review and verify each detection</li>
            <li>Correct any misidentifications</li>
            <li>Save verified results to database</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize session state for batch processing
        if 'batch_results' not in st.session_state:
            st.session_state.batch_results = []
        if 'batch_images' not in st.session_state:
            st.session_state.batch_images = {}
        if 'batch_location' not in st.session_state:
            st.session_state.batch_location = ""
        
        # Batch upload
        st.markdown("### 📁 Upload Batch Images")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            uploaded_batch = st.file_uploader(
                "Upload multiple plankton images from field collection",
                type=['png', 'jpg', 'jpeg', 'tiff', 'tif'],
                accept_multiple_files=True,
                help="Select all images from your offline collection",
                key="batch_uploader"
            )
        
        with col2:
            batch_location = st.text_input(
                "Collection Location",
                value="Varanasi, UP, India",
                placeholder="e.g., Varanasi",
                help="Where were these samples collected?"
            )
        
        if uploaded_batch:
            st.info(f"📁 **{len(uploaded_batch)} images** uploaded for batch processing")
            
            if st.button("🔍 Analyze Batch", key="analyze_batch", type="primary"):
                # Clear previous results
                st.session_state.batch_results = []
                st.session_state.batch_images = {}
                st.session_state.batch_location = batch_location
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process all images
                for idx, uploaded_file in enumerate(uploaded_batch):
                    status_text.text(f"Analyzing {idx+1}/{len(uploaded_batch)}: {uploaded_file.name}")
                    
                    # Load image
                    image = Image.open(uploaded_file)
                    
                    # Store image for display
                    st.session_state.batch_images[uploaded_file.name] = image.copy()
                    
                    # Predict
                    pred_idx, confidence, all_probs = predict_image(model, image, device)
                    predicted_class = classes[pred_idx]
                    
                    # Store result (not saved to DB yet - waiting for verification)
                    st.session_state.batch_results.append({
                        'image_name': uploaded_file.name,
                        'ai_prediction': predicted_class,
                        'confidence': confidence,
                        'verified_species': predicted_class,  # Default to AI prediction
                        'verification_status': 'pending',  # pending, verified, corrected
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    progress_bar.progress((idx + 1) / len(uploaded_batch))
                
                status_text.empty()
                progress_bar.empty()
                
                st.success(f"✅ Analysis complete! Please verify the results below.")
                st.rerun()
        
        # Display verification interface if results exist
        if st.session_state.batch_results:
            st.markdown("---")
            st.markdown('<p class="section-header">🔍 Verify Detection Results</p>', unsafe_allow_html=True)
            
            # Verification progress
            total_results = len(st.session_state.batch_results)
            verified_count = sum(1 for r in st.session_state.batch_results 
                               if r['verification_status'] in ['verified', 'corrected'])
            pending_count = total_results - verified_count
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Images", total_results)
            with col2:
                st.metric("Verified", verified_count, delta=f"{verified_count/total_results*100:.0f}%")
            with col3:
                st.metric("Pending", pending_count)
            
            # Bulk verification option
            if pending_count > 0:
                st.markdown("### ⚡ Bulk Actions")
                col1, col2 = st.columns(2)
                
                with col1:
                    confidence_threshold_bulk = st.slider(
                        "Auto-verify detections above confidence:",
                        min_value=0.5,
                        max_value=1.0,
                        value=0.9,
                        step=0.05,
                        help="Automatically verify high-confidence predictions"
                    )
                
                with col2:
                    if st.button(f"✅ Auto-Verify {sum(1 for r in st.session_state.batch_results if r['confidence'] >= confidence_threshold_bulk and r['verification_status'] == 'pending')} High-Confidence Results", 
                                key="bulk_verify"):
                        for result in st.session_state.batch_results:
                            if result['confidence'] >= confidence_threshold_bulk and result['verification_status'] == 'pending':
                                result['verification_status'] = 'verified'
                        st.success("✅ High-confidence results auto-verified!")
                        st.rerun()
            
            # Individual verification
            st.markdown("---")
            st.markdown("### 📋 Review Each Detection")
            
            # Display results in grid
            cols_per_row = 3
            for i in range(0, len(st.session_state.batch_results), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j, col in enumerate(cols):
                    if i + j < len(st.session_state.batch_results):
                        result = st.session_state.batch_results[i + j]
                        result_idx = i + j
                        
                        with col:
                            # Display image
                            if result['image_name'] in st.session_state.batch_images:
                                img = st.session_state.batch_images[result['image_name']]
                                st.image(img, use_column_width=True)
                            
                            # Verification status indicator
                            if result['verification_status'] == 'verified':
                                status_color = "#10b981"
                                status_icon = "✅"
                                status_text = "Verified"
                            elif result['verification_status'] == 'corrected':
                                status_color = "#f59e0b"
                                status_icon = "✏️"
                                status_text = "Corrected"
                            else:
                                status_color = "#6b7280"
                                status_icon = "⏳"
                                status_text = "Pending"
                            
                            # Display detection info
                            confidence_color = "#10b981" if result['confidence'] > 0.8 else "#f59e0b" if result['confidence'] > 0.6 else "#ef4444"
                            
                            st.markdown(f"""
                            <div style="background: #1e293b; padding: 0.8rem; border-radius: 8px; 
                                        border-left: 4px solid {status_color}; margin-top: -1rem;">
                                <div style="color: {status_color}; font-weight: bold; margin-bottom: 0.5rem;">
                                    {status_icon} {status_text}
                                </div>
                                <strong style="color: #3b82f6;">🤖 AI: {result['ai_prediction']}</strong><br>
                                <small style="color: #94a3b8;">
                                    📊 Confidence: <span style="color: {confidence_color};">{result['confidence']:.1%}</span><br>
                                    📁 {result['image_name'][:20]}...
                                </small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Verification buttons (only if pending)
                            if result['verification_status'] == 'pending':
                                st.markdown("<br>", unsafe_allow_html=True)
                                
                                btn_col1, btn_col2 = st.columns(2)
                                
                                with btn_col1:
                                    if st.button("✅ Correct", key=f"verify_{result_idx}", use_container_width=True):
                                        st.session_state.batch_results[result_idx]['verification_status'] = 'verified'
                                        st.rerun()
                                
                                with btn_col2:
                                    if st.button("❌ Wrong", key=f"wrong_{result_idx}", use_container_width=True):
                                        st.session_state.batch_results[result_idx]['verification_status'] = 'correcting'
                                        st.rerun()
                            
                            # Correction interface
                            elif result['verification_status'] == 'correcting':
                                st.markdown("<br>", unsafe_allow_html=True)
                                
                                # Add "Custom/Unknown" option to species list
                                species_options = ["🆕 Custom/Unknown Species"] + classes
                                
                                corrected_species = st.selectbox(
                                    "Select correct species:",
                                    options=species_options,
                                    key=f"correct_species_{result_idx}",
                                    index=0
                                )
                                
                                # If custom species selected, show text input
                                final_species = corrected_species
                                if corrected_species == "🆕 Custom/Unknown Species":
                                    custom_name = st.text_input(
                                        "Enter species name:",
                                        key=f"custom_species_{result_idx}",
                                        placeholder="e.g., Copepod sp. nov."
                                    )
                                    if custom_name:
                                        final_species = custom_name
                                    else:
                                        st.warning("⚠️ Please enter a species name")
                                
                                # Only enable save button if valid species selected
                                can_save = (corrected_species != "🆕 Custom/Unknown Species") or (corrected_species == "🆕 Custom/Unknown Species" and custom_name)
                                
                                if st.button("💾 Save Correction", key=f"save_correction_{result_idx}", use_container_width=True, disabled=not can_save):
                                    st.session_state.batch_results[result_idx]['verified_species'] = final_species
                                    st.session_state.batch_results[result_idx]['verification_status'] = 'corrected'
                                    st.rerun()
                            
                            # Show final verified species if corrected
                            elif result['verification_status'] == 'corrected':
                                st.markdown(f"""
                                <div style="background: #0f172a; padding: 0.5rem; border-radius: 4px; margin-top: 0.5rem;">
                                    <small style="color: #10b981;">✓ Verified as: <strong>{result['verified_species']}</strong></small>
                                </div>
                                """, unsafe_allow_html=True)
            
            # Save to database button
            if verified_count > 0:
                st.markdown("---")
                st.markdown('<p class="section-header">💾 Save Verified Results</p>', unsafe_allow_html=True)
                
                st.info(f"📊 **{verified_count}** results ready to save to database")
                
                if st.button("💾 Save All Verified Results to Database", key="save_batch", type="primary"):
                    from detection_logger import get_detection_logger
                    logger = get_detection_logger()
                    
                    saved_count = 0
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    verified_results = [r for r in st.session_state.batch_results 
                                      if r['verification_status'] in ['verified', 'corrected']]
                    
                    for idx, result in enumerate(verified_results):
                        status_text.text(f"Saving {idx+1}/{len(verified_results)}: {result['image_name']}")
                        
                        try:
                            logger.log_detection(
                                image_name=result['image_name'],
                                species=result['verified_species'],
                                confidence=float(result['confidence']),
                                location=st.session_state.batch_location if st.session_state.batch_location else None,
                                ai_prediction=result['ai_prediction'],
                                verified=True,
                                corrected_by_user=(result['verification_status'] == 'corrected')
                            )
                            saved_count += 1
                        except Exception as e:
                            st.warning(f"⚠️ Failed to save {result['image_name']}: {e}")
                        
                        progress_bar.progress((idx + 1) / len(verified_results))
                    
                    status_text.empty()
                    progress_bar.empty()
                    
                    st.success(f"✅ Successfully saved **{saved_count}** verified detections to database!")
                    
                    # Generate summary statistics
                    st.markdown("---")
                    st.markdown('<p class="section-header">📊 Batch Summary</p>', unsafe_allow_html=True)
                    
                    species_counts = {}
                    for result in verified_results:
                        species = result['verified_species']
                        species_counts[species] = species_counts.get(species, 0) + 1
                    
                    # Display summary
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Total Saved", saved_count)
                    with col2:
                        st.metric("Unique Species", len(species_counts))
                    with col3:
                        corrections = sum(1 for r in verified_results if r['verification_status'] == 'corrected')
                        st.metric("User Corrections", corrections)
                    
                    # Species distribution
                    if species_counts:
                        viz = PlanktonVisualizer()
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            fig_bar = viz.create_species_bar_chart(species_counts, top_n=15)
                            st.pyplot(fig_bar)
                        
                        with col2:
                            fig_pie = viz.create_species_pie_chart(species_counts, top_n=10)
                            st.pyplot(fig_pie)
                    
                    # Export options
                    st.markdown("---")
                    st.markdown('<p class="section-header">📥 Export Results</p>', unsafe_allow_html=True)
                    
                    df_batch = pd.DataFrame(verified_results)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv_data = df_batch.to_csv(index=False)
                        st.download_button(
                            "📥 Download Batch Results (CSV)",
                            csv_data,
                            "batch_results.csv",
                            "text/csv"
                        )
                    
                    with col2:
                        json_data = df_batch.to_json(orient='records', indent=2)
                        st.download_button(
                            "📥 Download Batch Results (JSON)",
                            json_data,
                            "batch_results.json",
                            "application/json"
                        )
                    
                    # Clear batch after saving
                    if st.button("🔄 Start New Batch", key="clear_batch"):
                        st.session_state.batch_results = []
                        st.session_state.batch_images = {}
                        st.session_state.batch_location = ""
                        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; padding: 1rem;">
        <p>🔬 Marine Plankton Detection System | Powered by MobileNetV3 Deep Learning</p>
        <p style="font-size: 0.8rem;">For research and educational purposes</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
