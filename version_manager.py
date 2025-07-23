import sys
import semver
import os
import importlib.util


def get_version_file():
    return os.path.join(os.path.dirname(__file__), "version.py")


def read_version():
    path = get_version_file()
    if os.path.exists(path):
        spec = importlib.util.spec_from_file_location("version", path)
        if spec is not None and spec.loader is not None:
            version_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(version_mod)
            return getattr(version_mod, "__version__", "0.0.0")
    return "0.0.0"


def write_version(version):
    path = get_version_file()
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"__version__ = '{version}'\n")


def bump_version(version, bump_type):
    v = semver.VersionInfo.parse(version)
    if bump_type == "patch" and "-" in version:
        return version.split("-")[0]
    bump_methods = {
        "major": v.bump_major,
        "minor": v.bump_minor,
        "patch": v.bump_patch,
        "prerelease": v.bump_prerelease,
    }
    method = bump_methods.get(bump_type)
    if method is None:
        # 默认 patch
        method = v.bump_patch
    return str(method())


def main():
    usage = "Usage: python version_manager.py [patch|minor|major|prerelease|set <version>|get]"
    args = sys.argv[1:]
    if not args:
        print(f"Current version: {read_version()}\n{usage}")
        return

    cmd = args[0].lower()
    if cmd in ("major", "minor", "patch", "release", "prerelease"):
        old_version = read_version()
        if cmd == "patch" and "-" in old_version:
            new_version = old_version.split("-")[0]
        elif cmd == "prerelease" and "-" not in old_version:
            new_version = bump_version(old_version, "patch")
            new_version = bump_version(new_version, cmd)
        else:
            print(111, old_version, cmd)
            new_version = bump_version(old_version, cmd)
        write_version(new_version)
        print(f"Version bumped: {old_version} -> {new_version}")
    elif cmd == "set" and len(args) == 2:
        new_version = args[1]
        try:
            semver.VersionInfo.parse(new_version)
            write_version(new_version)
            print(f"Version set to: {new_version}")
        except ValueError:
            print(f"Invalid semver: {new_version}")
    elif cmd == "get":
        print(read_version())
    else:
        print(f"Invalid command.\n{usage}")


if __name__ == "__main__":
    main()
