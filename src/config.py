DATABASE_CONFIG = {
    "connection_string": """
        DRIVER={ODBC Driver 17 for SQL Server};
        SERVER=45.32.92.85,8445;
        DATABASE=O2Jam;
        UID=sa;
        PWD=DPJAM2022Server!;
        TrustServerCertificate=yes;""",
    "trade_connection_string": """
        DRIVER={ODBC Driver 17 for SQL Server};
        SERVER=45.32.92.85,8445;
        DATABASE=O2JamTrade;
        UID=sa;
        PWD=DPJAM2022Server!;
        TrustServerCertificate=yes;""",
}

EMAIL_CONFIG = {"mail": "dmjam.noreply@gmail.com", "password": "yrzb uiym rbpd spaj"}

TURNSTILE_PRIVATE_KEY = "0x4AAAAAAAUifFOjD3TNzttuRmOr0NvAIpE"
TURNSTILE_ENDPOINT = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
