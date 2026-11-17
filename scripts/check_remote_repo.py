import urllib.request
import json

def check_account_and_repo():
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Check user account
    user_url = "https://api.github.com/users/TirthRahulBora"
    try:
        req = urllib.request.Request(user_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            user_data = json.loads(response.read().decode())
            print(f"[GITHUB USER] Found user: {user_data.get('login')} (Name: {user_data.get('name')})")
    except Exception as e:
        print(f"[GITHUB USER ERROR] {e}")

    # Check repo
    repo_url = "https://api.github.com/repos/TirthRahulBora/examination-management-portal"
    try:
        req = urllib.request.Request(repo_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            repo_data = json.loads(response.read().decode())
            print(f"[GITHUB REPO] Found repo: {repo_data.get('full_name')} (Private: {repo_data.get('private')})")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[GITHUB REPO NOTICE] Repository 'examination-management-portal' does not exist yet under 'TirthRahulBora' (HTTP 404).")
        else:
            print(f"[GITHUB REPO HTTP {e.code}] {e}")
    except Exception as e:
        print(f"[GITHUB REPO ERROR] {e}")

if __name__ == '__main__':
    check_account_and_repo()
