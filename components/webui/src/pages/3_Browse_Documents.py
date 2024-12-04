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
import pathlib

import pandas as pd  # type: ignore
import streamlit as st  # type: ignore
from dpu.api import fetch_all_agent_docs
from dpu.components import TITLE_LOGO, LOGO, show_agent_document
from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder  # type: ignore
from google.cloud import storage
from google.cloud import discoveryengine_v1beta as discoveryengine
import mimetypes

PROJECT_ID = os.environ["PROJECT_ID"]
LOCATION = os.environ["AGENT_BUILDER_LOCATION"]
SEARCH_DATASTORE_ID = os.environ["AGENT_BUILDER_DATA_STORE_ID"]
SEARCH_APP_ID = os.environ["AGENT_BUILDER_SEARCH_ID"]

logger = st.logger.get_logger(__name__)  # pyright: ignore[reportAttributeAccessIssue]


# Function to fetch and process document data
def get_document_dataframe():
    """Fetch and process document data for display."""
    df = pd.DataFrame(fetch_all_agent_docs())
    if len(df) > 0:
        df["bucket"] = df["uri"].str.extract(r"gs://([^/]*)/")
        df["path"] = df["uri"].str.extract(r"gs://[^/]*/(.*)$")
        df["name"] = df["path"].apply(lambda p: pathlib.Path(p).name)

        common_prefix = os.path.commonprefix(
            df["path"].apply(lambda p: pathlib.Path(p).parent).to_list() # type: ignore
        )
        df["full_name"] = df["path"].apply(lambda p: p[len(common_prefix) :])
        df["document_id"] = df["id"]
    return df

st.set_page_config(
    page_title="Browse Documents",
    page_icon=TITLE_LOGO,
    layout="wide",
)

image_col, title_col = st.columns([1, 2])
with image_col:
    st.image(LOGO, width=256)
    st.write("")
with title_col:
    st.title(":green[Document Corpus]")
st.divider()
st.markdown("""Full Document corpus accessible to the Search App. Select a document to either View, Download, or Delete it.""")

if "documents" not in st.session_state:
    st.session_state["documents"] = get_document_dataframe()

df = st.session_state["documents"]
if len(df) > 0:
    # Configure AgGrid table
    gb = GridOptionsBuilder()
    gb.configure_column("name", header_name="Name", flex=2)
    gb.configure_selection(selection_mode="single")
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=50)
    gridOptions = gb.build()

    # Render AgGrid
    data = AgGrid(
        df,
        gridOptions=gridOptions,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        allow_unsafe_jscode=True,
    )

    # Show document details when a row is selected
    if data["selected_rows"] is not None and len(data["selected_rows"]) > 0:
        show_agent_document(data["selected_rows"].iloc[0]["id"])
else:
    st.info("No documents available.")