from pathlib import Path

def get_project_base() -> Path:
    return Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    path = get_project_base()
    print(path)