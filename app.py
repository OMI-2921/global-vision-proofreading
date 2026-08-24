import streamlit as st
import pandas as pd
import re
import io
import tempfile
import os
import docx2txt
import PyPDF2
import language_tool_python


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
# LOAD LANGUAGE TOOL
# ============================================================

@st.cache_resource
def load_language_tool():
    try:
        return language_tool_python.LanguageTool("en-US")
    except Exception:
        return None


# ============================================================
# PROOFREADING ENGINE
# ============================================================

class ProofreadingEngine:

    def __init__(self):
        self.lt = load_language_tool()

    def extract_text(self, uploaded_file):

        if uploaded_file is None:
            return None

        filename = uploaded_file.name.lower()

        try:

            # TXT FILE
            if filename.endswith(".txt"):

                return uploaded_file.getvalue().decode(
                    "utf-8",
                    errors="ignore"
                )

            # PDF FILE
            elif filename.endswith(".pdf"):

                pdf_reader = PyPDF2.PdfReader(
                    io.BytesIO(uploaded_file.getvalue())
                )

                text = ""

                for page in pdf_reader.pages:

                    page_text = page.extract_text()

                    if page_text:
                        text += page_text + "\n"

                return text

            # DOCX FILE
            elif filename.endswith(".docx"):

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".docx"
                ) as temp_file:

                    temp_file.write(uploaded_file.getvalue())
                    temp_path = temp_file.name

                try:
                    text = docx2txt.process(temp_path)
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                return text

            else:
                return None

        except Exception as e:

            st.error(f"Error reading document: {e}")

            return None


    # ========================================================
    # GRAMMAR AND SPELLING
    # ========================================================

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
                    else "No suggestion available"
                )

                category = "General"

                try:
                    category = match.category
                except Exception:
                    pass

                issues.append({
                    "Type": match.ruleId,
                    "Category": str(category),
                    "Message": match.message,
                    "Suggestions": replacements,
                    "Context": match.context,
                    "Position": (
                        f"{match.offset} - "
                        f"{match.offset + match.errorLength}"
                    )
                })

            return issues

        except Exception as e:

            st.warning(
                f"Grammar checking could not be completed: {e}"
            )

            return []


    # ========================================================
    # SYLLABLE COUNTER
    # ========================================================

    def count_syllables(self, word):

        word = word.lower()

        word = re.sub(
            r"[^a-z]",
            "",
            word
        )

        if not word:
            return 0

        if len(word) <= 3:
            return 1

        vowels = "aeiouy"

        count = 0
        previous_vowel = False

        for char in word:

            is_vowel = char in vowels

            if is_vowel and not previous_vowel:
                count += 1

            previous_vowel = is_vowel

        if word.endswith("e") and count > 1:
            count -= 1

        return max(count, 1)


    # ========================================================
    # READABILITY
    # ========================================================

    def check_readability(self, text):

        words = re.findall(
            r"\b[\w'-]+\b",
            text
        )

        sentences = [
            sentence.strip()
            for sentence in re.split(r"[.!?]+", text)
            if sentence.strip()
        ]

        total_words = len(words)
        total_sentences = len(sentences)

        avg_sentence_length = (
            total_words / total_sentences
            if total_sentences > 0
            else 0
        )

        avg_word_length = (
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
                - 1.015 * (
                    total_words / total_sentences
                )
                - 84.6 * (
                    syllables / total_words
                )
            )

        else:
            flesch_score = 0

        if flesch_score >= 90:
            reading_level = "Very Easy"

        elif flesch_score >= 80:
            reading_level = "Easy"

        elif flesch_score >= 70:
            reading_level = "Fairly Easy"

        elif flesch_score >= 60:
            reading_level = "Standard"

        elif flesch_score >= 50:
            reading_level = "Fairly Difficult"

        elif flesch_score >= 30:
            reading_level = "Difficult"

        else:
            reading_level = "Very Difficult"

        return {

            "Total Words": total_words,

            "Total Sentences": total_sentences,

            "Avg Sentence Length": round(
                avg_sentence_length,
                2
            ),

            "Avg Word Length": round(
                avg_word_length,
                2
            ),

            "Flesch Reading Ease": round(
                flesch_score,
                2
            ),

            "Reading Level": reading_level
        }


    # ========================================================
    # STYLE CHECKING
    # ========================================================

    def check_style_issues(self, text):

        issues = []

        if not text:
            return issues

        # POSSIBLE PASSIVE VOICE

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

                "Issue": "Possible Passive Voice",

                "Count": len(passive_matches),

                "Suggestion": (
                    "Consider using active voice "
                    "where appropriate."
                )
            })


        # WORDY PHRASES

        wordiness_patterns = {

            "in order to": "to",

            "due to the fact that": "because",

            "in the event that": "if",

            "at this point in time": "now",

            "for the purpose of": "to",

            "has the ability to": "can",

            "in spite of the fact that": "although",

            "make a decision": "decide",

            "give consideration to": "consider"
        }

        for phrase, suggestion in wordiness_patterns.items():

            matches = re.findall(
                re.escape(phrase),
                text,
                re.IGNORECASE
            )

            if matches:

                issues.append({

                    "Issue": f'Wordy phrase: "{phrase}"',

                    "Count": len(matches),

                    "Suggestion": (
                        f'Consider using "{suggestion}" instead.'
                    )
                })


        # REPEATED WORDS

        repeated_pattern = r"\b(\w+)\s+\1\b"

        repeated_words = re.findall(
            repeated_pattern,
            text,
            re.IGNORECASE
        )

        if repeated_words:

            issues.append({

                "Issue": "Repeated Words",

                "Count": len(repeated_words),

                "Suggestion": (
                    "Check for accidentally repeated words."
                )
            })


        # MULTIPLE EXCLAMATION MARKS

        exclamation_matches = re.findall(
            r"!{2,}",
            text
        )

        if exclamation_matches:

            issues.append({

                "Issue": "Multiple Exclamation Marks",

                "Count": len(exclamation_matches),

                "Suggestion": (
                    "Consider using a single exclamation mark."
                )
            })

        return issues


    # ========================================================
    # GENERATE COMPLETE REPORT
    # ========================================================

    def generate_report(self, text):

        return {

            "Basic Stats": self.check_readability(text),

            "Grammar Issues": self.check_spelling_grammar(text),

            "Style Issues": self.check_style_issues(text)
        }


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

