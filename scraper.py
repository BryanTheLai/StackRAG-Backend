import os
import sys
from datetime import datetime

# --- Configuration ---
# HARDCODE the exact, full path to the directory you want to scan.
# Use a raw string (r"...") or double backslashes (\\) for Windows paths.
TARGET_DIRECTORY = r"C:\Users\wbrya\OneDrive\Documents\GitHub\AI-CFO-FYP"

# Set the name for the output file.
# It will be created in the directory where you run the script.
# Using .md extension because the output format is Markdown.
OUTPUT_FILENAME = "consolidated_code.md"

# Optional: List of directory names to completely skip during scanning
# Add any other folders within the TARGET_DIRECTORY you want to ignore.
DIRECTORIES_TO_SKIP = {'.venv','data','.git', '.vscode', '.idea', 'target', 'build', '__pycache__', 'node_modules', 'output_folder', 'experimental', 'notebooks','data'}

# Optional: List of specific file names (case-sensitive) to completely skip
# regardless of which directory they are in.
FILES_TO_SKIP = {'__init__.py', 'setup.py', '.env', 'scraper.py', '.env.example', 'README.md','consolidated_code.md'}
# --- End Configuration ---


def consolidate_to_markdown(root_dir, output_filepath, dirs_to_skip, files_to_skip):
    """
    Walks through the specified root directory and consolidates file contents
    into a single Markdown file using triple-backtick code blocks.

    Skips specified directories and specific files by name, and hidden files/folders.

    Args:
        root_dir (str): The absolute path to the directory to scan.
        output_filepath (str): The absolute path to the output Markdown file.
        dirs_to_skip (set): A set of directory names to skip.
        files_to_skip (set): A set of file names to skip.
    """
    abs_root_dir = os.path.abspath(root_dir)

    # --- Input Validation ---
    if not os.path.isdir(abs_root_dir):
        print(f"Error: Target directory not found at the specified path:")
        print(f"  '{abs_root_dir}'")
        print("\nPlease check the TARGET_DIRECTORY variable in the script.")
        return False # Indicate failure
    # --- End Input Validation ---

    print(f"Scanning directory: {abs_root_dir}")
    print(f"Output file:      {output_filepath}")
    print(f"Skipping dirs:    {', '.join(dirs_to_skip) if dirs_to_skip else 'None'}")
    print(f"Skipping files:   {', '.join(files_to_skip) if files_to_skip else 'None'}") # Added print for new list
    print("-" * 30)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            # Add the current date to the output file
            outfile.write(f"<Date> {datetime.now().strftime('%B %d, %Y %H:%M')}</Date>\n\n")
            file_count = 0
            # os.walk efficiently traverses the directory tree
            for dirpath, dirnames, filenames in os.walk(abs_root_dir, topdown=True):
                # Modify dirnames in-place to prevent os.walk from descending into skipped directories
                dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in dirs_to_skip]

                # Sort filenames for consistent order (optional, but nice)
                filenames.sort()

                for filename in filenames:
                    # Skip hidden files
                    if filename.startswith('.'):
                       continue
                    # --- Modification: Skip files in the exclusion list ---
                    if filename in files_to_skip:
                       print(f"  Skipping file: {filename}") # Optional: Add log for skipped files
                       continue
                    # --- End Modification ---


                    full_path = os.path.join(dirpath, filename)
                    # Calculate the relative path from the root directory being scanned
                    relative_path = os.path.relpath(full_path, abs_root_dir)
                    # Ensure consistent use of forward slashes for the Markdown path header
                    relative_path = relative_path.replace(os.sep, '/')

                    print(f"  Adding: {relative_path}")
                    file_count += 1

                    try:
                        # Read the content of the current file
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            content = infile.read()

                        # --- Write the formatted Markdown output ---
                        outfile.write(f"```{relative_path}\n") # Start code block with relative path
                        outfile.write(content)                # The actual file content
                        # Ensure there's a newline before the closing backticks if content exists
                        if content and not content.endswith('\n'):
                            outfile.write("\n")
                        outfile.write("```\n\n")               # End code block and add blank line for separation
                        # --- End Markdown output ---

                    except Exception as e:
                        print(f"    Error reading file {full_path}: {e}")
                        # Still write header, but note error inside code block
                        outfile.write(f"```{relative_path}\n")
                        outfile.write(f"*** Error reading file: {e} ***")
                        outfile.write("\n```\n\n")

            print("-" * 30)
            if file_count > 0:
                print(f"Consolidation complete. Added {file_count} files.")
                print(f"Output saved to '{output_filepath}'.")
            else:
                 print(f"Warning: No files found in '{abs_root_dir}' (excluding skipped dirs/files).")
            return True # Indicate success

    except IOError as e:
        print(f"Error: Could not write to output file {output_filepath}: {e}")
        return False # Indicate failure
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False # Indicate failure


# --- Main execution part ---
if __name__ == "__main__":
    print("Starting file consolidation script...")
    print("-" * 30)

    # Use the hardcoded target directory from configuration
    target_dir_path = TARGET_DIRECTORY

    # Determine where to save the output file (in the current working directory)
    try:
        # Get the current working directory from where the script is executed
        script_run_dir = os.getcwd()
    except Exception as e:
         print(f"Fatal Error: Could not get current working directory: {e}")
         print("Cannot determine where to save the output file.")
         sys.exit(1) # Exit if we can't figure out where to save the file

    # Construct the full path for the output file
    output_file_path = os.path.join(script_run_dir, OUTPUT_FILENAME)

    print(f"Target directory:   {target_dir_path}")
    print(f"Output file will be created at: {output_file_path}")

    # Run the consolidation function, passing the new exclusion list
    success = consolidate_to_markdown(target_dir_path, output_file_path, DIRECTORIES_TO_SKIP, FILES_TO_SKIP)

    print("-" * 30)
    if success:
        print("Script finished successfully.")
    else:
        print("Script finished with errors.")

    # Optional: Pause for visibility when run by double-clicking
    # input("\nPress Enter to exit...")