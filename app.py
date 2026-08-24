
import streamlit as st
import pandas as pd
import re
from datetime import datetime
import io
import docx2txt
import PyPDF2
import language_tool_python
import time
import random
 
# Initialize language tool for grammar checking
@st.cache_resource
def load_language_tool():
    return language_tool_python.LanguageTool('en-US')
 
class ProofreadingEngine:
    def __init__(self):
        self.lt = load_language_tool()
        
    def extract_text(self, uploaded_file):
        """Extract text from various file formats"""
        file_type = uploaded_file.type
        text = ""
        
        if file_type == "text/plain":
            text = uploaded_file.read().decode('utf-8')
            
        elif file_type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text = docx2txt.process(uploaded_file)
            
        else:
            st.error(f"Unsupported file type: {file_type}")
            return None
            
        return text
    
    def check_spelling_grammar(self, text):
        """Check spelling and grammar using LanguageTool"""
        matches = self.lt.check(text)
        issues = []
        
        for match in matches:
            issues.append({
                'Type': match.ruleId,
                'Message': match.message,
                'Replacements': ', '.join(match.replacements[:3]) if match.replacements else 'N/A',
                'Context': match.context,
                'Position': f"{match.offset}-{match.offset + match.errorLength}"
            })
        
        return issues
    
    def check_readability(self, text):
        """Calculate readability metrics"""
        sentences = re.split(r'[.!?]+', text)
        words = re.findall(r'\b\w+\b', text)
        
        avg_sentence_len = len(words) / len(sentences) if sentences else 0
        avg_word_len = sum(len(word) for word in words) / len(words) if words else 0
        
        if len(sentences) > 0 and len(words) > 0:
            flesch_score = 206.835 - 1.015 * (len(words)/len(sentences)) - 84.6 * (avg_word_len)
        else:
            flesch_score = 0
            
        return {
            'Total Words': len(words),
            'Total Sentences': len(sentences),
            'Avg Sentence Length': round(avg_sentence_len, 2),
            'Avg Word Length': round(avg_word_len, 2),
            'Flesch Reading Ease': round(flesch_score, 2)
        }
    
    def check_style_issues(self, text):
        """Check for style issues like passive voice, weak words, etc."""
        issues = []
        
        passive_pattern = r'\b(be|am|are|is|was|were|been|being)\s+\w+ed\b'
        passive_matches = re.findall(passive_pattern, text, re.I)
        if passive_matches:
            issues.append({
                'Type': 'Style',
                'Issue': 'Passive Voice',
                'Count': len(passive_matches),
                'Suggestion': 'Consider using active voice for clearer writing'
            })
        
        wordiness_patterns = {
            r'\bin order to\b': 'to',
            r'\bdue to the fact that\b': 'because',
            r'\bin the event that\b': 'if',
            r'\bat this point in time\b': 'now'
        }
        
        for pattern, suggestion in wordiness_patterns.items():
            matches = re.findall(pattern, text, re.I)
            if matches:
                issues.append({
                    'Type': 'Style',
                    'Issue': f'Wordy phrase: "{pattern.strip()}"',
                    'Count': len(matches),
                    'Suggestion': f'Consider using "{suggestion}" instead'
                })
        
        return issues
    
    def generate_report(self, text):
        """Generate comprehensive proofreading report"""
        report = {}
        report['Basic Stats'] = self.check_readability(text)
        report['Grammar Issues'] = self.check_spelling_grammar(text)
        report['Style Issues'] = self.check_style_issues(text)
        return report
 
