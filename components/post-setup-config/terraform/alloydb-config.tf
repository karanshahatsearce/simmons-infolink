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

locals {
  # specification of the alloy db docs of removing the .gserviceaccount.com part: https://cloud.google.com/alloydb/docs/manage-iam-authn#create-user
  alloydb_username     = replace(module.configure_schema_account.email, ".gserviceaccount.com", "")
  service_account_name = var.configure_schema_cloud_run_job_name
}

resource "google_cloud_run_v2_job" "configure_db_schema_job" {
  name     = var.configure_schema_cloud_run_job_name
  location = var.region
  template {
    template {
      service_account = module.configure_schema_account.email
      vpc_access {
        network_interfaces {
          network    = var.vpc_network_name
          subnetwork = var.serverless_connector_subnet
        }
        egress = "PRIVATE_RANGES_ONLY"
      }
      containers {
        image = local.image_name_and_tag
        name  = var.configure_schema_cloud_run_job_name
        resources {
          limits = {
            cpu    = "2"
            memory = "2048Mi"
          }
        }
        env {
          name  = "ALLOYDB_INSTANCE"
          value = var.alloydb_primary_instance
        }
        env {
          name  = "ALLOYDB_DATABASE"
          value = var.alloydb_database
        }
        env {
          name  = "ALLOYDB_USER_CONFIG"
          value = replace(module.configure_schema_account.email, ".gserviceaccount.com", "")
        }
        env {
          name  = "ALLOYDB_USER_SPECIALIZED_PARSER"
          value = replace(var.specialized_parser_db_user, ".gserviceaccount.com", "")
        }
      }
    }
  }
  lifecycle {
    ignore_changes = [
      effective_labels["goog-packaged-solution"],
      terraform_labels["goog-packaged-solution"],
      labels["goog-packaged-solution"]
    ]
  }
}

module "gcloud_trigger_job_to_configure_alloydb_schema" {
  source                = "github.com/terraform-google-modules/terraform-google-gcloud?ref=db25ab9c0e9f2034e45b0034f8edb473dde3e4ff" # commit hash of version 3.5.0
  create_cmd_entrypoint = "gcloud"
  create_cmd_body       = <<-EOT
    run jobs execute ${google_cloud_run_v2_job.configure_db_schema_job.name} \
      --region ${var.region}
  EOT
  enabled               = true
}



module "configure_schema_account" {
  source     = "github.com/terraform-google-modules/terraform-google-service-accounts?ref=a11d4127eab9b51ec9c9afdaf51b902cd2c240d9" #commit hash of version 4.0.0
  project_id = var.project_id
  prefix     = "eks"
  names      = [local.service_account_name]
  project_roles = [
    "${var.project_id}=>roles/alloydb.databaseUser",
    "${var.project_id}=>roles/alloydb.client",
    "${var.project_id}=>roles/serviceusage.serviceUsageConsumer",
  ]
  display_name = "AlloyDB db configuration Account"
  description  = "Account used to run configure the schema and db roles in AlloyDB"
}

resource "google_alloydb_user" "schema_setup_user" {
  cluster        = var.alloy_db_cluster_id
  user_id        = local.alloydb_username
  user_type      = "ALLOYDB_IAM_USER"
  database_roles = ["alloydbiamuser", "alloydbsuperuser"]

  depends_on = [var.alloydb_cluster_ready]
}
