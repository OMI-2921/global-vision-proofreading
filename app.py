import streamlit as st
import pandas as pd
import re
import io
import docx2txt
import PyPDF2
import language_tool_python
import tempfile


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Global Vision - Proofreading Software",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# LANGUAGE TOOL
# ============================================================

@st.cache_resource
def load_language_tool():
    """
    Load LanguageTool once and reuse it across Streamlit reruns.
    """
    try:
        return language_tool_python.LanguageTool("en-US")
    except Exception as e:
        return None


# ============================================================
# PROOFREADING ENGINE
# ============================================================

class ProofreadingEngine:

    def __init__(self):
        self.lt = load_language_tool()

    # --------------------------------------------------------
    # TEXT EXTRACTION
    # --------------------------------------------------------

    def extract_text(self, uploaded_file):
        """Extract text from TXT, PDF and DOCX files."""

        if uploaded_file is None:
            return None

        file_name = uploaded_file.name.lower()

        try:

            # TXT
            if file_name.endswith(".txt"):
                return uploaded_file.getvalue().decode(
                    "utf-8",
                    errors="ignore"
                )

            # PDF
            elif file_name.endswith(".pdf"):

                pdf_reader = PyPDF2.PdfReader(
                    io.BytesIO(uploaded_file.getvalue())
                )

                extracted_text = []

                for page in pdf_reader.pages:
                    page_text = page.extract_text()

                    if page_text:
                        extracted_text.append(page_text)

                return "\n".join(extracted_text)

            # DOCX
            elif file_name.endswith(".docx"):

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".docx"
                ) as temp_file:

                    temp_file.write(uploaded_file.getvalue())
                    temp_path = temp_file.name

                return docx2txt.process(temp_path)

            else:
                return None

        except Exception as e:
            st.error(f"Error reading file: {e}")
            return None

    # --------------------------------------------------------
    # GRAMMAR AND SPELLING
    # --------------------------------------------------------

    def check_spelling_grammar(self, text):

        if not self.lt:
            return []

        if not text or not text.strip():
            return []

        try:

            matches = self.lt.check(text)

            issues = []

            for match in matches:

                replacements = (
                    ", ".join(match.replacements[:5])
                    if match.replacements
                    else "No suggestion"
                )

                issues.append({
                    "Type": match.ruleId,
                    "Category": (
                        match.category
                        if hasattr(match, "category")
                        else "General"
                    ),
                    "Message": match.message,
                    "Suggestions": replacements,
                    "Context": match.context,
                    "Position":
                        f"{match.offset} - "
                        f"{match.offset + match.errorLength}"
                })

            return issues

        except Exception as e:
            st.warning(
                f"Grammar engine could not complete the check: {e}"
            )
            return []

    # --------------------------------------------------------
    # SYLLABLE COUNT
    # --------------------------------------------------------

    def count_syllables(self, word):

        word = word.lower()
        word = re.sub(r"[^a-z]", "", word)

        if len(word) <= 3:
            return 1 if word else 0

        vowels = "aeiouy"

        count = 0
        previous_was_vowel = False

        for char in word:

            is_vowel = char in vowels

            if is_vowel and not previous_was_vowel:
                count += 1

            previous_was_vowel = is_vowel

        if word.endswith("e") and count > 1:
            count -= 1

        return max(count, 1)

    # --------------------------------------------------------
    # READABILITY
    # --------------------------------------------------------

    def check_readability(self, text):

        if not text:
            return {
                "Total Words": 0,
                "Total Sentences": 0,
                "Avg Sentence Length": 0,
                "Avg Word Length": 0,
                "Flesch Reading Ease": 0,
                "Grade Level": "N/A"
            }

        words = re.findall(r"\b[\w'-]+\b", text)

        sentences = [
            sentence.strip()
            for sentence in re.split(r"[.!?]+", text)
            if sentence.strip()
        ]

        total_words = len(words)
        total_sentences = len(sentences)

        avg_sentence_len = (
            total_words / total_sentences
            if total_sentences > 0
            else 0
        )

        avg_word_len = (
            sum(len(word) for word in words) / total_words
            if total_words > 0
            else 0
        )

        syllables = sum(
            self.count_syllables(word)
            for word in words
        )

        if total_words > 0 and total_sentences > 0:

            flesch_score = (
                206.835
                - 1.015 * (total_words / total_sentences)
                - 84.6 * (syllables / total_words)
            )

        else:
            flesch_score = 0

        # Reading level
        if flesch_score >= 90:
            grade_level = "Very Easy"
        elif flesch_score >= 80:
            grade_level = "Easy"
        elif flesch_score >= 70:
            grade_level = "Fairly Easy"
        elif flesch_score >= 60:
            grade_level = "Standard"
        elif flesch_score >= 50:
            grade_level = "Fairly Difficult"
        elif flesch_score >= 30:
            grade_level = "Difficult"
        else:
            grade_level = "Very Difficult"

        return {
            "Total Words": total_words,
            "Total Sentences": total_sentences,
            "Avg Sentence Length": round(
                avg_sentence_len,
                2
            ),
            "Avg Word Length": round(
                avg_word_len,
                2
            ),
            "Flesch Reading Ease": round(
                flesch_score,
                2
            ),
            "Grade Level": grade_level
        }

    # --------------------------------------------------------
    # STYLE CHECKS
    # --------------------------------------------------------

    def check_style_issues(self, text):

        issues = []

        if not text:
            return issues

        # Passive voice
        passive_pattern = (
            r"\b(am|are|is|was|were|be|been|being)"
            r"\s+\w+(?:ed|en)\b"
        )

        passive_matches = re.findall(
            passive_pattern,
            text,
            re.IGNORECASE
        )

        if passive_matches:

            issues.append({
                "Type": "Style",
                "Issue": "Possible Passive Voice",
                "Count": len(passive_matches),
                "Suggestion":
                    "Consider using active voice where appropriate."
            })

        # Wordiness
        wordiness_patterns = {
            r"\bin order to\b": "to",
            r"\bdue to the fact that\b": "because",
            r"\bin the event that\b": "if",
            r"\bat this point in time\b": "now",
            r"\bfor the purpose of\b": "to",
            r"\bhas the ability to\b": "can",
            r"\bin spite of the fact that\b": "although",
            r"\bmake a decision\b": "decide",
            r"\bgive consideration to\b": "consider"
        }

        for pattern, suggestion in wordiness_patterns.items():

            matches = re.findall(
                pattern,
                text,
                re.IGNORECASE
            )

            if matches:

                clean_phrase = re.sub(
                    r"\\b",
                    "",
                    pattern
                )

                issues.append({
                    "Type": "Style",
                    "Issue":
                        f'Wordy phrase: "{clean_phrase}"',
                    "Count": len(matches),
                    "Suggestion":
                        f'Consider using "{suggestion}" instead.'
                })

        # Repeated words
        repeated_pattern = r"\b(\w+)\s+\1\b"

        repeated_words = re.findall(
            repeated_pattern,
            text,
            re.IGNORECASE
        )

        if repeated_words:

            issues.append({
                "Type": "Style",
                "Issue": "Repeated Words",
                "Count": len(repeated_words),
                "Suggestion":
                    "Check for accidentally repeated words."
            })

        # Excessive exclamation marks
        exclamation_matches = re.findall(r"!{2,}", text)

        if exclamation_matches:

            issues.append({
                "Type": "Style",
                "Issue": "Multiple Exclamation Marks",
                "Count": len(exclamation_matches),
                "Suggestion":
                    "Consider using a single exclamation mark."
            })

        return issues

    # --------------------------------------------------------
    # GENERATE REPORT
    # --------------------------------------------------------

    def generate_report(self, text):

        report = {}

        report["Basic Stats"] = (
            self.check_readability(text)
        )

        report["Grammar Issues"] = (
            self.check_spelling_grammar(text)
        )

        report["Style Issues"] = (
            self.check_style_issues(text)
        )

        return report


