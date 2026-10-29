import os
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("CLOUD_STORAGE")
logging.basicConfig(level=logging.INFO)

# Optional GCP imports (graceful fallback if offline or local)
try:
    from google.cloud import storage
    from google.cloud import bigquery
    HAS_GCP_LIBS = True
except ImportError:
    HAS_GCP_LIBS = False

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "tradeverse-ai-models")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "tradeverse-fe8ef")

class CloudStorageManager:
    """Manages 24/7 cloud data persistence between local/VM storage and Google Cloud Platform (GCS & BigQuery)."""
    
    def __init__(self, bucket_name: str = GCS_BUCKET_NAME, project_id: str = GCP_PROJECT_ID):
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.storage_client = None
        self.bq_client = None
        
        if HAS_GCP_LIBS:
            try:
                self.storage_client = storage.Client(project=self.project_id)
                self.bq_client = bigquery.Client(project=self.project_id)
                logger.info(f"✅ Initialized GCP Cloud Storage & BigQuery Client for project: {self.project_id}")
            except Exception as e:
                logger.warning(f"⚠️ Cloud Storage running in local-only fallback mode: {e}")

    def upload_model_checkpoint(self, local_file_path: str, remote_filename: str = None) -> bool:
        """Uploads trained AI model checkpoints (.joblib, .pth, .zip) to GCS bucket."""
        path = Path(local_file_path)
        if not path.exists():
            logger.error(f"Cannot upload non-existent model file: {local_file_path}")
            return False
            
        target_name = remote_filename or path.name
        
        if self.storage_client:
            try:
                bucket = self.storage_client.bucket(self.bucket_name)
                blob = bucket.blob(f"models/{target_name}")
                blob.upload_from_filename(str(path))
                logger.info(f"☁️ Successfully uploaded model {target_name} to gs://{self.bucket_name}/models/")
                return True
            except Exception as e:
                logger.error(f"GCP upload failed for {target_name}: {e}")
                return False
        else:
            logger.info(f"ℹ️ [LOCAL MODE] Model checkpoint {target_name} safely stored locally at {local_file_path}")
            return True

    def upload_observatory_simulation(self, simulation_json_path: str) -> bool:
        """Syncs daily observatory simulation journals to GCS bucket and updates GitHub backup manifests."""
        path = Path(simulation_json_path)
        if not path.exists():
            return False

        # Always keep GitHub backup manifests synchronized
        try:
            from github_backup_manager import github_backup_manager
            github_backup_manager.generate_backup_manifests()
        except Exception as e:
            logger.debug(f"GitHub manifest update warning: {e}")
            
        if self.storage_client:
            try:
                bucket = self.storage_client.bucket(self.bucket_name)
                blob = bucket.blob(f"observatory_logs/{path.name}")
                blob.upload_from_filename(str(path))
                logger.info(f"☁️ Synced Observatory log {path.name} to GCS.")
                return True
            except Exception as e:
                logger.error(f"GCP sync failed for {path.name}: {e}")
                return False
        return True

    def fetch_model_from_cloud(self, remote_filename: str, local_destination_path: str) -> bool:
        """Downloads latest trained model checkpoint from GCS bucket or GitHub Raw backup if missing locally."""
        if self.storage_client:
            try:
                bucket = self.storage_client.bucket(self.bucket_name)
                blob = bucket.blob(f"models/{remote_filename}")
                blob.download_to_filename(local_destination_path)
                logger.info(f"📥 Downloaded latest {remote_filename} from GCS bucket.")
                return True
            except Exception as e:
                logger.warning(f"Could not download {remote_filename} from GCS: {e}")

        # Fallback: attempt restore from GitHub backup repository
        try:
            from github_backup_manager import github_backup_manager
            if github_backup_manager._download_raw_file(f"backend/{remote_filename}", Path(local_destination_path)):
                logger.info(f"📥 Restored {remote_filename} from GitHub backup.")
                return True
        except Exception as e:
            logger.debug(f"GitHub model restore fallback failed: {e}")
        return False

# Global Singleton Instance
cloud_manager = CloudStorageManager()
