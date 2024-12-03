# pages/utils.py
import os
import pathlib
import pandas as pd
from dpu.api import fetch_all_agent_docs

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
