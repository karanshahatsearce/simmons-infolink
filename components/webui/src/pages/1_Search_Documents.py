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
import os
import streamlit as st  # type: ignore
from dpu.api import generate_answer
from dpu.components import SIMMONS_LOGO, TITLE_LOGO, LOGO, PREAMBLE, choose_source_id, show_agent_document
from fpdf import FPDF # type: ignore
logger = st.logger.get_logger(__name__)  # pyright: ignore[reportAttributeAccessIssue]
import base64
from datetime import datetime
from vertexai.generative_models import GenerativeModel
from dpu.api import fetch_all_agent_docs
from dpu.utils import get_document_dataframe, upload_to_gcs, summarize_with_gemini, extract_text_from_pdf


class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(left=20, top=20, right=20)
        self.set_auto_page_break(auto=True, margin=20)



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
if "query_triggered" not in st.session_state:
    st.session_state["query_triggered"] = False
if "upload_triggered" not in st.session_state:
    st.session_state["upload_triggered"] = False
if "documents" not in st.session_state:
    st.session_state["documents"] = get_document_dataframe()

#
# Dropdown for document selection
#
selected_document = ""
df = st.session_state["documents"]
if len(df) > 0:
    document_names = df["name"].tolist()
    selected_document = st.selectbox(
        """### Select an existing document to summarize it:""",
        options=["Select a document"] + document_names,
        key="selected_document"
    )

    if selected_document != "Select a document":
        selected_row = df[df["name"] == selected_document].iloc[0]
        st.write(f"### Selected Document: {selected_document}")

        # Summarize button
        if st.button("Summarize Document"):
            try:
                # Fetch the full path (uri) of the selected document
                selected_doc_uri = selected_row["uri"]

                # Download and extract text from the document
                from google.cloud import storage
                storage_client = storage.Client()
                bucket_name = selected_row["bucket"]
                path = selected_row["path"]
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(path)
                local_file_path = f"./{selected_document}"
                blob.download_to_filename(local_file_path)

                text = extract_text_from_pdf(local_file_path)

                # Generate a summary
                summary = summarize_with_gemini(text)

                st.session_state["doc_triggered"] = True
                st.session_state["current_summary"] = summary
                st.session_state["current_summary_type"] = "summarize"

                # Remove document after use
                try:
                    if os.path.exists(local_file_path):
                        os.remove(local_file_path)
                    else:
                        st.warning(f"File does not exist.")
                except Exception as e:
                    st.error(f"An error occured while deleting the file: {e}")
            except Exception as e:
                st.error(f"An error occurred while summarizing: {e}")

else:
    st.info("No documents available.")

if st.session_state.get("doc_triggered") and st.session_state.get("current_summary"):
    st.write("### Document Summary")
    st.text_area(
        "Summary",
        value=st.session_state["current_summary"],
        height=300,
        disabled=True,
    )

