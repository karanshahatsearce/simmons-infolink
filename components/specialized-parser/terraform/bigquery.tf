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


resource "google_bigquery_table" "processed_documents" {
  dataset_id = var.bigquery_dataset_id
  table_id   = "prcessed_documents"
  schema     = file("${path.module}/processed_documents.json")

  # NOTE: For production use-cases, change this!
  deletion_protection = false
}

resource "google_bigquery_table_iam_member" "member" {
  project    = google_bigquery_table.processed_documents.project
  dataset_id = google_bigquery_table.processed_documents.dataset_id
  table_id   = google_bigquery_table.processed_documents.table_id
  role       = "roles/bigquery.dataOwner"
  member     = module.specialized_parser_account.iam_email
}
