import os
import msal

SCOPES = [
    "User.Read",
    "Mail.ReadWrite",
]

AUTHORITY = (
    "https://login.microsoftonline.com/"
    + os.getenv("MICROSOFT_TENANT_ID", "common")
)

CACHE_FILE = "msal_token_cache.json"


def _load_cache():
    cache = msal.SerializableTokenCache()

    if os.path.exists(CACHE_FILE):
        try:
            cache.deserialize(
                open(CACHE_FILE, "r", encoding="utf-8").read()
            )
        except OSError:
            pass

    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(cache.serialize())


def get_access_token():
    client_id = os.environ["MICROSOFT_CLIENT_ID"]
    cache = _load_cache()

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=AUTHORITY,
        token_cache=cache,
    )

    accounts = app.get_accounts()

    if accounts:
        result = app.acquire_token_silent(
            SCOPES,
            account=accounts[0],
        )
        if result and "access_token" in result:
            _save_cache(cache)
            return result["access_token"]

    print("\nMicrosoft sign-in required.")
    print("A browser window may open, or MSAL may provide a device code.")
    print()

    flow = app.initiate_device_flow(scopes=SCOPES)

    if "user_code" not in flow:
        raise RuntimeError(
            "Could not start Microsoft device authentication: "
            + str(flow)
        )

    print(flow["message"])

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(
            "Microsoft authentication failed: "
            + result.get("error_description", str(result))
        )

    _save_cache(cache)
    return result["access_token"]
