from __future__ import annotations

import argparse
import os

from config import OUTPUT_BASE_DIR
from runner import run_for_profile

# config/ directory sits one level above backend/
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")


def _read_profiles_yaml() -> list[str]:
    """Return enabled profile names from config/profiles.yaml."""
    path = os.path.join(_CONFIG_DIR, "profiles.yaml")
    try:
        import yaml  # type: ignore
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        return [
            entry["name"]
            for entry in (data.get("profiles") or [])
            if entry.get("name") and entry.get("enabled", True)
        ]
    except Exception as exc:
        print(f"[WARN] Could not parse profiles.yaml: {exc}")
        return []


def main() -> None:
    parser = argparse.ArgumentParser(description='Collect inventory across AWS profiles')
    parser.add_argument('--sso-login', action='store_true', help='Perform AWS SSO login for all configured SSO profiles before collecting')
    parser.add_argument(
        '--profiles',
        nargs='+',
        metavar='PROFILE',
        help='Override profiles to run (space-separated). Defaults to enabled entries in config/profiles.yaml.',
    )
    args = parser.parse_args()

    try:
        import sso_login  # type: ignore
    except Exception:
        sso_login = None

    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

    if getattr(args, 'sso_login', False) and sso_login:
        print('Attempting SSO login for SSO-enabled profiles...')
        try:
            sso_login.sso_login_all()
        except Exception as exc:
            print(f"SSO login step failed: {exc}")

    # Determine profiles to run
    if getattr(args, 'profiles', None):
        profiles: list[str] = [p.strip() for p in args.profiles if p and p.strip()]
    else:
        profiles = _read_profiles_yaml()
        if not profiles:
            print('No enabled profiles found in config/profiles.yaml. Exiting.')
            return

    print(f"Profiles to process: {profiles}")
    for profile in profiles:
        run_for_profile(profile)

    print(f"\nAll profiles processed. Output written to: {OUTPUT_BASE_DIR}")


if __name__ == '__main__':
    main()
