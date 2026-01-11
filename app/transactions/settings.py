from dynaconf import Dynaconf

settings = Dynaconf(
    env_var_prefix="TRANSACTION_SERVICE",
    settings_files=[
        "app/transactions/config/default.toml",
        "app/transactions/config/settings.toml",
        "app/transactions/config/testing.toml",
    ],
    env_switcher="TRANSACTION_SERVICE_ENV",
    environments=True,
    load_dotenv=False,
    uppercase_keys=True,
)
