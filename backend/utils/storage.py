import os
import logging
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, BlobSasPermissions
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
        self.service_client = BlobServiceClient(account_url=self.account_url, credential=self.credential)
        self.container_client = self.service_client.get_container_client(self.container_name)

    def upload_file(self, file_path, blob_name=None, generate_sas=False, sas_expiry_hours=24):
        """
        Uploads a file to Azure Blob Storage using Entra ID authentication.
        Args:
            file_path (str): Local path to the file to upload.
            blob_name (str): Name of the blob in storage. If None, uses the file name.
            generate_sas (bool): Whether to generate a SAS token for the uploaded blob.
            sas_expiry_hours (int): Number of hours the SAS token should be valid (default: 24).
        Returns:
            str: The URL of the uploaded blob, or the SAS URL if generate_sas is True.
        """
        logger = logging.getLogger(__name__)
        blob_name = blob_name or os.path.basename(file_path)
        logger.info(f"Uploading {file_path} to blob {blob_name} in container {self.container_name}.")
        blob_client = self.container_client.get_blob_client(blob_name)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        if generate_sas:
            blob_url = self.generate_sas_token(blob_name, sas_expiry_hours)
            logger.info(f"Upload complete. SAS URL generated: {blob_url}")
        else:
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

    def generate_sas_token(self, blob_name, expiry_hours=24):
        """
        Generates a SAS token for read access to a specific blob.
        Args:
            blob_name (str): Name of the blob to generate SAS token for.
            expiry_hours (int): Number of hours the SAS token should be valid (default: 24).
        Returns:
            str: The full URL with SAS token for read access to the blob.
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Calculate expiry time
            start_time = datetime.utcnow()
            expiry_time = start_time + timedelta(hours=expiry_hours)
            
            logger.info(f"Generating SAS token for blob '{blob_name}' valid until {expiry_time}")
            
            # Get the account key from environment variables
            account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
            
            if not account_key or not account_name:
                raise ValueError("AZURE_STORAGE_ACCOUNT_KEY and AZURE_STORAGE_ACCOUNT_NAME must be set in environment variables for SAS token generation")
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=expiry_time,
                start=start_time
            )
            
            # Construct the full URL with SAS token
            blob_url_with_sas = f"{self.account_url}{self.container_name}/{blob_name}?{sas_token}"
            
            logger.info(f"SAS token generated successfully. URL valid until {expiry_time}")
            return blob_url_with_sas
            
        except Exception as e:
            logger.error(f"Failed to generate SAS token for blob '{blob_name}': {e}")
            raise

    def generate_sas_url_for_upload(self, blob_name, expiry_hours=1):
        """
        Generates a SAS URL with read/write permissions for uploading a blob.
        Args:
            blob_name (str): Name of the blob to generate SAS token for.
            expiry_hours (int): Number of hours the SAS token should be valid (default: 1).
        Returns:
            str: The full URL with SAS token for read/write access to the blob.
        """
        logger = logging.getLogger(__name__)
        
        try:
            # Calculate expiry time
            start_time = datetime.utcnow()
            expiry_time = start_time + timedelta(hours=expiry_hours)
            
            logger.info(f"Generating SAS token for upload to blob '{blob_name}' valid until {expiry_time}")
            
            # Get the account key from environment variables
            account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
            account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
            
            if not account_key or not account_name:
                raise ValueError("AZURE_STORAGE_ACCOUNT_KEY and AZURE_STORAGE_ACCOUNT_NAME must be set in environment variables for SAS token generation")
            
            # Generate SAS token with read/write permissions
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True, write=True, create=True),
                expiry=expiry_time,
                start=start_time
            )
            
            # Construct the full URL with SAS token
            blob_url_with_sas = f"{self.account_url}{self.container_name}/{blob_name}?{sas_token}"
            
            logger.info(f"Upload SAS token generated successfully. URL valid until {expiry_time}")
            return blob_url_with_sas
            
        except Exception as e:
            logger.error(f"Failed to generate upload SAS token for blob '{blob_name}': {e}")
            raise

# Example usage:
if __name__ == "__main__":
    storage = StorageFactory()
    
    # List blobs
    blobs = storage.list_blobs(prefix="")
    print("Available blobs:", blobs)
    
    # Upload a file
    # storage.upload_file("../data/VO50_20s.MP3")
    
    # Download a file
    # storage.download_file("blobname.txt", "downloaded.txt")
    
    # Generate SAS token for read access (24 hours by default)
    # if blobs:
    #     sas_url = storage.generate_sas_token(blobs[0])
    #     print(f"SAS URL for read access: {sas_url}")
    
    # Generate SAS token for upload (1 hour by default)
    # upload_sas_url = storage.generate_sas_url_for_upload("new-file.wav")
    # print(f"SAS URL for upload: {upload_sas_url}")