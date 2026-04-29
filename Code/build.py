"""PyInstaller打包脚本。"""
import subprocess
import sys
import os

def build():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "build.spec",
        "--clean",
        "--noconfirm",
    ]
    subprocess.run(cmd, check=True)
    print("\n打包完成！输出目录: dist/")

if __name__ == "__main__":
    build()