# ============================================================
# ANIMATED CSS
# ============================================================

st.markdown("""
<style>

@keyframes blink {
    0% { opacity: 1; }
    50% { opacity: 0; }
    100% { opacity: 1; }
}

@keyframes scanline {
    0% {
        transform: translateY(-100%);
    }

    100% {
        transform: translateY(100%);
    }
}

@keyframes pulse {
    0% {
        transform: scale(1);
    }

    50% {
        transform: scale(1.05);
    }

    100% {
        transform: scale(1);
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes shimmer {
    0% {
        background-position: -200% center;
    }

    100% {
        background-position: 200% center;
    }
}

@keyframes glowPulse {
    0% {
        box-shadow: 0 0 5px #1f77b4;
    }

    50% {
        box-shadow:
            0 0 20px #1f77b4,
            0 0 30px #1f77b4;
    }

    100% {
        box-shadow: 0 0 5px #1f77b4;
    }
}

.main-header {
    font-size: 3rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 1.5rem;
    animation: fadeInUp 0.8s ease-out;
    text-shadow:
        2px 2px 4px
        rgba(31, 119, 180, 0.3);
}

.blinking-cursor {
    display: inline-block;
    width: 3px;
    height: 1em;
    background-color: #1f77b4;
    animation: blink 1s step-end infinite;
    vertical-align: middle;
    margin-left: 5px;
}

.metric-card {
    background:
        linear-gradient(
            135deg,
            #f0f2f6,
            #e8ebf0
        );

    padding: 1.5rem;
    border-radius: 15px;
    border-left: 5px solid #1f77b4;
    margin: 0.5rem 0;
    transition: all 0.3s ease;
    animation: fadeInUp 0.6s ease-out;

    box-shadow:
        0 4px 6px
        rgba(0,0,0,0.1);
}

.metric-card:hover {
    transform: translateY(-5px);

    box-shadow:
        0 8px 15px
        rgba(31, 119, 180, 0.2);

    border-left-color: #ff7f0e;
}

.issue-card {
    background:
        linear-gradient(
            135deg,
            #fff3cd,
            #ffe69b
        );

    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #ffc107;
    margin: 0.5rem 0;

    animation: fadeInUp 0.5s ease-out;

    transition: all 0.3s ease;
}

.issue-card:hover {
    transform: translateX(10px);

    box-shadow:
        0 4px 12px
        rgba(255, 193, 7, 0.3);
}

.error-card {
    background:
        linear-gradient(
            135deg,
            #f8d7da,
            #f5c6cb
        );

    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #dc3545;
    margin: 0.5rem 0;
}

.success-card {
    background:
        linear-gradient(
            135deg,
            #d4edda,
            #b7e4c7
        );

    padding: 1rem;
    border-radius: 10px;
    border-left: 5px solid #28a745;
    margin: 0.5rem 0;
}

.status-indicator {
    display: inline-block;

    width: 12px;
    height: 12px;

    border-radius: 50%;

    margin-right: 8px;

    animation:
        pulse
        1.5s
        ease-in-out
        infinite;
}

.status-active {
    background-color: #28a745;

    box-shadow:
        0 0 10px #28a745;
}

.status-processing {
    background-color: #ffc107;

    box-shadow:
        0 0 10px #ffc107;
}

.status-idle {
    background-color: #6c757d;
}

.progress-bar-animated {
    background:
        linear-gradient(
            90deg,
            #1f77b4 0%,
            #ff7f0e 50%,
            #1f77b4 100%
        );

    background-size: 200% auto;

    animation:
        shimmer
        2s
        linear
        infinite;

    height: 5px;

    border-radius: 3px;

    margin: 10px 0;
}

.stats-number {
    font-size: 2.2rem;
    font-weight: bold;

    background:
        linear-gradient(
            135deg,
            #1f77b4,
            #ff7f0e
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stats-label {
    color: #495057;
    font-weight: 500;
}

.tab-transition {
    animation:
        fadeInUp
        0.8s
        ease-out;
}

/* Scrollbar */

::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background:
        linear-gradient(
            135deg,
            #1f77b4,
            #ff7f0e
        );

    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    📝 Global Vision
    <span style="color: #ff7f0e;">
        Proofreading
    </span>
    <span class="blinking-cursor"></span>
</div>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "report" not in st.session_state:
    st.session_state.report = None

if "document_text" not in st.session_state:
    st.session_state.document_text = None

if "file_name" not in st.session_state:
    st.session_state.file_name = None


# ============================================================
# STATUS
# ============================================================

status_col1, status_col2, status_col3 = st.columns([1, 2, 1])

with status_col2:

    status_placeholder = st.empty()

    if st.session_state.report:

        status_placeholder.markdown("""
        <div style="
            text-align: center;
            padding: 10px;
            background: #e8f5e9;
            border-radius: 10px;
            margin-bottom: 20px;
        ">
            <span class="
                status-indicator
                status-active
            "></span>

            <span style="
                color: #28a745;
                font-weight: 600;
            ">
                Analysis Complete
            </span>
        </div>
        """, unsafe_allow_html=True)

    else:

        status_placeholder.markdown("""
        <div style="
            text-align: center;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 20px;
        ">
            <span class="
                status-indicator
                status-idle
            "></span>

            <span style="
                color: #6c757d;
                font-weight: 500;
            ">
                System Ready • Waiting for document
            </span>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("""
    <div style="
        background:
            linear-gradient(
                135deg,
                #1f77b4,
                #0d47a1
            );

        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        text-align: center;
    ">

        <h3 style="
            color: white;
            margin: 0;
        ">
            📤 Upload Center
        </h3>

        <p style="
            color: #bbdefb;
            margin: 5px 0 0 0;
        ">
            Drag & drop or click to upload
        </p>

    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=["txt", "pdf", "docx"],
        help="Supported formats: TXT, PDF and DOCX",
        key="file_uploader"
    )

    st.markdown("---")

    st.markdown("""
    <div style="
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
    ">

        <h4 style="color: #1f77b4;">
            📋 Features
        </h4>

        <ul style="
            list-style: none;
            padding: 0;
        ">
            <li>✅ Grammar & Spelling</li>
            <li>✅ Style Analysis</li>
            <li>✅ Readability Metrics</li>
            <li>✅ Passive Voice Detection</li>
            <li>✅ Wordiness Detection</li>
        </ul>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    if st.button(
        "🗑️ Clear Analysis",
        use_container_width=True
    ):

        st.session_state.report = None
        st.session_state.document_text = None
        st.session_state.file_name = None

        st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

if uploaded_file is None:

    st.markdown("""
    <div class="metric-card">

        <h2 style="
            color: #1f77b4;
            text-align: center;
        ">
            Welcome to Global Vision Proofreading
        </h2>

        <p style="
            text-align: center;
            font-size: 1.1rem;
            color: #555;
        ">

            Upload a TXT, PDF or DOCX document to begin
            a comprehensive proofreading analysis.

        </p>

    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🔤</h3>
            <h4>Grammar</h4>
            <p>
                Detect spelling and grammar issues.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>🎯</h3>
            <h4>Style</h4>
            <p>
                Identify wordiness and writing patterns.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📊</h3>
            <h4>Readability</h4>
            <p>
                Understand document readability.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# ANALYZE FILE
# ============================================================

else:

    st.success(
        f"📄 Document loaded: {uploaded_file.name}"
    )

    engine = ProofreadingEngine()

    analyze_col1, analyze_col2, analyze_col3 = (
        st.columns([1, 2, 1])
    )

    with analyze_col2:

        analyze_button = st.button(
            "🔍 START PROOFREADING",
            use_container_width=True,
            type="primary"
        )

    if analyze_button:

        with st.spinner(
            "🔍 Extracting text and analyzing document..."
        ):

            text = engine.extract_text(uploaded_file)

            if text and text.strip():

                progress_bar = st.progress(0)

                progress_bar.progress(25)

                report = engine.generate_report(text)

                progress_bar.progress(100)

                st.session_state.report = report
                st.session_state.document_text = text
                st.session_state.file_name = uploaded_file.name

                progress_bar.empty()

                st.success(
                    "✅ Proofreading analysis completed successfully!"
                )

            else:

                st.error(
                    "❌ No readable text could be extracted from this document."
                )


# ============================================================
# RESULTS
# ============================================================

if st.session_state.report:

    report = st.session_state.report
    text = st.session_state.document_text

    basic_stats = report["Basic Stats"]
    grammar_issues = report["Grammar Issues"]
    style_issues = report["Style Issues"]

    st.markdown("---")

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    st.markdown(
        "## 📊 Analysis Dashboard"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Words",
            basic_stats["Total Words"]
        )

    with col2:
        st.metric(
            "Sentences",
            basic_stats["Total Sentences"]
        )

    with col3:
        st.metric(
            "Grammar Issues",
            len(grammar_issues)
        )

    with col4:
        st.metric(
            "Style Issues",
            len(style_issues)
        )

    st.markdown("")

    # --------------------------------------------------------
    # TABS
    # --------------------------------------------------------

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Document",
        "🔤 Grammar & Spelling",
        "🎯 Style Analysis",
        "📊 Readability",
        "📋 Final Report"
    ])


    # ========================================================
    # DOCUMENT TAB
    # ========================================================

    with tab1:

        st.subheader("Extracted Document Text")

        st.text_area(
            "Document Content",
            value=text,
            height=450,
            disabled=True
        )


    # ========================================================
    # GRAMMAR TAB
    # ========================================================

    with tab2:

        st.subheader(
            f"Grammar & Spelling Issues ({len(grammar_issues)})"
        )

        if grammar_issues:

            grammar_df = pd.DataFrame(
                grammar_issues
            )

            st.dataframe(
                grammar_df,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### 🔍 Issue Details")

            for index, issue in enumerate(
                grammar_issues,
                start=1
            ):

                with st.expander(
                    f"{index}. {issue['Message']}"
                ):

                    st.write(
                        f"**Rule:** {issue['Type']}"
                    )

                    st.write(
                        f"**Suggestion:** "
                        f"{issue['Suggestions']}"
                    )

                    st.write(
                        f"**Context:** "
                        f"{issue['Context']}"
                    )

        else:

            st.markdown("""
            <div class="success-card">
                <h3>🎉 Great Job!</h3>
                <p>
                    No grammar or spelling issues were detected.
                </p>
            </div>
            """, unsafe_allow_html=True)


    # ========================================================
    # STYLE TAB
    # ========================================================

    with tab3:

        st.subheader(
            f"Style Analysis ({len(style_issues)})"
        )

        if style_issues:

            style_df = pd.DataFrame(
                style_issues
            )

            st.dataframe(
                style_df,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("### 💡 Recommendations")

            for issue in style_issues:

                st.markdown(
                    f"""
                    <div class="issue-card">
                        <h4>{issue['Issue']}</h4>
                        <p>
                            <b>Occurrences:</b>
                            {issue['Count']}
                        </p>
                        <p>
                            <b>Recommendation:</b>
                            {issue['Suggestion']}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:

            st.markdown("""
            <div class="success-card">
                <h3>✨ Excellent Writing!</h3>
                <p>
                    No major style issues were detected.
                </p>
            </div>
            """, unsafe_allow_html=True)


    # ========================================================
    # READABILITY TAB
    # ========================================================

    with tab4:

        st.subheader("📊 Readability Metrics")

        read_col1, read_col2, read_col3 = (
            st.columns(3)
        )

        with read_col1:

            st.metric(
                "Flesch Reading Ease",
                basic_stats["Flesch Reading Ease"]
            )

        with read_col2:

            st.metric(
                "Average Sentence Length",
                basic_stats["Avg Sentence Length"]
            )

        with read_col3:

            st.metric(
                "Reading Level",
                basic_stats["Grade Level"]
            )

        st.markdown("---")

        readability_df = pd.DataFrame(
            list(basic_stats.items()),
            columns=["Metric", "Value"]
        )

        st.dataframe(
            readability_df,
            use_container_width=True,
            hide_index=True
        )

        score = basic_stats["Flesch Reading Ease"]

        if score >= 80:

            st.success(
                "🟢 This document is easy to read."
            )

        elif score >= 60:

            st.info(
                "🔵 This document has a standard readability level."
            )

        elif score >= 30:

            st.warning(
                "🟡 This document may be difficult for some readers."
            )

        else:

            st.error(
                "🔴 This document is difficult to read."
            )


    # ========================================================
    # FINAL REPORT TAB
    # ========================================================

    with tab5:

        st.subheader("📋 Comprehensive Proofreading Report")

        total_issues = (
            len(grammar_issues)
            + len(style_issues)
        )

        st.markdown(
            f"""
            <div class="metric-card">

                <h3>
                    📄 Document Summary
                </h3>

                <p>
                    <b>File:</b>
                    {st.session_state.file_name}
                </p>

                <p>
                    <b>Total Words:</b>
                    {basic_stats['Total Words']}
                </p>

                <p>
                    <b>Grammar & Spelling Issues:</b>
                    {len(grammar_issues)}
                </p>

                <p>
                    <b>Style Issues:</b>
                    {len(style_issues)}
                </p>

                <p>
                    <b>Total Issues:</b>
                    {total_issues}
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

        if total_issues == 0:

            st.markdown("""
            <div class="success-card">
                <h3>🏆 Excellent!</h3>
                <p>
                    No major proofreading issues were detected.
                </p>
            </div>
            """, unsafe_allow_html=True)

        elif total_issues <= 5:

            st.warning(
                "⚠️ A small number of issues were detected. "
                "Review the recommendations before finalizing the document."
            )

        else:

            st.error(
                "⚠️ Multiple issues were detected. "
                "A detailed review is recommended."
            )

        # --------------------------------------------
        # DOWNLOAD REPORT
        # --------------------------------------------

        report_text = f"""
GLOBAL VISION - PROOFREADING REPORT
===================================

FILE:
{st.session_state.file_name}

BASIC STATISTICS
----------------
Total Words: {basic_stats['Total Words']}
Total Sentences: {basic_stats['Total Sentences']}
Average Sentence Length: {basic_stats['Avg Sentence Length']}
Average Word Length: {basic_stats['Avg Word Length']}
Flesch Reading Ease: {basic_stats['Flesch Reading Ease']}
Reading Level: {basic_stats['Grade Level']}

GRAMMAR & SPELLING ISSUES
-------------------------
Total Issues: {len(grammar_issues)}

STYLE ISSUES
------------
Total Issues: {len(style_issues)}

TOTAL ISSUES
------------
{total_issues}
"""

        st.download_button(
            label="⬇️ Download Proofreading Report",
            data=report_text,
            file_name="proofreading_report.txt",
            mime="text/plain",
            use_container_width=True
        )
