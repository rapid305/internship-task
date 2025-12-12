from dynaconf import Dynaconf

settings = Dynaconf(
    env_var_prefix='PAYMENT_SERVICE',
    settings_files=[
        'app/config/default.toml',
        'app/config/settings.toml',
        'app/config/secrets.toml',
        'app/config/testing.toml',
    ],
    env_switcher="PAYMENT_SERVICE_ENV",
    environments=True,
    load_dotenv=False,
    uppercase_keys=True
)

