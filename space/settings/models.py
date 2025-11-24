from pydantic import Field
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    dataset_url: str      = Field(validation_alias="DATASET_URL", default="sudoping01/bambara-speech-recognition-benchmark")
    dataset_config: str   = Field(validation_alias="DATASET_CONFIG", default="default")
    split_name: str       = Field(validation_alias="SPLIT_NAME", default="eval")
    leaderboard_file: str = Field(validation_alias="LEADERBOARD_FILE", default="leaderboard.csv")
    logo_path: str        = Field(validation_alias="LOGO_PATH", default="assets/images/bambara-logo.png")
    hf_token: str         = Field(validation_alias="HF_TOKEN", default=os.environ.get("HF_TOKEN"))
    github_user: str      = Field(validation_alias="GITHUB_USER", default="sudoping01")
    github_repo: str      = Field(validation_alias="GITHUB_REPO", default="MALIBA-AI/bambara-asr-leaderboard")
    github_email: str     = Field(validation_alias="GITHUB_EMAIL", default="sudoping01@gmail.com")
    github_token: str     = Field(validation_alias="GITHUB_TOKEN", default=os.environ.get("GITHUB_TOKEN"))







