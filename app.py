import streamlit as st
import pandas as pd
import re
import io
import tempfile
import os
import textwrap

import docx2txt
import PyPDF2
import language_tool_python


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Global Vision - Proofreading Software",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# HTML RENDERING HELPER
# IMPORTANT: Removes indentation so HTML does NOT become a code block
# ============================================================

def render_html(html_code):
    st.markdown(
        textwrap.dedent(html_code).strip(),
        unsafe_allow_html=True
    )


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

/* ----------------------------------------------------------
   MAIN APPLICATION
---------------------------------------------------------- */

.stApp {
    background-color: #0e1117;
}


/* ----------------------------------------------------------
   MAIN CONTENT WIDTH
---------------------------------------------------------- */

.block-container {
    padding-top: 2.5rem;
    padding-bottom: 2rem;
}


/* ----------------------------------------------------------
   GLOBAL VISION HEADER
---------------------------------------------------------- */

.main-title {
    text-align: center;
    font-size: 42px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 20px;
    color: #75b5ff;
}

.main-title .orange {
    color: #ff9d42;
}


/* ----------------------------------------------------------
   STATUS BAR
---------------------------------------------------------- */

.status-box {
    width: 100%;
    background-color: #1b212c;
    border: 1px solid #384252;
    border-radius: 8px;
    padding: 10px;
    text-align: center;
    color: #aeb8c5;
    margin-bottom: 15px;
    font-size: 14px;
}


/* ----------------------------------------------------------
   MAIN WELCOME CARD
---------------------------------------------------------- */

.welcome-card {
    background-color: #202733;
    border: 1px solid #3c4758;
    border-radius: 14px;
    padding: 30px;
    margin-bottom: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.20);
}

.welcome-title {
    color: #75b5ff;
    text-align: center;
    font-size: 27px;
    font-weight: 600;
    margin-bottom: 15px;
}

.welcome-text {
    color: #c7ced8;
    text-align: center;
    font-size: 17px;
    line-height: 1.6;
}


/* ----------------------------------------------------------
   FEATURE CARDS
---------------------------------------------------------- */

.feature-card {
    background-color: #202733;
    border: 1px solid #3c4758;
    border-radius: 14px;
    padding: 28px;
    min-height: 150px;
    transition: all 0.25s ease;
    margin-top: 10px;
}

.feature-card:hover {
    transform: translateY(-4px);
    border-color: #4da3ff;
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
}

.feature-title {
    color: #f0f4fa;
    font-size: 21px;
    font-weight: 600;
    margin-bottom: 12px;
}

.feature-description {
    color: #aeb8c5;
    font-size: 15px;
    line-height: 1.5;
}


/* ----------------------------------------------------------
   SIDEBAR
---------------------------------------------------------- */

section[data-testid="stSidebar"] {
    background-color: #2a2d38;
}

.sidebar-box {
    background: linear-gradient(135deg, #1f6fb2, #244c75);
    border-radius: 14px;
    padding: 22px 12px;
    text-align: center;
    margin-bottom: 20px;
    border: 1px solid #3378b7;
}

.sidebar-title {
    color: white;
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 8px;
}

.sidebar-text {
    color: #d5e9ff;
    font-size: 14px;
}

.features-box {
    background-color: #1e2430;
    border: 1px solid #3b4758;
    border-radius: 12px;
    padding: 18px;
    margin-top: 10px;
}

.features-title {
    color: #75b5ff;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 15px;
}

.features-item {
    color: #d7dee8;
    font-size: 14px;
    margin: 10px 0;
}


/* ----------------------------------------------------------
   ISSUE CARDS
---------------------------------------------------------- */

.issue-card {
    background-color: #202733;
    border: 1px solid #3c4758;
    border-left: 5px solid #ffb347;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 12px;
}

.issue-title {
    color: #ffffff;
    font-size: 17px;
    font-weight: 600;
}

.issue-text {
    color: #c7ced8;
}


/* ----------------------------------------------------------
   BUTTONS
---------------------------------------------------------- */

.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    min-height: 42px;
}


/* ----------------------------------------------------------
   FILE UPLOADER
---------------------------------------------------------- */

[data-testid="stFileUploader"] {
    border-radius: 10px;
}


/* ----------------------------------------------------------
   METRICS
---------------------------------------------------------- */

[data-testid="stMetric"] {
    background-color: #202733;
    border: 1px solid #3c4758;
    border-radius: 12px;
    padding: 15px;
}


