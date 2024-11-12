import os
from tkinter import filedialog, Tk

def log_message(message):
    print(f"[INFO] {message}")

def select_file_with_hint(title_hint, file_types):
    log_message(f"Prompting for file: {title_hint}")
    
    root = Tk()
    root.withdraw()
    root.lift()
    
    # Set initial directory to the parent of the current working directory
    initial_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    file_path = filedialog.askopenfilename(title=title_hint, filetypes=file_types, initialdir=initial_dir)
    root.destroy()
    
    log_message(f"Selected file: {file_path}")
    return file_path

def select_directory(title_hint):
    log_message(f"Prompting for directory: {title_hint}")
    
    root = Tk()
    root.withdraw()
    root.lift()
    
    # Set initial directory to the parent of the current working directory
    initial_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    directory_path = filedialog.askdirectory(title=title_hint, initialdir=initial_dir)
    root.destroy()
    
    log_message(f"Selected directory: {directory_path}")
    return directory_path

def select_project_files():
    log_message("Please select the .uproject file.")
    uproject_path = select_file_with_hint("Select ProjectStamina .uproject", [("Unreal Project Files", "*.uproject")])

    log_message("\nHint: UnrealEditor.exe is usually located in <Source Engine Directory>/Engine/Binaries/Win64")
    log_message("Please select the UnrealEditor.exe")
    engine_path = select_file_with_hint("Select UnrealEditor.exe (Hint: <Source Engine Directory>/Engine/Binaries/Win64)", [("Executable Files", "UnrealEditor.exe")])

    return uproject_path, engine_path

def select_server_build_directory():
    log_message("Please select the Linux server build directory (where the build for the server is located):")
    return select_directory("Select Linux Server Build Directory")

def select_output_directory():
    log_message("Please select the output directory (recommended to create a 'ServerTools_bin' folder):")
    return select_directory("Select Output Directory")

# Test the functions individually if running this script directly
if __name__ == "__main__":
    uproject_path, engine_path = select_project_files()
    server_build_dir = select_server_build_directory()
    output_dir = select_output_directory()
    log_message(f"Selected files: \nuproject: {uproject_path}\nengine: {engine_path}\nserver build: {server_build_dir}\noutput: {output_dir}")
