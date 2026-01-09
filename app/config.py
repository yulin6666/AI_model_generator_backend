"""App configuration using pydantic-settings"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Replicate
    replicate_api_token: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # VTON Models on Replicate (不指定版本号，使用最新版)
    idm_vton_model: str = "cuuupid/idm-vton"
    ootd_model: str = "viktorfa/oot_diffusion:9f8fa4956970dde99689af7488157a30aa152e23953526a605df1d77598343d7"
    catvton_model: str = "zhengchong/cat-vton:2e4e24460dd86bdb929df68ff1a76830c605ad1b7cbd4e51a6a1b71d4e5ed1f5"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
