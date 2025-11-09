import sys
import os

if getattr(sys, 'frozen', False):
    # This is the correct way to get the path to the app's resource directory
    # when running as a bundled app.
    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    
    # Change the current working directory to the bundle's resource directory
    os.chdir(bundle_dir)

def setup_macos():
    if getattr(sys, 'frozen', False):
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
        os.environ['QT_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt', 'plugins')

setup_macos()  # 确保函数被调用 