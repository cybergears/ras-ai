import argparse
from ras.config import load_profile
from ras.engine import RASEngine

def main():
    parser = argparse.ArgumentParser(description="R.A.S - Rider Assist System")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument("--profile", default="profiles/motorcycle.json")

    args = parser.parse_args()

    profile = load_profile(args.profile)
    engine = RASEngine(profile)
    engine.process(args.input, args.output)

if __name__ == "__main__":
    main()