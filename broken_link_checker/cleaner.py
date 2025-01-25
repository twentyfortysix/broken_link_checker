import json

# filepath: /Volumes/data/WEBDESIGN/broken-links-checker/broken_link_checker/output.json
input_file = 'output.json'
output_file = 'filtered_output.json'

# Load JSON data
with open(input_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Filter out items where link_text contains '@'
filtered_data = [item for item in data if '@' not in item.get('link_text', '')]

# Save filtered data back to JSON file
with open(output_file, 'w', encoding='utf-8') as file:
    json.dump(filtered_data, file, indent=4, ensure_ascii=False)

print(f"Filtered data saved to {output_file}")