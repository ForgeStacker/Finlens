import os
import re
import subprocess
import argparse
import boto3

def get_profiles_from_config(config_path):
    """Parse AWS config file for profile names.

    Supports header formats: [profile name] and [default]. Returns a list of profile names.
    """
    profiles = []
    if not os.path.exists(config_path):
        return profiles
    with open(config_path, 'r') as f:
        current = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'\[(.+)\]', line)
            if m:
                header = m.group(1).strip()
                # Header can be 'profile name' or 'default'
                if header == 'default':
                    current = 'default'
                    profiles.append('default')
                elif header.startswith('profile '):
                    current = header.split(' ', 1)[1]
                    profiles.append(current)
                else:
                    # Some files may omit 'profile' prefix
                    current = header
                    profiles.append(current)
    return profiles


def get_profiles_from_boto3():
    try:
        sess = boto3.Session()
        return sess.available_profiles or []
    except Exception:
        return []

def profile_uses_sso(profile, config_path=os.path.expanduser('~/.aws/config')):
    # If profile has sso_start_url or sso_region in the config file, consider it SSO-enabled
    if not os.path.exists(config_path):
        return False
    current = None
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            m = re.match(r'\[(.+)\]', line)
            if m:
                header = m.group(1).strip()
                if header == 'default':
                    current = 'default'
                elif header.startswith('profile '):
                    current = header.split(' ', 1)[1]
                else:
                    current = header
                continue
            if current == profile:
                if line.startswith('sso_'):
                    return True
    return False


def sso_login_all(profiles=None, dry_run=False):
    """Perform `aws sso login` for all SSO-enabled profiles.

    If profiles is None, we will discover profiles via boto3 and ~/.aws/config.
    """
    if profiles is None:
        profiles = sorted(set(get_profiles_from_boto3() + get_profiles_from_config(os.path.expanduser('~/.aws/config'))))
    if not profiles:
        print("No AWS profiles found to attempt SSO login.")
        return

    for p in profiles:
        is_sso = profile_uses_sso(p)
        if not is_sso:
            print(f"Skipping profile '{p}' (not SSO-enabled).")
            continue
        print(f"Attempting SSO login for profile: {p}")
        cmd = ["aws", "sso", "login", "--profile", p]
        if dry_run:
            print("DRY RUN: would run:", ' '.join(cmd))
            continue
        try:
            ret = subprocess.run(cmd)
            if ret.returncode == 0:
                print(f"SSO login successful for profile: {p}")
            else:
                print(f"SSO login failed for profile: {p} (exit {ret.returncode})")
        except FileNotFoundError:
            print("aws CLI not found in PATH; cannot run SSO login. Install AWS CLI v2.")
            return

def main():
    parser = argparse.ArgumentParser(description='Perform AWS SSO login for all configured SSO profiles.')
    parser.add_argument('--profiles', '-p', nargs='+', help='Specific profiles to login to (space-separated)')
    parser.add_argument('--dry-run', action='store_true', help='Print commands but do not execute')
    args = parser.parse_args()
    sso_login_all(profiles=args.profiles, dry_run=args.dry_run)


if __name__ == "__main__":
    main()