# config.py

from dotenv import load_dotenv
import os



load_dotenv(override=True)

"""Storage stuff"""
LOCAL_STORAGE_PATH = "storage"
ORIGIN_FOLDER = "docs_to_process"


"""Database stuff"""
LOCAL_DB_PATH = "database/mydatabase.db"


"""Vectorization stuff"""
VECT_MODEL_NAME = "Qwen/Qwen2.5-VL-3B-Instruct"