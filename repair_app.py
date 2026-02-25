
import os

file_path = 'app.py'

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Fix corrupted strings
replacements = {
    "flash('S &  Bakım kaydı bax arıyla eklendi.', 'success')": "flash('✅ Bakım kaydı başarıyla eklendi.', 'success')",
    "flash(f'R  Hata: {result[\"message\"]}', 'error')": "flash(f'❌ Hata: {result[\"message\"]}', 'error')",
    "flash('S &  Kayıt silindi.', 'success')": "flash('✅ Kayıt silindi.', 'success')",
    # Catching variations if the replacement char is different or absent in regex
}

# Allow for fuzzy matching if exact string fails due to waiting bytes
# We will use direct replacement of the specific known bad patterns if found
# Or we can just rewrite the functions entirely if we can identify them.

# Let's try to reconstruct the file by identifying the functions.
# Actually, the file content in memory is what matters.

# Let's just find the bad lines by partial match and replace the whole line.
lines = content.split('\n')
new_lines = []
for line in lines:
    if "Bakım kaydı ba" in line and "eklendi" in line and "flash" in line:
        new_lines.append("        flash('✅ Bakım kaydı başarıyla eklendi.', 'success')")
    elif "Kayıt silindi" in line and "flash" in line and "success" in line and "S &" in line:
        new_lines.append("        flash('✅ Kayıt silindi.', 'success')")
    elif "Hata:" in line and "result[\"message\"]" in line and "flash" in line and "R" in line:
        new_lines.append("        flash(f'❌ Hata: {result[\"message\"]}', 'error')")
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# Check if main block exists
if "if __name__ == '__main__':" not in content:
    content += "\n\nif __name__ == '__main__':\n    app.run(debug=True, port=5000)\n"

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Repair complete.")
