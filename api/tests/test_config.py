from app.core.config import montar_settings, parse_env_linhas


def test_parse_env_linhas_ignora_comentarios_e_vazios() -> None:
    linhas = [
        "# comentário",
        "",
        "APP_ENV=dev",
        "MYSQL_PORT = 3307 ",
        'MYSQL_PASSWORD="se=nha"',
    ]
    assert parse_env_linhas(linhas) == {
        "APP_ENV": "dev",
        "MYSQL_PORT": "3307",
        "MYSQL_PASSWORD": "se=nha",
    }


def test_parse_env_linhas_e_pura() -> None:
    linhas = ["A=1", "B=2"]
    assert parse_env_linhas(linhas) == parse_env_linhas(linhas)  # determinística
    assert linhas == ["A=1", "B=2"]  # não altera a entrada


def test_montar_settings_com_defaults() -> None:
    settings = montar_settings({})
    assert settings.app_env == "dev"
    assert settings.mysql_port == 3306
    assert settings.database_url.startswith("mysql+pymysql://")


def test_montar_settings_le_ambiente() -> None:
    settings = montar_settings({"MYSQL_HOST": "db.interno", "MYSQL_PORT": "3310"})
    assert settings.mysql_host == "db.interno"
    assert settings.mysql_port == 3310
    assert "@db.interno:3310/" in settings.database_url
