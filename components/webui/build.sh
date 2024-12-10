#!/bin/bash

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

export PROJECT_ID="applied-ai-practice00"
export REGION="us"
export IAP_ADMIN_ACCOUNT="karan.shah@searce.com"
export AGENT_BUILDER_DATA_STORE_ID="eks-data-store"
export AGENT_BUILDER_LOCATION="us"
export AGENT_BUILDER_SEARCH_ID="ent-search-agent"
export AR_REPO="simmons-infolink"
export AR_REPO_LOCATION="us-central1"
export SERVICE_NAME="docuwhizz"
export GOOGLE_CLOUD_PROJECT=$PROJECT_ID

cp "$HOME"/.config/gcloud/application_default_credentials.json ./adc.json

gcloud builds submit ../../components/webui/terraform/build \
    --tag "$AR_REPO_LOCATION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$AR_REPO/$SERVICE_NAME"

rm ./adc.json
