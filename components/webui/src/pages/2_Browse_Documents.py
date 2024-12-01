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

logger = st.logger.get_logger(__name__)  # pyright: ignore[reportAttributeAccessIssue]

def upload_to_gcs(bucket_name, destination_blob_name, file):
    """Uploads a file to the specified GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)
    return f"File {destination_blob_name} uploaded to bucket {bucket_name}."

st.set_page_config(
    page_title="Browse and Upload Documents",
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
st.markdown("""Full Document corpus accessible to the Search App.""")

df = pd.DataFrame(fetch_all_agent_docs())

if len(df) > 0:

    # Extract bucket and path
    df["bucket"] = df["uri"].str.extract(r"gs://([^/]*)/")
    df["path"] = df["uri"].str.extract(r"gs://[^/]*/(.*)$")

    # Extract parent and name from the path
    df["name"] = df["path"].apply(lambda p: pathlib.Path(p).name)
    common_prefix = os.path.commonprefix(
        df["path"].apply(lambda p: pathlib.Path(p).parent).to_list()
    )
    df["full_name"] = df["path"].apply(lambda p: p[len(common_prefix) :])

    gb = GridOptionsBuilder()
    gb.configure_column("name", header_name="Name", flex=0)
    gb.configure_column("full_name", header_name="Full Name", flex=1)
    gb.configure_selection()
    gb.configure_pagination()
    gridOptions = gb.build()

    data = AgGrid(
        df,
        gridOptions=gridOptions,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        allow_unsafe_jscode=True,
    )

    if data["selected_rows"] is not None and len(data["selected_rows"]) > 0:
        show_agent_document(data["selected_rows"].iloc[0]["id"])

# Upload Functionality
st.divider()
st.markdown("### Upload a Document to GCS")
bucket_name = df["bucket"].iloc[0]
file = st.file_uploader("Choose a file to upload: ")

if file and bucket_name:
    if st.button("Upload"):
        try:
            destination_blob_name = file.name
            with st.spinner("Uploading file..."):
                result = upload_to_gcs(bucket_name, destination_blob_name, file)
            st.success(result)
        except Exception as e:
            st.error(f"An error occurred during upload: {e}")