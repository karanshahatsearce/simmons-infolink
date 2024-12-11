# pages/utils.py
import os
import pathlib
import pandas as pd
from dpu.api import fetch_all_agent_docs
from google.cloud import documentai_v1 as documentai
from google.cloud import storage
import json
from PyPDF2 import PdfReader, PdfWriter
from vertexai.generative_models import GenerativeModel, Part
import streamlit as st
import os
import pdfplumber
from google.cloud import discoveryengine_v1beta as discoveryengine
from google.cloud.discoveryengine_v1beta.types import DeleteDocumentRequest
from google.protobuf import struct_pb2
from types import SimpleNamespace

details = SimpleNamespace(name="Karan Shah", email="karan.shah@searce.com", role="ML engineer")


def get_document_dataframe():
    """Fetch and process document data for display."""
    df = pd.DataFrame(fetch_all_agent_docs())
    if len(df) > 0:
        df["bucket"] = df["uri"].str.extract(r"gs://([^/]*)/")
        df["path"] = df["uri"].str.extract(r"gs://[^/]*/(.*)$")
        df["name"] = df["path"].apply(lambda p: pathlib.Path(p).name)
        common_prefix = os.path.commonprefix(
            df["path"].apply(lambda p: pathlib.Path(p).parent).to_list()
        )
        df["full_name"] = df["path"].apply(lambda p: p[len(common_prefix) :])
    return df

def upload_to_gcs(bucket_name, destination_blob_name, local_file_path):
    """Uploads a file to the specified GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    
    # Use upload_from_filename for local file paths
    blob.upload_from_filename(local_file_path)
    
    return f"File {destination_blob_name} uploaded."

def batch_process_document(project_id, location, processor_id, input_gcs_uri, output_gcs_uri):
    """Processes a document using Document AI Batch API."""
    client = documentai.DocumentProcessorServiceClient()

    # Define processor name
    name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"

    # Extract bucket name and prefix from input GCS URI
    bucket_name, prefix = input_gcs_uri.replace("gs://", "").split("/", 1)

    # Configure input
    input_config = documentai.BatchDocumentsInputConfig(
        gcs_prefix=documentai.GcsPrefix(gcs_uri=input_gcs_uri)
    )

    # Configure output
    output_config = documentai.DocumentOutputConfig(
        gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(gcs_uri=output_gcs_uri)
    )

    # Create the request
    request = documentai.BatchProcessRequest(
        name=name,
        input_documents=input_config,
        document_output_config=output_config,
    )

    # Call the Batch API
    operation = client.batch_process_documents(request=request)

    print("Waiting for operation to complete...")
    operation.result(timeout=300)  # Waits for the operation to complete
    print(f"Batch processing completed. Output saved to: {output_gcs_uri}")
    return output_gcs_uri

def download_and_parse_output(output_gcs_uri, local_output_dir):
    """Downloads and parses the output JSON from GCS."""
    client = storage.Client()

    # Extract bucket name and prefix from the GCS URI
    bucket_name, prefix = output_gcs_uri.replace("gs://", "").split("/", 1)
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)

    summaries = []
    for blob in blobs:
        if blob.name.endswith(".json"):
            # Download the JSON file locally
            local_file_path = f"{local_output_dir}/{blob.name.split('/')[-1]}"
            blob.download_to_filename(local_file_path)

            # Parse the JSON to extract the document text
            with open(local_file_path, "r") as f:
                document = json.load(f)
                summaries.append(document.get("text", ""))

    # Combine all summaries
    return "\n\n".join(summaries)

def summarize_document_with_docai(project_id, location, processor_id, file_path, mime_type):
    """Summarizes a document using Google Cloud Document AI."""
    client = documentai.DocumentProcessorServiceClient()
    processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
    with open(file_path, "rb") as f:
        file_content = f.read()
    raw_document = {"content": file_content, "mime_type": mime_type}
    request = {"name": processor_name, "raw_document": raw_document}
    result = client.process_document(request=request)
    return result.document.text

def summarize_with_gemini(text):
    model = GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([f"Please summarize the following content in a concise manner, ensuring that only relevant information is included. The summary should be written in exactly 500 words. Structure the response with two paragraphs for a high-level overview and a bulleted list of detailed points. Use the exact wording from the provided content where possible. Do not add any additional information, and avoid bolding any text. DO NOT TRY TO BOLD ANYTHING! Also, for bullet points, use '-' and not '*', please. Here's the text: \n\n{text}. \n\n Make sure you add 600 words."])
    return response.text.replace("*", "")

def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def delete_metadata_from_eks(document_id):
    """
    Deletes document metadata from the EKS datastore.

    Args:
        document_id (str): The unique identifier of the document to delete.
                           (e.g., b4f4330609ae54b626f8dd026c59090c)
    """

    client = discoveryengine.DocumentServiceClient()

    # Extract project, location, and data store information
    project_id = os.environ["PROJECT_ID"]
    location = os.environ["AGENT_BUILDER_LOCATION"]
    data_store_id = os.environ["AGENT_BUILDER_DATA_STORE_ID"]
    collection = "default_collection"
    branch = "0"

    # Construct the full document path
    document_path = (
        f"projects/{project_id}/locations/{location}/collections/{collection}/"
        f"dataStores/{data_store_id}/branches/{branch}/documents/{document_id}"
    )

    request = DeleteDocumentRequest(name=document_path)

    try:
        client.delete_document(request=request)
        print(f"Metadata for document {document_id} successfully deleted from EKS datastore.")
        st.rerun()
    except Exception as e:
        raise Exception(f"Failed to delete metadata for {document_id}: {e}")
    