from typing import Optional

from pydantic import BaseModel
import yaml


class Config(BaseModel):
    db_name: str
    bot_token: str
    proxy: Optional[dict]
    openai_api_key_default: str
    openai_test_model: str


def get_config(yaml_file_name: str) -> Config:
    """
    Получить конфигурацию для приложения
    :yaml_file_name: Путь до конфига приложения
    :return: Config
    """

    with open(yaml_file_name, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Config(**data)


# Test read config
if __name__ == '__main__':
    config = get_config('config.yaml')
    print(config)
