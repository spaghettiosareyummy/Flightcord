from dotenv import load_dotenv
import os

load_dotenv()

DEBUG = True

DEV_GUILD = int(os.environ.get("DEV_GUILD"))