# Add an export as PDF button here
if st.session_state.get("current_summary"):
    pdf = PDF()
    pdf.add_page()

    pdf.image(SIMMONS_LOGO, x=10, y=8, w=100)
    
    # Add date and title
    pdf.set_font('Times', '', 10)
    current_time = datetime.now().strftime("%b %d, %Y at %I:%M %p")
    pdf.set_xy(150, 23)
    pdf.cell(0, 10, current_time, align='R')

    pdf.ln(10)

    selected_doc_title = f"Summary of Financials for {selected_document}"
    pdf.set_font("Arial", "B", 16)
    pdf.set_xy(15, 35)
    pdf.multi_cell(0, 5, selected_doc_title, align='C')
    
    pdf.ln(5)

    pdf.set_font("Times", "", 13)

    cleaned_summary = (
        st.session_state["current_summary"]
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    pdf.multi_cell(0, 5, cleaned_summary)
    
    pdf_output = pdf.output(dest="S")
    st.download_button(
        label="Download Summary as PDF",
        data=bytes(pdf_output),
        file_name="document_summary.pdf",
        mime="application/pdf",
    )

#
# Form
#
st.divider()
if "preamble" not in st.session_state:
    st.session_state["preamble"] = PREAMBLE

def get_document_urls():
    """Fetch document metadata and return a mapping of titles to their urls"""
    document_metadata = fetch_all_agent_docs()
    document_urls = {}

    for doc in document_metadata:
        title = doc.get("title", "").strip()
        uri = doc.get("uri", "").strip()
        if title and uri:
            document_urls[title] = uri

    return document_urls

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

st.write(
    """### Given a query, DocuWhizz will generate an answer with citations to the documents."""
)

query_col, button_col, example_col = st.columns([85, 15, 15])

with query_col:
    question = st.text_input(
        label="",
        value="",
        placeholder="e.g., What are Simmons Bank Q1 2023 details?",
        key="question",
    )

with button_col:
    st.write("")
    st.write("")
    if st.button("Execute Query"):
        st.session_state["query_triggered"] = True  # Trigger query
        st.session_state["upload_triggered"] = False  # Disable upload trigger
        try:
            result = generate_answer(
                st.session_state.question, preamble=st.session_state["preamble"]
            )
            st.session_state.answer = result["answer"]
            st.session_state.sources = result["sources"]
            st.session_state["query_triggered"] = True
            st.session_state["upload_triggered"] = False
        except Exception as e:
            st.error(f"An error occurred while processing the query: {e}")

with example_col:
    st.write("")
    st.write("")
    
    with st.popover("Examples"):
        st.markdown(SAMPLE_QUERIES, unsafe_allow_html=True)

st.divider()

# Handle and display the relevant summary
if st.session_state["query_triggered"]:
    st.session_state["current_summary"] = st.session_state.answer
    st.session_state["current_summary_type"] = "query"
    st.markdown("### :blue[Query-Based Summary:]")
    st.text_area(
        "Summary", 
        value=st.session_state.answer, 
        height=240, 
        key="query_summary_textarea", 
        disabled=True
    )

    # Render the answer if there is a response
    if st.session_state["query_triggered"] and st.session_state.get("current_summary"):
        pdf = PDF()
        pdf.add_page()
        llm = GenerativeModel("gemini-1.5-flash")

        if st.session_state["upload_triggered"]:
            doc_sum = st.session_state["current_summary"]
            title_prompt = f"Generate a concise title for the summary of the uploaded document: {doc_sum}. Do not include hashtags or preambles."
        else:
            title_prompt = f"Generate a concise title for the query: {question}. Do not include hashtags or preambles."
        title = llm.generate_content(title_prompt)

        pdf_title = title.text.strip().encode("ascii", "ignore").decode("ascii")

        pdf.image(SIMMONS_LOGO, x=10, y=8, w=100)
        
        # Add date and title
        pdf.set_font('Times', '', 10)
        current_time = datetime.now().strftime("%b %d, %Y at %I:%M %p")
        pdf.set_xy(150, 23)
        pdf.cell(0, 10, current_time, align='R')

        pdf.ln(10)

        pdf.set_xy(0, 35)
        pdf.set_font('Arial', 'B', 16)
        pdf.multi_cell(0, 5, pdf_title, align='C')

        pdf.ln(5)

        pdf.set_font("Times", "", 13)
        pdf.multi_cell(0, 5, st.session_state["current_summary"].encode("ascii", "ignore").decode("ascii"))

        if not st.session_state["upload_triggered"]:
            pdf.set_font("Times", "B", 14)
            pdf.multi_cell(0, 7, "Sources:")
            if st.session_state.sources:
                pdf.set_font("Times", "", 14)
                for i, source in enumerate(st.session_state.sources[:3], start=1):
                    source_title = source.get("uri", "Unknown Document").encode("ascii", "ignore").decode("ascii").replace("gs://docs-input-applied-ai-practice00/", "")
                    pdf.multi_cell(0, 7, f"[{i}] {source_title}")
            else:
                pdf.multi_cell(0, 7, "No sources available.")

        pdf.set_font("Times", "", 12)
        pdf_output = pdf.output(dest="S")
        st.download_button(
            label="Download PDF",
            data=bytes(pdf_output),
            file_name="query_response.pdf",
            mime="application/pdf",
        )

elif st.session_state["upload_triggered"]:
    st.session_state["current_summary"] = doc_summary
    st.session_state["current_summary_type"] = "upload"
    st.markdown("### :blue[Document-Based Summary:]")
    st.text_area("Summary", value=doc_summary, height=240, key="upload_summary_textarea", disabled=True)

# Logic to avoid simultaneous execution
if st.session_state["upload_triggered"] and st.session_state["query_triggered"]:
    st.warning("Please complete one action (Upload or Query) at a time.")

# Inform about successful upload
elif st.session_state["upload_triggered"] and not st.session_state["query_triggered"]:
    st.info("Upload completed successfully.")

# Add an export as PDF button here
def create_download_link(value, filename):
    """Generate a download link for the PDF."""
    b64 = base64.b64encode(value)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'


# Render list of other documents
if st.session_state.sources:
    st.session_state["source_id"] = choose_source_id(
        st.session_state.sources, "Search Results"
    )

# Render the selected document or reference
if "source_id" in st.session_state and st.session_state.source_id:
    logger.info(f"source_id: {st.session_state.source_id}")
    show_agent_document(st.session_state.source_id)