/* MAIN BACKGROUND */

.stApp {
    background-color: #0e1117;
}


/* HEADER */

.main-header {
    font-size: 3rem;
    text-align: center;
    margin-bottom: 20px;
    color: #4da3ff;
    font-weight: 600;
}


/* BLINKING CURSOR */

.blinking-cursor {
    display: inline-block;
    width: 3px;
    height: 35px;
    background-color: #4da3ff;
    margin-left: 8px;
    animation: blink 1s infinite;
    vertical-align: middle;
}

@keyframes blink {

    0% {
        opacity: 1;
    }

    50% {
        opacity: 0;
    }

    100% {
        opacity: 1;
    }
}


/* CARDS */

.metric-card {

    background: linear-gradient(
        135deg,
        #1c212b,
        #252b36
    );

    padding: 25px;

    border-radius: 15px;

    border: 1px solid #3a4658;

    margin-bottom: 15px;

    transition: 0.3s;
}

.metric-card:hover {

    transform: translateY(-4px);

    border-color: #4da3ff;

}


/* ISSUE CARD */

.issue-card {

    background-color: #242a35;

    padding: 18px;

    border-radius: 10px;

    border-left: 5px solid #f0ad4e;

    margin-bottom: 12px;
}


/* SUCCESS CARD */

.success-card {

    background-color: #1b3325;

    padding: 20px;

    border-radius: 12px;

    border-left: 5px solid #28a745;

}


/* STATUS BOX */

