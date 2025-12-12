from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=[
        'app/config/default.toml',
        'app/config/settings.toml',
        'app/config/secrets.toml',
        'app/config/testing.toml',
    ],
    environments=True,
    load_dotenv=False,
    uppercase_keys=True
)