# Streamlit UI
st.set_page_config(
    page_title="Global Vision - Proofreading Software",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# ============ ANIMATED CSS ============
st.markdown("""
<style>
@keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0; }
    100% { opacity: 1; }
}
 
@keyframes scanline {
    0% { transform: translateY(-100%); }
    100% { transform: translateY(100%); }
}
 
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
 
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}
 
@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}
 
@keyframes glowPulse {
    0% { box-shadow: 0 0 5px #1f77b4; }
    50% { box-shadow: 0 0 20px #1f77b4, 0 0 30px #1f77b4; }
    100% { box-shadow: 0 0 5px #1f77b4; }
}
 
.main-header {
    font-size: 3rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    animation: fadeInUp 0.8s ease-out;
    text-shadow: 2px 2px 4px rgba(31, 119, 180, 0.3);
}
 
.blinking-cursor {
    display: inline-block;
    width: 3px;
    height: 2em;
    background-color: #1f77b4;
    animation: blink 1s step-end infinite;
    vertical-align: text-bottom;
    margin-left: 2px;
}
 
.scanning-effect {
    position: relative;
    overflow: hidden;
    background: linear-gradient(180deg,
        transparent 0%,
        rgba(31, 119, 180, 0.05) 50%,
        transparent 100%);
    animation: scanline 3s linear infinite;
}
 
.metric-card {
    background: linear-gradient(135deg, #f0f2f6, #e8ebf0);
    padding: 1.5rem;
    border-radius: 15px;
    border-left: 5px solid #1f77b4;
    margin: 0.5rem 0;
    transition: all 0.3s ease;
    animation: fadeInUp 0.6s ease-out;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
 
.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 15px rgba(31, 119, 180, 0.2);
    border-left-color: #ff7f0e;
}
 
.issue-card {
    background: linear-gradient(135deg, #fff3cd, #ffe69b);
    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #ffc107;
    margin: 0.5rem 0;
    animation: fadeInUp 0.5s ease-out;
    transition: all 0.3s ease;
}
 
.issue-card:hover {
    transform: translateX(10px);
    box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3);
}
 
.error-card {
    background: linear-gradient(135deg, #f8d7da, #f5c6cb);
    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #dc3545;
    margin: 0.5rem 0;
    animation: fadeInUp 0.5s ease-out;
    transition: all 0.3s ease;
}
 
.error-card:hover {
    transform: translateX(10px);
    box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
}
 
.success-card {
    background: linear-gradient(135deg, #d4edda, #b7e4c7);
    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #28a745;
    margin: 0.5rem 0;
    animation: fadeInUp 0.5s ease-out;
}
 
.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 1.5s ease-in-out infinite;
}
 
.status-active {
    background-color: #28a745;
    box-shadow: 0 0 10px #28a745;
}
 
.status-processing {
    background-color: #ffc107;
    box-shadow: 0 0 10px #ffc107;
}
 
.status-idle {
    background-color: #6c757d;
}
 
.progress-bar-animated {
    background: linear-gradient(90deg,
        #1f77b4 0%,
        #ff7f0e 50%,
        #1f77b4 100%);
    background-size: 200% auto;
    animation: shimmer 2s linear infinite;
    height: 4px;
    border-radius: 2px;
    margin: 10px 0;
}
 
.upload-zone {
    border: 3px dashed #1f77b4;
    border-radius: 20px;
    padding: 3rem;
    text-align: center;
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    transition: all 0.5s ease;
    animation: glowPulse 3s ease-in-out infinite;
}
 
.upload-zone:hover {
    transform: scale(1.02);
    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
    border-color: #ff7f0e;
}
 
.glow-text {
    color: #1f77b4;
    text-shadow: 0 0 10px rgba(31, 119, 180, 0.5);
}
 
.stats-number {
    font-size: 2.5rem;
    font-weight: bold;
    background: linear-gradient(135deg, #1f77b4, #ff7f0e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: pulse 2s ease-in-out infinite;
}
 
.stats-label {
    color: #495057;
    font-weight: 500;
}
 
.tab-transition {
    animation: fadeInUp 0.8s ease-out;
}
 
/* Scrollbar styling */
::-webkit-scrollbar {
    width: 10px;
}
::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}
::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #1f77b4, #ff7f0e);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #ff7f0e, #1f77b4);
}
</style>
""", unsafe_allow_html=True)
 
# ============ HEADER WITH BLINKING CURSOR ============
st.markdown('''
<div class="main-header">
    📝 Global Vision
    <span style="color: #ff7f0e;">Proofreading</span>
    <span class="blinking-cursor"></span>
</div>
''', unsafe_allow_html=True)
 
# ============ STATUS INDICATOR ============
status_col1, status_col2, status_col3 = st.columns([1, 2, 1])
with status_col2:
    status_placeholder = st.empty()
    status_placeholder.markdown('''
    <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 10px; margin-bottom: 20px;">
        <span class="status-indicator status-idle"></span>
        <span style="color: #6c757d; font-weight: 500;">System Ready • Waiting for document</span>
    </div>
    ''', unsafe_allow_html=True)
 
# Sidebar for file upload
with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1f77b4, #0d47a1);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 20px;
                text-align: center;">
        <h3 style="color: white; margin: 0;">📤 Upload Center</h3>
        <p style="color: #bbdefb; margin: 5px 0 0 0;">Drag & drop or click to upload</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['txt', 'pdf', 'docx'],
        help="Supported formats: TXT, PDF, DOCX",
        key="file_uploader"
    )
    
    # Animated progress bar (hidden initially)
    progress_placeholder = st.empty()
    
    st.markdown("---")
    
    st.markdown("""
    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
        <h4 style="color: #1f77b4;">📋 Features</h4>
        <ul style="list-style: none; padding: 0;">
            <li style="padding: 5px 0;">✅ Grammar & Spelling</li>
            <li style="padding: 5px 0;">✅ Style Analysis</li>
            <li style="padding: 5px 0;">✅ Readability Metrics</li>
            <li style="padding: 5px 0;">✅ Passive Voice Detection</li>
            <li style="padding: 5px 0;">✅ Wordiness Detection</li>
        </ul>
    </div>
    """, unsafe_all
