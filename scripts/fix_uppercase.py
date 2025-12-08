import os
import re

def clean_text(text):
    # Match words with 2 or more uppercase letters
    # Example: CHAPTER -> Chapter, THE -> The
    def replace(match):
        return match.group(0).title()
    
    # \b matches word boundary
    # [A-Z]{2,} matches 2 or more uppercase letters
    # We avoid single letters like "I" or "A" (start of sentence) if they are just one letter,
    # though usually single 'A' is not ALL CAPS problem. "I" is fine.
    # If the text has "A BOOK", "A" is single. "BOOK" is matches.
    # If the text has "I AM", "I" is single. "AM" matches -> "Am".
    
    cleaned = re.sub(r'\b[A-Z]{2,}\b', replace, text)
    
    # Remove page numbers like [2], [15], etc.
    cleaned = re.sub(r'\[\d+\]', '', cleaned)
    
    return cleaned

def process_files(directory):
    if not os.path.exists(directory):
        print(f"Directory {directory} not found.")
        return

    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            print(f"Processing {filepath}...")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                cleaned_content = clean_text(content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                print(f"Finished {filepath}")
            except Exception as e:
                print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    # Assuming script is run from root or we point to 'txt' folder relative to root
    # The user provided files are in 'txt' folder in root
    process_files("txt")

