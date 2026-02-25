
import re
import os

file_path = 'app.py'

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Define the main block regex
# We look for if __name__ == ... and the indented block.
# This is hard to do perfectly with regex, but we can look for the specific lines we saw.
# We saw: 
#    print("="*50 + "\n")
#    app.run(debug=True, host='0.0.0.0', port=5000)

main_block_pattern = r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:(?:.|\n)*?app\.run\(.*?\)'

# Find all occurrences
matches = list(re.finditer(main_block_pattern, content, re.DOTALL))

if not matches:
    # If regex fails (maybe usage of single/double quotes, or spacing), try a simpler search for app.run
    # and try to extract the block around it.
    print("Main block regex didn't match. Falling back to identifying app.run line.")
    # We know app.run is there. Let's just find the if __name__ line and everything until app.run(...)
    # But wait, python indentation matters. 
    
    # Let's try to just cut the file at 'if __name__ == "__main__":'
    if 'if __name__ == "__main__":' in content:
        parts = content.split('if __name__ == "__main__":')
        # This is risky if it appears multiple times or in strings.
        
        # Safe strategy:
        # 1. Read lines.
        # 2. Identify the line range of the main block.
        # 3. Move it to the end.
        pass

# Let's use a line-based approach for robustness
lines = content.splitlines()
main_start_idx = -1
app_run_idx = -1

for i, line in enumerate(lines):
    if line.strip().startswith('if __name__') and '__main__' in line:
        main_start_idx = i
    if 'app.run(' in line:
        app_run_idx = i

if main_start_idx != -1 and app_run_idx != -1 and app_run_idx > main_start_idx:
    # We found a block.
    # Check if this block is before the end of the file.
    if app_run_idx < len(lines) - 5: # If there are more than 5 lines after app.run, assume it's misplaced.
        print(f"Found misplaced main block at lines {main_start_idx}-{app_run_idx}")
        
        # Extract the block
        # We assume the block ends at app_run_idx (inclusive) or slightly after? 
        # Usually app.run is the last thing.
        # But wait, looking at the previous output, it was followed by comments.
        
        # Let's extract lines main_start_idx to app_run_idx
        main_block_lines = lines[main_start_idx : app_run_idx + 1]
        
        # Remove these lines from original position
        # Be careful about indices shifting if we delete.
        # Easier to reconstruct.
        
        new_lines = lines[:main_start_idx] + lines[app_run_idx + 1:]
        
        # Append the block at the end
        new_lines.extend(['', ''] + main_block_lines)
        
        # Join and write
        new_content = '\n'.join(new_lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Moved main block to the end.")
        
    else:
        print("Main block seems to be at the end already (or close enough).")
        # Check if bakim routes are BEFORE it.
        # If Bakim routes are appended, they might be AFTER lines length?
        # No, lines list includes everything.
        pass

else:
    print(f"Could not locate main block cleanly. Start: {main_start_idx}, Run: {app_run_idx}")
    # If app.run exists but not in main block?
    if app_run_idx != -1:
         # Just app.run is called?
         pass
