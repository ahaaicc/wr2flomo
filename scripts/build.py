import PyInstaller.__main__
import platform
import os
import shutil


def get_pyinstaller_args():
    """Returns a list of arguments for PyInstaller."""

    # Use os.pathsep for the --add-data separator, which is ':' on POSIX and ';' on Windows
    add_data_separator = os.pathsep

    base_args = [
        '--name', 'wr2flomo',
        '--windowed',
        '--noconfirm',
        '--add-data', f'resources{add_data_separator}resources',
        '--add-data', f'resources/styles/minimalist.qss{add_data_separator}resources/styles',
        '--hidden-import', 'PyQt6.QtCore',
        '--hidden-import', 'PyQt6.QtWidgets',
        '--hidden-import', 'PyQt6.QtGui',
    ]

    if platform.system() == 'Darwin':
        platform_args = [
            '--icon', 'resources/icons/app.icns',
            '--runtime-hook', 'scripts/macos_hook.py'
        ]
    elif platform.system() == 'Windows':
        platform_args = [
            '--icon', 'resources/icons/app.ico'
        ]
    else:
        # For other OS, maybe just don't add an icon
        print(f"Warning: Building on unsupported platform {platform.system()}. No icon will be set.")
        platform_args = []

    # Entry point script must be at the end
    entry_point = ['src/main.py']

    return base_args + platform_args + entry_point


def build():
    # It's better to run pyinstaller from the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(project_root)

    dist_path = os.path.join(project_root, 'dist')
    build_path = os.path.join(project_root, 'build')

    # Clean before build
    print("Cleaning previous builds...")
    if os.path.exists(dist_path):
        shutil.rmtree(dist_path)
    if os.path.exists(build_path):
        shutil.rmtree(build_path)

    pyinstaller_args = get_pyinstaller_args()

    print(f"Running PyInstaller with args: {' '.join(pyinstaller_args)}")

    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("Build successful.")
    except Exception as e:
        print(f"An error occurred during the build: {e}")
    finally:
        # Clean up build directory
        print("Cleaning up build directory...")
        if os.path.exists(build_path):
            shutil.rmtree(build_path)


if __name__ == '__main__':
    build()