.status-box {

    text-align: center;

    padding: 12px;

    border-radius: 10px;

    background-color: #1c212b;

    margin-bottom: 20px;

    border: 1px solid #303846;
}


/* SIDEBAR */

.sidebar-upload {

    background: linear-gradient(
        135deg,
        #1f77b4,
        #0d47a1
    );

    padding: 20px;

    border-radius: 15px;

    text-align: center;

    margin-bottom: 20px;
}


/* FEATURE BOX */

.feature-box {

    background-color: #1c212b;

    padding: 15px;

    border-radius: 10px;

    border: 1px solid #303846;
}


/* METRIC NUMBER */

.metric-number {

    font-size: 2rem;

    font-weight: bold;

    color: #4da3ff;
}

</style>
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
# HEADER
# ============================================================

st.markdown(
    """
    <div class="main-header">
        📝 Global Vision
        <span style="color:#ff9f43;">
            Proofreading
        </span>
        <span class="blinking-cursor"></span>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# STATUS
# ============================================================

if st.session_state.report:

    st.markdown(
        """
        <div class="status-box">
            🟢 <b style="color:#28a745;">
            System Active • Analysis Complete
            </b>
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        """
        <div class="status-box">
            ⚪ <span style="color:#a0a0a0;">
            System Ready • Waiting for document
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-upload">

            <h3 style="color:white; margin:0;">
                📤 Upload Center
            </h3>

            <p style="color:#cfe8ff;">
                Drag & drop or click to upload
            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(

        "Choose a document",

        type=["txt", "pdf", "docx"],

        help="Supported formats: TXT, PDF and DOCX"
    )

    st.markdown("---")

    st.markdown(
        """
        <div class="feature-box">

            <h4 style="color:#4da3ff;">
                📋 Features
            </h4>

            <p>✅ Grammar & Spelling</p>

            <p>✅ Style Analysis</p>

            <p>✅ Readability Metrics</p>

            <p>✅ Passive Voice Detection</p>

            <p>✅ Wordiness Detection</p>

        </div>
        """,
        unsafe_allow_html=True
    )

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
# WELCOME SCREEN
# ============================================================

if uploaded_file is None and st.session_state.report is None:

    st.markdown(
        """
        <div class="metric-card">

            <h2 style="
                text-align:center;
                color:#4da3ff;
            ">
                Welcome to Global Vision Proofreading
            </h2>

            <p style="
                text-align:center;
                color:#c5c5c5;
                font-size:18px;
            ">

                Upload a TXT, PDF or DOCX document to begin
                a comprehensive proofreading analysis.

            </p>

        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            <div class="metric-card">

                <h2>🔤 Grammar</h2>

                <p>
                    Detect grammar and spelling issues.
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            """
            <div class="metric-card">

                <h2>🎯 Style</h2>

                <p>
                    Identify wordiness and writing patterns.
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            """
            <div class="metric-card">

                <h2>📊 Readability</h2>

                <p>
                    Understand document readability.
                </p>

            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================
# FILE ANALYSIS
# ============================================================

if uploaded_file is not None:

    st.success(
        f"📄 Document loaded: {uploaded_file.name}"
    )

    st.markdown("")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        analyze_button = st.button(

            "🔍 START PROOFREADING",

            type="primary",

            use_container_width=True
        )

    if analyze_button:

        engine = ProofreadingEngine()

        with st.spinner(
            "Analyzing your document..."
        ):

            text = engine.extract_text(uploaded_file)

            if text and text.strip():

                progress = st.progress(0)

                progress.progress(20)

                report = engine.generate_report(text)

                progress.progress(100)

                st.session_state.report = report

                st.session_state.document_text = text

                st.session_state.file_name = uploaded_file.name

                progress.empty()

                st.success(
                    "✅ Proofreading completed successfully!"
                )

                st.rerun()

            else:

                st.error(
                    "❌ No readable text could be extracted."
                )


# ============================================================
# RESULTS DASHBOARD
# ============================================================

if st.session_state.report is not None:

    report = st.session_state.report

    text = st.session_state.document_text

    basic_stats = report["Basic Stats"]

    grammar_issues = report["Grammar Issues"]

    style_issues = report["Style Issues"]

    st.markdown("---")

    st.header("📊 Analysis Dashboard")

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


    # ========================================================
    # TABS
    # ========================================================

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

            height=450

        )


    # ========================================================
    # GRAMMAR TAB
    # ========================================================

    with tab2:

        st.subheader(
            f"Grammar & Spelling Issues "
            f"({len(grammar_issues)})"
        )

        if grammar_issues:

            grammar_df = pd.DataFrame(grammar_issues)

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
                        f"**Suggestions:** "
                        f"{issue['Suggestions']}"
                    )

                    st.write(
                        f"**Context:** "
                        f"{issue['Context']}"
                    )

        else:

            st.success(
                "🎉 No grammar or spelling issues were detected!"
            )


    # ========================================================
    # STYLE TAB
    # ========================================================

    with tab3:

        st.subheader(
            f"Style Issues ({len(style_issues)})"
        )

        if style_issues:

            style_df = pd.DataFrame(style_issues)

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

                        <h4>
                            {issue['Issue']}
                        </h4>

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

            st.success(
                "✨ No major style issues were detected!"
            )


    # ========================================================
    # READABILITY TAB
    # ========================================================

    with tab4:

        st.subheader("📊 Readability Metrics")

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Flesch Reading Ease",
                basic_stats["Flesch Reading Ease"]
            )

        with col2:

            st.metric(
                "Avg Sentence Length",
                basic_stats["Avg Sentence Length"]
            )

        with col3:

            st.metric(
                "Reading Level",
                basic_stats["Reading Level"]
            )

        readability_df = pd.DataFrame(
            list(basic_stats.items()),
            columns=["Metric", "Value"]
        )

        st.dataframe(
            readability_df,
            use_container_width=True,
            hide_index=True
        )


    # ========================================================
    # FINAL REPORT TAB
    # ========================================================

    with tab5:

        total_issues = (
            len(grammar_issues)
            + len(style_issues)
        )

        st.subheader(
            "📋 Comprehensive Proofreading Report"
        )

        st.write(
            f"**File:** {st.session_state.file_name}"
        )

        st.write(
            f"**Total Words:** "
            f"{basic_stats['Total Words']}"
        )

        st.write(
            f"**Grammar & Spelling Issues:** "
            f"{len(grammar_issues)}"
        )

        st.write(
            f"**Style Issues:** "
            f"{len(style_issues)}"
        )

        st.write(
            f"**Total Issues:** {total_issues}"
        )

        st.markdown("---")

        if total_issues == 0:

            st.success(
                "🏆 Excellent! No major issues were detected."
            )

        elif total_issues <= 5:

            st.warning(
                "⚠️ A small number of issues were detected."
            )

        else:

            st.error(
                "⚠️ Multiple issues were detected. "
                "A detailed review is recommended."
            )


        # DOWNLOADABLE REPORT

        report_text = f"""
GLOBAL VISION - PROOFREADING REPORT
===================================

FILE
----
{st.session_state.file_name}

BASIC STATISTICS
----------------
Total Words: {basic_stats['Total Words']}
Total Sentences: {basic_stats['Total Sentences']}
Average Sentence Length: {basic_stats['Avg Sentence Length']}
Average Word Length: {basic_stats['Avg Word Length']}
Flesch Reading Ease: {basic_stats['Flesch Reading Ease']}
Reading Level: {basic_stats['Reading Level']}

GRAMMAR & SPELLING ISSUES
-------------------------
{len(grammar_issues)}

STYLE ISSUES
------------
{len(style_issues)}

TOTAL ISSUES
------------
{total_issues}
"""

        st.download_button(

            "⬇️ Download Proofreading Report",

            data=report_text,

            file_name="global_vision_proofreading_report.txt",

            mime="text/plain",

            use_container_width=True
        )
