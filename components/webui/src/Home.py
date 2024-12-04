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
from dpu.components import LOGO, TITLE_LOGO
from dpu.utils import details
logger = st.logger.get_logger(__name__)  # pyright: ignore[reportAttributeAccessIssue]


st.set_page_config(
    page_title="DocuWhizz",
    page_icon=TITLE_LOGO,
    layout="wide",
)

image_col, title_col = st.columns([1, 2])
with image_col:
    st.write("")
    st.image(LOGO, "", 256)
with title_col:
    st.title(":green[DocuWhizz]")
st.markdown("""   """)

html_str = f"""
<style>
p.greeting {{
  font: 16px;
}}
</style>
<p class="greeting">Hi {details.name}! I'm DocuWhizz, here to help you with your document search requests. Feel free to ask any document-related questions, and I'd be happy to assist!</p>

<p> DocuWhizz is an advanced application designed to search and summarize documents, providing precise answers with citations for improved knowledge access and decision-making.
    The app integrates with the Vertex AI Agent Builder using APIs.
"""
st.markdown(html_str, unsafe_allow_html=True)

if st.button("Start Search"):
    st.switch_page("pages/1_Search_Documents.py")

st.divider()
