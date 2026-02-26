"""Exit with a clear error if Python version is not supported by crewai."""
import sys

# CrewAI 0.130.x requires Python >=3.10, <3.14
MIN = (3, 10)
MAX = (3, 14)

def main():
    v = sys.version_info[:2]
    if v < MIN:
        print(f"This project requires Python {MIN[0]}.{MIN[1]} or newer. You have {sys.version.split()[0]}.", file=sys.stderr)
        sys.exit(1)
    if v >= MAX:
        print(
            f"CrewAI 0.130 requires Python >=3.10 and <3.14. You have {sys.version.split()[0]} (3.14+ is not yet supported).\n"
            "Please use a virtual environment with Python 3.10, 3.11, or 3.12:\n"
            "  - Install Python 3.12 from https://www.python.org/downloads/\n"
            "  - Then: py -3.12 -m venv .venv  &&  .venv\\Scripts\\activate  &&  pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"Python {sys.version.split()[0]} OK for crewai.")

if __name__ == "__main__":
    main()
