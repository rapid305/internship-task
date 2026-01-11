from dynaconf import Dynaconf

settings = Dynaconf(
    env_var_prefix="USER_SERVICE",
    settings_files=[
        "app/users/config/default.toml",
        "app/users/config/settings.toml",
        "app/users/config/testing.toml",
    ],
    env_switcher="USER_SERVICE_ENV",
    environments=True,
    load_dotenv=False,
    uppercase_keys=True,
)