/* ----------------------------------------------------------
   DIVIDERS
---------------------------------------------------------- */

hr {
    border-color: #3c4758;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# LANGUAGE TOOL
# ============================================================

@st.cache_resource
def load_language_tool():

    try:
        return language_tool_python.LanguageTool("en-US")

    except Exception as e:
        return None


# ============================================================
# PROOFREADING ENGINE
# ============================================================

class ProofreadingEngine:

    def __init__(self):
        self.language_tool = load_language_tool()


    # --------------------------------------------------------
    # EXTRACT TEXT
    # --------------------------------------------------------

    def extract_text(self, uploaded_file):

        if uploaded_file is None:
            return None

        filename = uploaded_file.name.lower()

        try:

            # TXT
            if filename.endswith(".txt"):

                return uploaded_file.getvalue().decode(
                    "utf-8",
                    errors="ignore"
                )


            # PDF
            elif filename.endswith(".pdf"):

                pdf_reader = PyPDF2.PdfReader(
                    io.BytesIO(uploaded_file.getvalue())
                )

                extracted_text = ""

                for page in pdf_reader.pages:

                    page_text = page.extract_text()

                    if page_text:
                        extracted_text += page_text + "\n"

                return extracted_text


            # DOCX
            elif filename.endswith(".docx"):

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".docx"
                ) as temp_file:

                    temp_file.write(
                        uploaded_file.getvalue()
                    )

                    temp_path = temp_file.name

                try:

                    extracted_text = docx2txt.process(
                        temp_path
                    )

                finally:

                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                return extracted_text


            return None

        except Exception as e:

            st.error(
                f"Error reading document: {e}"
            )

            return None


    # --------------------------------------------------------
    # GRAMMAR AND SPELLING
    # --------------------------------------------------------

    def check_grammar(self, text):

        if not self.language_tool:
            return []

        if not text or not text.strip():
            return []

        try:

            matches = self.language_tool.check(text)

            issues = []

            for match in matches:

                suggestions = "No suggestion available"

                if match.replacements:
                    suggestions = ", ".join(
                        match.replacements[:5]
                    )

                issues.append({

                    "Rule": match.ruleId,

                    "Message": match.message,

                    "Suggestions": suggestions,

                    "Context": match.context,

                    "Position": (
                        f"{match.offset} - "
                        f"{match.offset + match.errorLength}"
                    )
                })

            return issues

        except Exception as e:

            st.warning(
                f"Grammar analysis could not be completed: {e}"
            )

            return []


    # --------------------------------------------------------
    # STYLE ANALYSIS
    # --------------------------------------------------------

    def check_style(self, text):

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
                    "Consider rewriting in active voice "
                    "where appropriate."
                )
            })


        # WORDY PHRASES

        wordy_phrases = {

            "in order to": "to",

            "due to the fact that": "because",

            "in the event that": "if",

            "at this point in time": "now",

            "for the purpose of": "to",

            "has the ability to": "can",

            "make a decision": "decide",

            "give consideration to": "consider",

            "in spite of the fact that": "although"
        }


        for phrase, replacement in wordy_phrases.items():

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
                        f'Consider replacing it with '
                        f'"{replacement}".'
                    )
                })


        # REPEATED WORDS

        repeated_words = re.findall(
            r"\b(\w+)\s+\1\b",
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

        multiple_exclamation = re.findall(
            r"!{2,}",
            text
        )

        if multiple_exclamation:

            issues.append({

                "Issue": "Multiple Exclamation Marks",

                "Count": len(multiple_exclamation),

                "Suggestion": (
                    "Consider using a single exclamation mark."
                )
            })


        return issues


    # --------------------------------------------------------
    # SYLLABLE COUNT
    # --------------------------------------------------------

    def count_syllables(self, word):

        word = re.sub(
            r"[^a-z]",
            "",
            word.lower()
        )

        if not word:
            return 0

        if len(word) <= 3:
            return 1

        vowels = "aeiouy"

        count = 0

        previous_was_vowel = False

        for character in word:

            is_vowel = character in vowels

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

        words = re.findall(
            r"\b[\w'-]+\b",
            text
        )

        sentences = [

            sentence.strip()

            for sentence in re.split(
                r"[.!?]+",
                text
            )

            if sentence.strip()
        ]


        total_words = len(words)

        total_sentences = len(sentences)


        average_sentence_length = (

            total_words / total_sentences

            if total_sentences > 0

            else 0
        )


        average_word_length = (

            sum(
                len(word)
                for word in words
            ) / total_words

            if total_words > 0

            else 0
        )


        total_syllables = sum(

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
                    total_syllables / total_words
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

            "Average Sentence Length": round(
                average_sentence_length,
                2
            ),

            "Average Word Length": round(
                average_word_length,
                2
            ),

            "Flesch Reading Ease": round(
                flesch_score,
                2
            ),

            "Reading Level": reading_level
        }


    # --------------------------------------------------------
    # COMPLETE REPORT
    # --------------------------------------------------------

    def generate_report(self, text):

        return {

            "readability": self.check_readability(text),

            "grammar": self.check_grammar(text),

            "style": self.check_style(text)
        }


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

render_html("""
<div class="main-title">
📝 Global Vision <span class="orange">Proofreading</span>
</div>
""")


# ============================================================
# STATUS BAR
# ============================================================

if st.session_state.report is None:

    render_html("""
    <div class="status-box">
    ⚪ System Ready • Waiting for document
    </div>
    """)

else:

    render_html("""
    <div class="status-box">
    🟢 System Active • Analysis Complete
    </div>
    """)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    render_html("""
    <div class="sidebar-box">
    <div class="sidebar-title">📤 Upload Center</div>
    <div class="sidebar-text">Drag & drop or click to upload</div>
    </div>
    """)


    uploaded_file = st.file_uploader(

        "Choose a document",

        type=["txt", "pdf", "docx"],

        help="Supported formats: TXT, PDF and DOCX"
    )


    st.divider()


    render_html("""
    <div class="features-box">
    <div class="features-title">📋 Features</div>

    <div class="features-item">✅ Grammar & Spelling</div>
    <div class="features-item">✅ Style Analysis</div>
    <div class="features-item">✅ Readability Metrics</div>
    <div class="features-item">✅ Passive Voice Detection</div>
    <div class="features-item">✅ Wordiness Detection</div>

    </div>
    """)


    st.write("")


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

if (
    uploaded_file is None
    and st.session_state.report is None
):

    render_html("""
    <div class="welcome-card">

    <div class="welcome-title">
    Welcome to Global Vision Proofreading
    </div>

    <div class="welcome-text">
    Upload a TXT, PDF or DOCX document to begin a
    comprehensive proofreading analysis.
    </div>

    </div>
    """)


    col1, col2, col3 = st.columns(3)


    with col1:

        render_html("""
        <div class="feature-card">

        <div class="feature-title">
        🔤 Grammar
        </div>

        <div class="feature-description">
        Detect grammar and spelling issues.
        </div>

        </div>
        """)


    with col2:

        render_html("""
        <div class="feature-card">

        <div class="feature-title">
        🎯 Style
        </div>

        <div class="feature-description">
        Identify wordiness and writing patterns.
        </div>

        </div>
        """)


    with col3:

        render_html("""
        <div class="feature-card">

        <div class="feature-title">
        📊 Readability
        </div>

        <div class="feature-description">
        Understand document readability.
        </div>

        </div>
        """)


# ============================================================
# DOCUMENT UPLOAD AND ANALYSIS
# ============================================================

if uploaded_file is not None:

    st.success(
        f"📄 Document loaded: {uploaded_file.name}"
    )


    st.write("")


    left, center, right = st.columns([1, 2, 1])


    with center:

        start_analysis = st.button(

            "🔍 START PROOFREADING",

            type="primary",

            use_container_width=True
        )


    if start_analysis:

        engine = ProofreadingEngine()


        with st.spinner(
            "Analyzing your document..."
        ):

            extracted_text = engine.extract_text(
                uploaded_file
            )


            if extracted_text and extracted_text.strip():

                progress_bar = st.progress(0)

                progress_bar.progress(20)

                report = engine.generate_report(
                    extracted_text
                )

                progress_bar.progress(100)


                st.session_state.report = report

                st.session_state.document_text = (
                    extracted_text
                )

                st.session_state.file_name = (
                    uploaded_file.name
                )


                progress_bar.empty()


                st.success(
                    "✅ Proofreading completed successfully!"
                )

                st.rerun()


            else:

                st.error(
                    "❌ No readable text could be extracted from this file."
                )


# ============================================================
# RESULTS DASHBOARD
# ============================================================

if st.session_state.report is not None:

    report = st.session_state.report

    document_text = st.session_state.document_text

    readability = report["readability"]

    grammar_issues = report["grammar"]

    style_issues = report["style"]


    st.divider()


    st.header("📊 Analysis Dashboard")


    metric_1, metric_2, metric_3, metric_4 = st.columns(4)


    with metric_1:

        st.metric(
            "Total Words",
            readability["Total Words"]
        )


    with metric_2:

        st.metric(
            "Sentences",
            readability["Total Sentences"]
        )


    with metric_3:

        st.metric(
            "Grammar Issues",
            len(grammar_issues)
        )


    with metric_4:

        st.metric(
            "Style Issues",
            len(style_issues)
        )


    # --------------------------------------------------------
    # TABS
    # --------------------------------------------------------

    (
        tab_document,
        tab_grammar,
        tab_style,
        tab_readability,
        tab_report
    ) = st.tabs([

        "📄 Document",

        "🔤 Grammar & Spelling",

        "🎯 Style Analysis",

        "📊 Readability",

        "📋 Final Report"
    ])


    # ========================================================
    # DOCUMENT TAB
    # ========================================================

    with tab_document:

        st.subheader(
            "Extracted Document Text"
        )

        st.text_area(

            "Document Content",

            value=document_text,

            height=450
        )


    # ========================================================
    # GRAMMAR TAB
    # ========================================================

    with tab_grammar:

        st.subheader(
            f"Grammar & Spelling Issues ({len(grammar_issues)})"
        )


        if grammar_issues:

            grammar_dataframe = pd.DataFrame(
                grammar_issues
            )

            st.dataframe(
                grammar_dataframe,
                use_container_width=True,
                hide_index=True
            )


            st.subheader(
                "Issue Details"
            )


            for index, issue in enumerate(
                grammar_issues,
                start=1
            ):

                with st.expander(
                    f"{index}. {issue['Message']}"
                ):

                    st.write(
                        f"**Rule:** {issue['Rule']}"
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

    with tab_style:

        st.subheader(
            f"Style Issues ({len(style_issues)})"
        )


        if style_issues:

            for issue in style_issues:

                render_html(f"""
                <div class="issue-card">

                <div class="issue-title">
                {issue["Issue"]}
                </div>

                <br>

                <div class="issue-text">
                <b>Occurrences:</b> {issue["Count"]}
                </div>

                <div class="issue-text">
                <b>Recommendation:</b>
                {issue["Suggestion"]}
                </div>

                </div>
                """)

        else:

            st.success(
                "✨ No major style issues were detected!"
            )


    # ========================================================
    # READABILITY TAB
    # ========================================================

    with tab_readability:

        st.subheader(
            "📊 Readability Metrics"
        )


        read_col1, read_col2, read_col3 = st.columns(3)


        with read_col1:

            st.metric(
                "Flesch Reading Ease",
                readability["Flesch Reading Ease"]
            )


        with read_col2:

            st.metric(
                "Average Sentence Length",
                readability[
                    "Average Sentence Length"
                ]
            )


        with read_col3:

            st.metric(
                "Reading Level",
                readability["Reading Level"]
            )


        readability_dataframe = pd.DataFrame(

            list(readability.items()),

            columns=[
                "Metric",
                "Value"
            ]
        )


        st.dataframe(
            readability_dataframe,
            use_container_width=True,
            hide_index=True
        )


    # ========================================================
    # FINAL REPORT TAB
    # ========================================================

    with tab_report:

        st.subheader(
            "📋 Comprehensive Proofreading Report"
        )


        total_issues = (

            len(grammar_issues)

            + len(style_issues)
        )


        st.write(
            f"**File:** {st.session_state.file_name}"
        )

        st.write(
            f"**Total Words:** "
            f"{readability['Total Words']}"
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
            f"**Total Issues:** "
            f"{total_issues}"
        )


        st.divider()


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


        # ----------------------------------------------------
        # DOWNLOAD REPORT
        # ----------------------------------------------------

        downloadable_report = f"""
GLOBAL VISION - PROOFREADING REPORT
===================================

FILE
----
{st.session_state.file_name}

BASIC STATISTICS
----------------
Total Words: {readability["Total Words"]}
Total Sentences: {readability["Total Sentences"]}
Average Sentence Length: {readability["Average Sentence Length"]}
Average Word Length: {readability["Average Word Length"]}
Flesch Reading Ease: {readability["Flesch Reading Ease"]}
Reading Level: {readability["Reading Level"]}

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

            data=downloadable_report,

            file_name=(
                "global_vision_proofreading_report.txt"
            ),

            mime="text/plain",

            use_container_width=True
        )
