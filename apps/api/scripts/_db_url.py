"""
DATABASE_URL helper — Prisma-style URL'i asyncpg-compatible hale getirir.

Prisma URL'i şu query params'ı içerebilir:
- ?schema=public (Prisma multi-schema)
- ?connection_limit=10 (Prisma connection pool)
- ?pgbouncer=true (Prisma PgBouncer support)
- ?statement_cache_size=0 (Prisma)

asyncpg bunları tanımıyor. Helper temizler.
"""
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


# asyncpg'nin DESTEKLEDIĞI query params (whitelist)
ASYNCPG_SUPPORTED_PARAMS = {
    "sslmode",
    "ssl",
    "host",
    "hostaddr",
    "port",
    "user",
    "password",
    "dbname",
    "passfile",
    "channel_binding",
    "connect_timeout",
    "client_encoding",
    "options",
    "application_name",
    "fallback_application_name",
    "keepalives",
    "keepalives_idle",
    "keepalives_interval",
    "keepalives_count",
    "tcp_user_timeout",
    "replication",
    "gssencmode",
    "sslcompression",
    "sslcert",
    "sslkey",
    "sslpassword",
    "sslrootcert",
    "sslcrl",
    "requirepeer",
    "krbsrvname",
    "gsslib",
    "service",
    "target_session_attrs",
}


def clean_db_url_for_asyncpg(url: str) -> str:
    """
    Prisma-style DATABASE_URL'i asyncpg-compatible hale getirir.
    Tanımayan query params (schema, pgbouncer, vs.) kaldırılır.

    Args:
        url: Prisma DATABASE_URL formatı

    Returns:
        asyncpg-compatible URL

    Example:
        >>> clean_db_url_for_asyncpg("postgresql://u:p@h/db?schema=public&sslmode=require")
        'postgresql://u:p@h/db?sslmode=require'
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    # Sadece asyncpg destekli params'ı koru
    cleaned_params = {
        k: v for k, v in params.items()
        if k.lower() in ASYNCPG_SUPPORTED_PARAMS
    }

    new_query = urlencode(cleaned_params, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


if __name__ == "__main__":
    # Test
    test_urls = [
        "postgresql://reeldeger:dev@localhost:5432/reeldeger_dev?schema=public",
        "postgresql://reeldeger:dev@localhost:5432/reeldeger_dev?schema=public&connection_limit=10&pgbouncer=true",
        "postgresql://reeldeger:dev@localhost:5432/reeldeger_dev?sslmode=require&schema=public",
        "postgresql://reeldeger:dev@localhost:5432/reeldeger_dev",
    ]
    for url in test_urls:
        print(f"IN:  {url}")
        print(f"OUT: {clean_db_url_for_asyncpg(url)}")
        print()
