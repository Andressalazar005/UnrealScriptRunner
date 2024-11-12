import sys
import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import queue
import requests
import json
import webbrowser
import shutil  

class ScriptRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Andres's Unreal Script Runner")
        self.root.geometry("700x600")
        self.root.configure(bg="#2b2b2b")

        # Log window setup
        self.log_text = scrolledtext.ScrolledText(self.root, bg="#3c3f41", fg="white", font=("Arial", 10), wrap=tk.WORD)
        self.log_text.pack(padx=10, pady=(10, 5), fill=tk.BOTH, expand=True)

        # Frame for buttons and dropdown
        control_frame = tk.Frame(self.root, bg="#2b2b2b")
        control_frame.pack(pady=(0, 10), fill=tk.X)
        
        self.log_text.tag_configure("green", foreground="green")
        
        # Define script configurations
        self.scripts_config = [
            {"name": "Generate Launch .bats", "script": "script_generator.py"},
            {"name": "Run Docker Setup", "script": "docker_setup.py"},
            {"name": "Setup Test Suite", "script": "setup_test_suite.py"},
            {"name": "Setup UE Source", "script": "setup_ue_source.py"},
            {"name": "Compile UE Proj", "script": "ue_compiler.py"},
            {"name": "Package Game", "script": "game_builder.py"},
            {"name": "Package Linux Server", "script": "linux_server_builder.py"},
            {"name": "Package Windows Server", "script": "windows_server_builder.py"}
        ]

        # Prepare dropdown options
        self.script_names = [config["name"] for config in self.scripts_config]
        self.script_choice = tk.StringVar()
        self.script_dropdown = ttk.Combobox(control_frame, textvariable=self.script_choice, state="readonly")
        self.script_dropdown['values'] = self.script_names
        self.script_dropdown.current(0)
        self.script_dropdown.grid(row=0, column=0, padx=10, pady=10)
        self.script_dropdown.bind("<<ComboboxSelected>>", self.load_script_inputs)

        # Run button
        self.run_button = tk.Button(control_frame, text="Run Script", command=self.run_selected_script, state=tk.NORMAL, bg="#646464", fg="white")
        self.run_button.grid(row=0, column=1, padx=5)

        # Cancel button
        self.cancel_button = tk.Button(control_frame, text="Cancel", command=self.cancel_subprocess, bg="#646464", fg="white")
        self.cancel_button.grid(row=0, column=2, padx=5)

        # Input Frame for dynamic inputs
        self.input_frame = tk.Frame(self.root, bg="#2b2b2b")
        self.input_frame.pack(pady=(10, 0), fill=tk.X)

        # Progress bar (initially hidden)
        self.progress_bar = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=3, padx=10)
        self.hide_progress_bar()

        # Track if a script is currently running
        self.script_running = False
        self.process = None

        # Input Storage
        self.script_inputs = []

        # Load inputs for the default selected script
        self.load_script_inputs()

    def show_progress_bar(self):
        self.progress_bar.grid()
        self.progress_bar.start()

    def hide_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()

    def get_script_path(self, script_name):
        """
        Determines the correct path to the script based on whether the application is frozen.
        """
        if getattr(sys, 'frozen', False):
            # If the application is frozen, scripts are bundled inside the executable's directory
            application_path = os.path.dirname(sys.executable)
        else:
            # If not frozen, scripts are in the same directory as this script
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        script_path = os.path.join(application_path, script_name)
        return script_path

    def load_script_inputs(self, event=None):
        selected_name = self.script_choice.get()
        selected_config = next((config for config in self.scripts_config if config["name"] == selected_name), None)

        if selected_config:
            # Clear existing inputs
            for widget in self.input_frame.winfo_children():
                widget.destroy()

            # Load input requirements from the script
            inputs = self.get_script_inputs(selected_config["script"])
            self.script_inputs = []

            # Log the selection hint for the selected script
            self.print_selection_hint(selected_config["script"])

            for i, input_info in enumerate(inputs):
                if input_info["type"] == "dropdown" and input_info.get("dynamic_fetch"):
                    options = self.fetch_dynamic_data(input_info)
                else:
                    options = []

                self.create_input_field(i, input_info, options)

    def print_selection_hint(self, script_name):
        """
        Imports the selected script and logs the selection hint if available.
        """
        try:
            # Dynamically load the script module
            script_module = __import__(script_name.replace(".py", ""))
            # Get the hint function and call it
            hint = script_module.selection_hint()
            self.log_message(hint)  # Log the hint in the log text box
        except AttributeError:
            self.log_message(f"No hint available for {script_name}.")
        except ImportError as e:
            self.log_message(f"Error importing script module: {e}")


    def create_input_field(self, index, input_info, options):
        label = tk.Label(self.input_frame, text=input_info["label"], bg="#2b2b2b", fg="white")
        label.grid(row=index, column=0, padx=5, pady=5)

        if input_info["type"] == "dropdown":
            input_var = tk.StringVar()
            dropdown = ttk.Combobox(self.input_frame, textvariable=input_var, state="readonly")
            dropdown['values'] = options
            dropdown.set(input_info.get("default", ""))
            dropdown.grid(row=index, column=1, padx=5, pady=5)
            self.script_inputs.append(input_var)
        elif input_info["type"] == "button":
            # Create a Button field
            button = tk.Button(self.input_frame, text=input_info["label"], command=lambda: self.call_script_function(input_info["function"]), bg="#646464", fg="white")
            button.grid(row=index, column=1, padx=5, pady=5)
        else:  # Text Input
            input_entry = tk.Entry(self.input_frame, bg="#3c3f41", fg="white")
            input_entry.insert(0, input_info.get("default", ""))
            input_entry.grid(row=index, column=1, padx=5, pady=5)
            self.script_inputs.append(input_entry)
            
    def call_script_function(self, function_name):
        # Identify which script is currently selected
        selected_name = self.script_choice.get()
        selected_config = next((config for config in self.scripts_config if config["name"] == selected_name), None)

        if not selected_config:
            self.log_message("No script selected or found.")
            return

        try:
            # Dynamically load the script module
            script_module = __import__(selected_config["script"].replace(".py", ""))
            # Get the function by name from the loaded module
            function = getattr(script_module, function_name)
            # Call the function
            function()
        except AttributeError as e:
            self.log_message(f"Error: Function {function_name} does not exist. {e}")
        except ImportError as e:
            self.log_message(f"Error importing script module: {e}")

               
    def open_github_page(self):
        github_url = "https://github.com/EpicGames/UnrealEngine/tags"
        self.log_message(f"Opening GitHub page: {github_url}")
        webbrowser.open(github_url)
        
    def fetch_dynamic_data(self, input_info):
        if input_info["fetch_from"] == "github_tags":
            repo_url = input_info.get("repo_url")
            return self.fetch_github_tags(repo_url)
        return []

    def fetch_github_tags(self, repo_url):
        try:
            self.log_message(f"Fetching tags from Git repository: {repo_url}")

            # Run 'git ls-remote --tags <repo_url>'
            result = subprocess.run(
                ['git', 'ls-remote', '--tags', repo_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                self.log_message(f"Error fetching tags: {result.stderr.strip()}")
                return []

            # Parse the output to extract tag names
            lines = result.stdout.strip().split('\n')
            tags = []
            for line in lines:
                parts = line.split()
                if len(parts) == 2:
                    ref = parts[1]
                    if ref.startswith('refs/tags/'):
                        tag = ref[len('refs/tags/'):]
                        # Remove any '^{}' suffix
                        if tag.endswith('^{}'):
                            tag = tag[:-3]
                        tags.append(tag)

            # Remove duplicates and sort the tags
            tags = sorted(set(tags))
            self.log_message(f"Fetched {len(tags)} tags.")
            return tags
        except Exception as e:
            self.log_message(f"Error fetching Git tags: {e}")
            return []


    def get_script_inputs(self, script_name):
        try:
            script_module = __import__(script_name.replace(".py", ""))
            return script_module.get_script_inputs().get("inputs", [])
        except Exception as e:
            self.log_message(f"Error loading script inputs: {e}")
            return []

    def run_selected_script(self):
        if self.script_running:
            self.log_message("A script is already running. Please wait.")
            return

        selected_name = self.script_choice.get()
        selected_config = next((config for config in self.scripts_config if config["name"] == selected_name), None)

        if selected_config:
            # Collect inputs
            inputs = []
            for var in self.script_inputs:
                if isinstance(var, tk.StringVar):
                    value = var.get()
                elif isinstance(var, tk.Entry):
                    value = var.get()
                else:
                    value = var.get()
                inputs.append(value.strip())

            # Remove empty strings to avoid passing unwanted inputs
            inputs = [inp for inp in inputs if inp]

            self.log_message(f"Running script: {selected_config['script']} with inputs: {inputs}")

            # Pass input data as JSON array
            input_data = json.dumps(inputs)

            # Run the script
            self.run_script(selected_config["script"], input_data=input_data)

    def run_script(self, script_name, input_data=None):
        self.log_text.delete(1.0, tk.END)
        self.show_progress_bar()
        self.script_running = True
        self.output_queue = queue.Queue()

        def enqueue_output(out, queue):
            for line in iter(out.readline, ''):
                queue.put(line)
            out.close()

        def run():
            try:
                script_path = self.get_script_path(script_name)
                self.log_message(f"Executing {script_path} with interpreter: {self.get_python_executable()}")
                self.process = subprocess.Popen(
                    [self.get_python_executable(), script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    universal_newlines=True,
                    bufsize=1  # Line-buffered
                )

                if input_data:
                    self.process.stdin.write(input_data + "\n")
                    self.process.stdin.flush()
                    self.process.stdin.close()  # Close stdin
                    self.log_message(f"Input data sent: {input_data}")

                # Start threads to read stdout and stderr
                threading.Thread(target=enqueue_output, args=(self.process.stdout, self.output_queue), daemon=True).start()
                threading.Thread(target=enqueue_output, args=(self.process.stderr, self.output_queue), daemon=True).start()

                # Wait for the process to finish
                self.process.wait()

                if self.process.returncode == 0:
                    self.log_message("Script completed successfully.")
                else:
                    self.log_message(f"Script exited with error code: {self.process.returncode}")

            except Exception as e:
                self.log_message(f"Error running script: {e}")
            finally:
                self.hide_progress_bar()
                self.script_running = False

        def process_output_queue():
            try:
                while True:
                    line = self.output_queue.get_nowait()
                    self.log_message(line.strip())
            except queue.Empty:
                pass
            if self.script_running:
                self.root.after(100, process_output_queue)

        # Start the run function in a new thread
        threading.Thread(target=run).start()
        # Start checking the output queue
        self.root.after(100, process_output_queue)

    def get_python_executable(self):
        """
        Determines the correct Python executable to use based on whether the application is frozen.
        """
        if getattr(sys, 'frozen', False):
            # If the application is frozen, assume 'python' is available in PATH
            python_exec = "python"  # Alternatively, provide full path if needed
        else:
            # If not frozen, use the current Python interpreter
            python_exec = sys.executable
        return python_exec

    def cancel_subprocess(self):
        if self.script_running and self.process:
            self.process.terminate()
            self.process.wait()
            self.log_message("Script cancelled.")
            self.script_running = False

    def quit_application(self):
        self.cancel_subprocess()
        self.root.quit()
        self.root.destroy()

    def log_message(self, message, color=None):
        # Use the specified color or default to no color
        if color:
            self.log_text.insert(tk.END, f"{message}\n", color)
        else:
            self.log_text.insert(tk.END, f"{message}\n")
        
        self.log_text.yview(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptRunnerApp(root)
    app.log_message("[Info]: Script_Runner State::Active, choose a script to run.", color="green")
    root.mainloop()
