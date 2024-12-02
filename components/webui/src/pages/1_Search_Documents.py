# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st  # type: ignore
from dpu.api import generate_answer
from dpu.components import TITLE_LOGO, LOGO, PREAMBLE, choose_source_id, show_agent_document
from fpdf import FPDF
logger = st.logger.get_logger(__name__)  # pyright: ignore[reportAttributeAccessIssue]
import base64
from datetime import datetime

# Put into a single place
SAMPLE_QUERIES = """
```
Provide a detailed summary of Simmons Bank's financial.
```
```
Give me the book value of Q4 2022.
```
```
What was the Loan to deposit ratio in Q4 2023?
```
```
What was the Loan to deposit ratio in Q2 2022?
```
```
Net charge-off ratio in Q3 2023?
```
```
What were the Salaries and employee benefits in Q1 2023?
```
```
Summarize the financials for the entire 2023 year for Simmons Bank.
```
```
What were the key highlights of Simmons Bank's Q3 2021?
```
"""

#
# Page Layout
#

# Page configuration
st.set_page_config(
    page_title="Search and Summarization",
    page_icon=TITLE_LOGO,
    layout="wide",
)

# Title
image_col, title_col = st.columns([1, 2])
with image_col:
    st.write("")
    st.image(LOGO, "", 256)
with title_col:
    st.title(":green[Search and Summarize Documents]")
st.divider()

#
# Initialize session state
#

if "answer" not in st.session_state:
    st.session_state["answer"] = ""
if "sources" not in st.session_state:
    st.session_state["sources"] = []
if "chosen_row" not in st.session_state:
    st.session_state["chosen_row"] = None
if "preamble" not in st.session_state:
    st.session_state["preamble"] = PREAMBLE

#
# Form
#

st.write(
    """### Given a query, Simmons InfoLink will generate an answer with citations to the documents."""
)

if "preamble" not in st.session_state:
    st.session_state["preamble"] = PREAMBLE

# Render the question input and Examples button
with st.container():

    def update_preamble():
        logger.info(f"preamble update: {st.session_state.preamble_new}")
        st.session_state.preamble = st.session_state.preamble_new

    def question_change():
        result = generate_answer(
            st.session_state.question, preamble=st.session_state["preamble"]
        )
        st.session_state.answer = result["answer"]
        st.session_state.sources = result["sources"]
        
    query_col, button_col, example_col = st.columns([85, 10, 15])

    with query_col:
        question = st.text_input(
            label="",
            value="",
            placeholder="e.g., What are Simmons Bank Q1 2023 details?",
            key="question",
            on_change=question_change,
        )

    with button_col:
        st.write("")
        st.write("")
        st.markdown(
            """
            <style>
            .enter-button {
                width: 100%;
                height: 30px; /* Matches the height of the text input box */
                font-size: 16px;
                background-color: #007BFF;  
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .enter-button:hover {
                background-color: #0056b3;
            }
            </style>
            <button class="enter-button">Enter</button>
            """,
            unsafe_allow_html=True,
        )
    
        with example_col:
            # Add spacing for alignment
            st.write("")
            st.write("")
            
            with st.popover("Examples"):
                st.markdown(SAMPLE_QUERIES, unsafe_allow_html=True)

# Add an export as PDF button here
def create_download_link(value, filename):
    """Generate a download link for the PDF."""
    b64 = base64.b64encode(value)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'

# Render the answer if there is a response
if st.session_state.answer:
    st.markdown("### :blue[Summary Response:]")
    ans = st.session_state.answer
    st.text_area("Summary", value=ans, height=240)

    st.markdown("### Please enter your name: ")
    username = st.text_input("Name", placeholder="Enter your name here", key="username_input")

    if username.strip() == "":
        st.warning("Name is required for generating the report.")

    # Export to PDF button
    export_as_pdf = st.button("Export Report")
    if export_as_pdf:
        if not username.strip():
            st.error("Please enter your name to generate the report.")
        else:
            # Create PDF instance
            pdf = FPDF()
            pdf.add_page()

            # Add the simmons bank logo to the PDF
            pdf.image(LOGO, x=10, y=8, w=30)

            # Add a title to the PDF besides the logo
            pdf.set_font('Arial', 'B', 16)
            pdf.set_xy(50, 10)
            pdf.cell(200, 10, "Simmons InfoLink - Summary Response", ln=True, align="L")

            pdf.ln(10)

            # Footer section with details
            pdf.set_font("Times", "", 12)
            current_time = datetime.now().strftime("%b %d, %Y at %I:%M %p")
            pdf.cell(0, 10, f"Generated by {username} on {current_time}", 0, 0, 'C')

            pdf.ln(10)

            # Query and formatted question
            pdf.set_font('Times', 'B', 12)
            pdf.multi_cell(0, 10, "Query:")
            formatted_question = question.strip().capitalize()
            pdf.set_font('Times', '', 12)
            pdf.multi_cell(0, 10, formatted_question)

            pdf.ln(5)

            # Response and formatted answer
            pdf.set_font('Times', 'B', 12)
            pdf.multi_cell(0, 10, "Response:")

            pdf.set_font('Times', '', 12)
            pdf.multi_cell(0, 10, st.session_state.answer)

            pdf.ln(5)

            # Sources Section
            pdf.set_font('Times', 'B', 12)
            pdf.multi_cell(0, 10, "Sources:")
            if st.session_state.sources:
                pdf.set_font('Times', '', 12)
                for i, source in enumerate(st.session_state.sources[:3], start=1):
                    source_title = source.get("title", "Unknown Document")
                    pdf.multi_cell(0, 10, f"[{i}] {source_title}")
            else:
                pdf.multi_cell(0, 10, "No sources available.")

            pdf_output = pdf.output(dest="S").encode("latin-1")
            html = create_download_link(pdf_output, "summary_response")
            st.markdown(html, unsafe_allow_html=True)


# Render list of other documents
if st.session_state.sources:
    st.session_state["source_id"] = choose_source_id(
        st.session_state.sources, "Search Results"
    )

# Render the selected document or reference
if "source_id" in st.session_state and st.session_state.source_id:
    logger.info(f"source_id: {st.session_state.source_id}")
    show_agent_document(st.session_state.source_id)
