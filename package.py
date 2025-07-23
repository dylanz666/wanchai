import subprocess
import sys

from version_manager import read_version


def main():
    print("Starting build process...")
    bump_type = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("major", "minor", "patch", "pre"):
            bump_type = arg if arg != "pre" else "prerelease"
    # 读取当前版本
    version = read_version()
    if bump_type:
        # 调用 version_manager.py 递增版本
        result = subprocess.run(
            [sys.executable, "version_manager.py", bump_type],
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        version = read_version()
    exe_name = f"wanchai-editor_v{version}"
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        f"--name={exe_name}",
        "--icon=editor.ico",
        "wanchai-editor.py",
    ]
    print(" ".join(cmd))
    try:
        result = subprocess.run(cmd, check=True)
        print("Build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
