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
from dpu.components import LOGO, PREAMBLE, choose_source_id, show_agent_document

logger = st.logger.get_logger(__name__)  # pyright: ignore[reportAttributeAccessIssue]

# Put into a single place
SAMPLE_QUERIES = """
```
    Generate a Table to summarize the Quarterly Revenue
of Google Cloud in 2024, 2023, and 2022.
```
```
    How many shares the Intelligent Group Limited offers
in their IPO filing?
```
```
    Create a table showing 2021 and 2022 annual revenue
of RYDE, and INTJ? Summarize the results.
```
```
    Summarize the outage in Denver.
```
```
    How long was the outage duration in Denver?
```
```
    List the incident number, owner,  RCA analyst, data,
root cause, and resolution for ticket #: T010101?
```
```
    Who is Sally Walker?
```
```
    Display a CPT1 Code for the clinical laboratory
service: "Cell enumeration phys interp"?
```
"""
#
# Page Layout
#

# Page configuration
st.set_page_config(
    page_title="Search and Summarization",
    page_icon=LOGO,
    layout="wide",
)

# Title
image_col, text_col = st.columns([10, 90])
with image_col:
    st.write("")
    st.image(LOGO, "", 64)
with text_col:
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
        
    query_col, button_col = st.columns([10, 1])

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

# Render the answer if there is a response
if st.session_state.answer:
    st.markdown("### :blue[Summary Response:]")
    ans = st.session_state.answer
    st.text_area("Summary", value=ans, height=240)

# Render list of other documents
if st.session_state.sources:
    st.session_state["source_id"] = choose_source_id(
        st.session_state.sources, "Search Results"
    )

# Render the selected document or reference
if "source_id" in st.session_state and st.session_state.source_id:
    logger.info(f"source_id: {st.session_state.source_id}")
    show_agent_document(st.session_state.source_id)
