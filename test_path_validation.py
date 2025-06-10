import os

# Test the current path validation logic
test_path = r"C:\Users\Jonandrop\AppData\Local\Temp\tmplfj.pdf"
output_dir = os.path.dirname(test_path)

print(f"Test path: {test_path}")
print(f"Output dir: {output_dir}")

# Current validation logic
if os.name == 'nt':  # Windows
    invalid_chars = '<>:"|?*'
    print(f"Invalid chars: {invalid_chars}")
    
    for char in invalid_chars:
        if char in output_dir:
            print(f"Found invalid char '{char}' in path: {output_dir}")
            
    # Check each character
    for i, char in enumerate(output_dir):
        if char in invalid_chars:
            print(f"Invalid char '{char}' at position {i}")