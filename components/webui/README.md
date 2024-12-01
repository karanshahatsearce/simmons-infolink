# Reference Implementation of Web UI to access EKS

The Web-UI is a Web App to interface with Vertex AI Agent Builder using REST APIs

## Deploy Locally

Set environment variables:

```commandline
export PROJECT_ID="applied-ai-practice00"
export AGENT_BUILDER_DATA_STORE_ID="eks-data-store"
export AGENT_BUILDER_LOCATION="global"
export AGENT_BUILDER_SEARCH_ID="ent-search-agent"
```

Command to create a virtual environment if building this App for the first time.

```commandline
python3 -m venv .venv
```

Activate the virtual environment

```commandline
source .venv/bin/activate
```

Install dependencies

```commandline
pip install -r ../../components/webui/requirements.txt
```

Initialize gcloud and set project

```commandline
gcloud init
```

Authenticate to set Google Application Default Credentials

```commandline
gcloud auth application-default login
```

Launch

```commandline
streamlit run ../../components/webui/src/Home.py
```

## Deploy to Cloud Run

Set environment variables

```commandline
export AR_REPO=[your-ar-repo-name]
export AR_REPO_LOCATION=[your-ar-repo-region]
export SERVICE_NAME=[your-app-name]
```

If this is the first time you are trying to deploy the App in your GCP Project,
you must enable APIs and Create an Artifact repository in your new GCP Project.
**You can skip this if a repository already exists!**

```commandline
gcloud config set project $GOOGLE_CLOUD_PROJECT

gcloud artifacts repositories create "$AR_REPO" --location="$AR_REPO_LOCATION" --repository-format=Docker

gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

```

Build the app and save it in the Artifact repository

```commandline
./build.sh
```

Deploy the app from the Artifact repository to Cloud Run

```commandline
./deploy.sh
```

Test locally using Cloud Run proxy

```commandline
./run_proxy.sh
```
