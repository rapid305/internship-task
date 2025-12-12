from dynaconf import Dynaconf

settings = Dynaconf(
    load_dotenv=True,
    envvar_prefix=False,
)

DATABASE_URL = settings.DATABASE_URL
