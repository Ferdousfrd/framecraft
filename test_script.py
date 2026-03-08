# test_script.py
from modules.script_generator import generate_script, print_script

topic = "Viking raid on Paris 845 AD"

print(f"Generating script for: {topic}")
print("Please wait...")

script = generate_script(topic)

# Debug - print raw output first
print("RAW OUTPUT:")
print(script)

# Then print nicely
print_script(script)