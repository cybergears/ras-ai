import json

def load_profile(profile_path):
    with open(profile_path, "r") as f:
        return json.load(f)