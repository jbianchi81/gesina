import io
import logging
import os

from minio import Minio
from minio.commonconfig import CopySource

from src import logger, config

from src.service.exception.file_exception import FileUploadError, FilePreSignedUrlError
from werkzeug.utils import secure_filename

minio_client = Minio(
    endpoint=config.minio_url,
    access_key=config.minio_user,
    secret_key=config.minio_password,
    secure=False,
)

ROOT_BUCKET = config.minio_bucket

GEOMETRY_FOLDER = "geometry"
EXECUTION_FOLDER = "execution-plans"
RESULT_FOLDER = "results"
RESULT_FILE_EXTENSION = ".dss"


def save_geometry(file):
    save_file(GEOMETRY_FOLDER, file, file.filename)


def save_execution_file(file, execution_id):
    save_file(f"{EXECUTION_FOLDER}/{execution_id}", file, file.filename)


def save_execution_result_file(file, execution_id, filename):
    save_file(f"{EXECUTION_FOLDER}/{execution_id}/{RESULT_FOLDER}", file, filename)


def copy_geometry_to(execution_id, geometry_filename):
    minio_client.copy_object(
        ROOT_BUCKET,
        f"{EXECUTION_FOLDER}/{execution_id}/{geometry_filename}",
        CopySource(ROOT_BUCKET, f"{GEOMETRY_FOLDER}/{geometry_filename}"),
    )


def save_file(folder, file, filename):
    file_bytes = file.read()
    data = io.BytesIO(file_bytes)
    try:
        minio_client.put_object(
            ROOT_BUCKET,
            f"{folder}/{secure_filename(filename)}",
            data,
            len(file_bytes),
        )
    except Exception as exception:
        error_message = "Error uploading file"
        logger.error(error_message, exception)
        raise FileUploadError(error_message)


def get_geometry_url(name):
    try:
        return minio_client.get_presigned_url(
            "GET", ROOT_BUCKET, f"{GEOMETRY_FOLDER}/{name}"
        )
    except Exception as exception:
        error_message = f"Error generating presigned url for {name}"
        logger.error(error_message, exception)
        raise FilePreSignedUrlError(error_message)


def list_files_for_execution(execution_id):
    return minio_client.list_objects(ROOT_BUCKET, f"{EXECUTION_FOLDER}/{execution_id}/")


def get_file(file, bucket=ROOT_BUCKET):
    logging.info(f"Obtaining file {file} from bucket {bucket}")
    return minio_client.get_object(bucket, file)


def get_geometry_file(file):
    return get_file(f"{GEOMETRY_FOLDER}/{file}")


def get_execution_file(file):
    return get_file(f"{EXECUTION_FOLDER}/{file}")


def download_files_for_execution(base_path, execution_id):
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    logger.info("Downloading files")
    for file in list_files_for_execution(execution_id):
        file = file.object_name
        logger.info(file)
        with get_file(file) as response:
            file = file.split("/")[-1]
            file_extension = file.split(".")[-1]
            with open(f"{base_path}\\{execution_id}.{file_extension}", "wb") as f:
                f.write(response.data)


def save_result_for_execution(base_path, execution_id):
    logger.info(f"Saving result files for execution: {execution_id}")

    for filename in os.listdir(base_path):
        if filename.endswith(RESULT_FILE_EXTENSION):
            with open(f"{base_path}\\{filename}", "rb") as file:
                save_execution_result_file(file, execution_id, filename)
