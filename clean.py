i = 0
import json

input_file = "unclean.txt"
output_file = "output.json"

users = []

with open(input_file, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]
    lines = lines[4:]

i = 0
while i < len(lines):
    user = lines[i]
    url = None

    if i + 1 < len(lines) and lines[i + 1].startswith("http"):
        url = lines[i + 1]
        i += 1

    users.append({"user": user, "url": url})
    i += 1

for idx, user in enumerate(users, start=1):
    user["id"] = idx

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(users, f, indent=2)

print(f"Cleaned data with IDs written to {output_file}")
