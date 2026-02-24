import json
import os
import sys


def load_profile(profile_path):

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    full_path = os.path.join(base_path, profile_path)

    with open(full_path, "r") as f:
        return json.load(f)