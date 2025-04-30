\
import subprocess
import time
import shlex
import datetime

def run_command(command, log_file):
    """Runs a command, returns its execution time, and logs details."""
    log_file.write(f"Running command: {command}\\n")
    print(f"Running command: {command}")
    start_time = time.time()
    try:
        # Use shlex.split to handle potential spaces in arguments correctly
        process = subprocess.run(shlex.split(command), check=True, capture_output=True, text=True)
        end_time = time.time()
        execution_time = end_time - start_time
        log_msg = f"Command finished successfully in {execution_time:.2f} seconds.\\n"
        log_file.write(log_msg)
        print(log_msg.strip())
        # log_file.write(f"Output:\\n{process.stdout}\\n") # Uncomment to log command output
        # log_file.write(f"Error:\\n{process.stderr}\\n") # Uncomment to log command error output
        return execution_time
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        execution_time = end_time - start_time
        log_msg = f"Command failed after {execution_time:.2f} seconds.\\n"
        log_file.write(log_msg)
        print(log_msg.strip())
        log_file.write(f"Error: {e}\\n")
        log_file.write(f"Output:\\n{e.stdout}\\n")
        log_file.write(f"Error output:\\n{e.stderr}\\n")
        print(f"Error: {e}")
        print("Output:\\n", e.stdout)
        print("Error output:\\n", e.stderr)
        return None
    except FileNotFoundError:
        log_msg = f"Error: Command not found - ensure python3 is in your PATH or provide the full path.\\n"
        log_file.write(log_msg)
        print(log_msg.strip())
        return None
    except Exception as e:
        end_time = time.time()
        execution_time = end_time - start_time
        log_msg = f"An unexpected error occurred after {execution_time:.2f} seconds: {e}\\n"
        log_file.write(log_msg)
        print(log_msg.strip())
        return None

def main():
    """Runs specific python scripts for a list of projects, times their execution, and logs results."""
    # project_names = [
    #     'adventure', 'book_shop', 'brush', 'cloud_solutions', 'cyberpulse',
    #     'energy', 'fraudlens', 'goal', 'hr', 'recipe', 'schedule', 'shop'
    # ]
    project_names = ['energy', 'schedule', 'cyberpulse', 'recipe']
    
    scripts_to_run = ['split_images.py', 'generate_code.py']
    log_file_path = "command_execution_log.txt"

    commands_to_run = []
    for project in project_names:
        for script in scripts_to_run:
            commands_to_run.append(f"python3 {script} {project}")

    total_time = 0
    successful_commands = 0
    failed_commands = 0

    start_run_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Starting run at {start_run_time}")
    print(f"Logging results to {log_file_path}")
    print(f"Running {len(commands_to_run)} commands for {len(project_names)} projects...")

    with open(log_file_path, 'w') as log_file:
        log_file.write(f"--- Script Run Started: {start_run_time} ---\\n")
        log_file.write(f"Running {len(commands_to_run)} commands for {len(project_names)} projects.\\n")
        log_file.write("-" * 30 + "\\n")

        for command in commands_to_run:
            execution_time = run_command(command, log_file)
            if execution_time is not None:
                total_time += execution_time
                successful_commands += 1
            else:
                failed_commands += 1
            log_file.write("-" * 30 + "\\n")
            print("-" * 30) # Separator

        summary_header = "\\n--- Summary ---"
        summary_total = f"Total commands executed: {len(commands_to_run)}"
        summary_success = f"Successful commands: {successful_commands}"
        summary_failed = f"Failed commands: {failed_commands}"
        summary_time = f"Total execution time for successful commands: {total_time:.2f} seconds"
        end_run_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_end = f"--- Script Run Finished: {end_run_time} ---"

        print(summary_header)
        print(summary_total)
        print(summary_success)
        print(summary_failed)
        print(summary_time)

        log_file.write(summary_header + "\\n")
        log_file.write(summary_total + "\\n")
        log_file.write(summary_success + "\\n")
        log_file.write(summary_failed + "\\n")
        log_file.write(summary_time + "\\n")
        log_file.write(summary_end + "\\n")

    print(f"\\nLog file saved to {log_file_path}")

if __name__ == "__main__":
    main()
