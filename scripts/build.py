import os
import sys
import subprocess
import shutil

def build():
    # Ensure we are in project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    sep = os.pathsep
    
    args = [
        "pyinstaller",
        "--noconfirm",
        "--windowed",
        "--name", "YTDownloader",
    ]
    
    # Ensure ffmpeg binaries are available locally
    os.makedirs("ffmpeg", exist_ok=True)
    for bin_name in ["ffmpeg", "ffprobe"]:
        bin_path = shutil.which(bin_name)
        if bin_path:
            dest = os.path.join("ffmpeg", os.path.basename(bin_path))
            if not os.path.exists(dest):
                shutil.copy2(bin_path, dest)
                print(f"Copied {bin_name} from {bin_path} to {dest}")
                
    # Add ffmpeg if it contains files
    if os.path.exists("ffmpeg") and os.listdir("ffmpeg"):
        args.append(f"--add-data=ffmpeg/*{sep}ffmpeg")
    else:
        print("Warning: ffmpeg folder not found or empty. Skipping FFmpeg bundling.")
        
    # Add assets if it exists
    if os.path.exists("assets"):
        args.append(f"--add-data=assets/*{sep}assets")
        
    args.append("main.py")
    
    print(f"Running command: {' '.join(args)}")
    subprocess.run(args, check=True)

if __name__ == "__main__":
    build()
