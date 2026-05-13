import os

from dotenv import load_dotenv

load_dotenv(override=True)

ZHIPU_KEY = os.getenv('ZHIPU_KEY')
ZHIPU_URL = os.getenv('ZHIPU_URL')
gaode_key = os.getenv('gaode_key')