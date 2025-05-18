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
VECT_MODEL_NAME = "MrLight/dse-qwen2-2b-mrl-v1"
VECT_MODEL_LOCAL_PATH = "weights_vect_model"