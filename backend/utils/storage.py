import os
import logging
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
class StorageFactory:
    def list_blobs(self, prefix=None):
        """
        Lists all blobs in the container, optionally filtered by prefix.
        Args:
            prefix (str, optional): Filter blobs whose names begin with the prefix.
        Returns:
            list: List of blob names in the container.
        """
        logger = logging.getLogger(__name__)
        try:
            logger.info(f"Listing blobs in container '{self.container_name}' with prefix '{prefix}'.")
            blob_list = self.container_client.list_blobs(name_starts_with=prefix)
            blobs = [blob.name for blob in blob_list]
            logger.info(f"Found {len(blobs)} blobs.")
            return blobs
        except Exception as e:
            logger.error(f"Failed to list blobs: {e}")
            return []
    def __init__(self, account_url=None, container_name=None):
        """
        Initializes the StorageFactory with Entra ID authentication (DefaultAzureCredential).
        Args:
            account_url (str): The URL of the Azure Blob Storage account (e.g., https://<account>.blob.core.windows.net/)
            container_name (str): The name of the blob container.
        """
        logger = logging.getLogger(__name__)
        logger.info("Initializing StorageFactory with provided parameters or environment variables.")
        self.account_url = account_url or os.getenv("AZURE_STORAGE_ACCOUNT_ENDPOINT")
        self.container_name = container_name or "data"  # Default container name, can be overridden by environment variable
        if not self.account_url or not self.container_name:
            raise ValueError("Both account_url and container_name must be provided or set in environment variables.")
        self.credential = DefaultAzureCredential()
        logger.info(f"Using DefaultAzureCredential {self.credential}.")
        self.service_client = BlobServiceClient(account_url=self.account_url, credential=self.credential)
        self.container_client = self.service_client.get_container_client(self.container_name)

    def upload_file(self, file_path, blob_name=None):
        """
        Uploads a file to Azure Blob Storage using Entra ID authentication.
        Args:
            file_path (str): Local path to the file to upload.
            blob_name (str): Name of the blob in storage. If None, uses the file name.
        Returns:
            str: The URL of the uploaded blob.
        """
        logger = logging.getLogger(__name__)
        blob_name = blob_name or os.path.basename(file_path)
        logger.info(f"Uploading {file_path} to blob {blob_name} in container {self.container_name}.")
        blob_client = self.container_client.get_blob_client(blob_name)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        blob_url = f"{self.account_url}{self.container_name}/{blob_name}"
        logger.info(f"Upload complete. Blob URL: {blob_url}")
        return blob_url

    def download_file(self, blob_name, download_path=None):
        """
        Downloads a blob from Azure Blob Storage using Entra ID authentication.
        Args:
            blob_name (str): Name of the blob in storage.
            download_path (str): Local path to save the downloaded file. If None, uses blob_name in current dir.
        Returns:
            str: The path to the downloaded file.
        """
        logger = logging.getLogger(__name__)
        download_path = download_path or blob_name
        logger.info(f"Downloading blob {blob_name} from container {self.container_name} to {download_path}.")
        blob_client = self.container_client.get_blob_client(blob_name)
        with open(download_path, "wb") as file:
            download_stream = blob_client.download_blob()
            file.write(download_stream.readall())
        logger.info(f"Download complete. File saved to {download_path}.")
        return download_path

# Example usage:
if __name__ == "__main__":
    storage = StorageFactory()
    # storage.upload_file("../data/VO50_20s.MP3")
    # storage.download_file("blobname.txt", "downloaded.txt")
    blobs = storage.list_blobs(prefix="")
    print(blobs)