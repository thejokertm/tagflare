import os
import sys
import pandas as pd
import re
import oyaml as yaml
import json
from colorama import Fore, Back, Style
from yaml import dump
import openai
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Folder containing markdown files for each category
DIGITAL_GARDEN_FOLDER = 'PATH'
VISUAL_FICTION_FOLDER = 'PATH'

TAGS_FILE = "tags.json"

# Loading markdown files into a Pandas DataFrame
def load_markdown_files(directory, category_filter):
    if not os.path.isdir(directory):
        print(f"{Fore.RED}The directory {directory} does not exist. Please check the path.{Style.RESET_ALL}")
        sys.exit(1)

    md_files = [
        f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith(".md")
    ]

    data = []
    for md_file in md_files:
        with open(os.path.join(directory, md_file), "r") as file:
            content = file.read()

            yaml_header_match = re.search(r"---(.*?)---", content, re.DOTALL)
            if yaml_header_match:
                yaml_header = yaml_header_match.group(1)
                yaml_content = content.replace(f"---{yaml_header}---", "", 1)

                try:
                    yaml_data = yaml.safe_load(yaml_header)
                    if yaml_data.get('taxonomy', {}).get('category', [None])[0] == category_filter:
                        data.append({"filename": md_file, **yaml_data, "content": yaml_content})
                except yaml.scanner.ScannerError as e:
                    print(f"YAML Error in {md_file}: {e}")
            else:
                print(f"No YAML header found in {md_file}")

    return pd.DataFrame(data)

# Load all tags present in tags.json into a Pandas DataFrame
def load_tags_from_file(tags_file):
    # Check if tags.json file exists, if not, create an empty one
    if not os.path.exists(tags_file):
        with open(tags_file, 'w') as f:
            json.dump({'tags': []}, f)

    with open(tags_file, 'r') as f:
        tags = json.load(f)['tags']

    return pd.DataFrame(tags, columns=['tag'])

# Update markdown file with new tags
def update_tags(directory, uid, new_tags):
    print(f"Looking for uid: {uid}")
    md_files = [f for f in os.listdir(directory) if f.endswith('.md')]

    for md_file in md_files:
        filepath = os.path.join(directory, md_file)
        with open(filepath, 'r') as file:
            lines = file.readlines()

        uid_line = next((i for i, line in enumerate(lines) if f"uid: {uid}" in line), None)
        if uid_line is None:
            continue

        print(f"Found uid in {md_file}: {uid}")

        tag_line = next((i for i, line in enumerate(lines) if "post_tag:" in line), None)
        if tag_line is None:
            continue

        # Counting the base indentation level
        base_indent = len(lines[tag_line]) - len(lines[tag_line].lstrip())
        
        if base_indent == 0:
            indent_for_new_tags = 4
        else:
            indent_for_new_tags = base_indent + 4

        new_tag_lines = [indent_for_new_tags*" " + "- " + tag + "\n" for tag in new_tags]
        lines = lines[:tag_line+1] + new_tag_lines + lines[tag_line+1:]

        with open(filepath, 'w') as file:
            file.writelines(lines)

        print(f"Successfully updated tags for uid {uid} in {md_file}")
        return

    print(f"No matching uid {uid} found in files")

# Get tags using OpenAI API (GPT-3)
def get_tags_from_openai(content, title, all_tags, category, max_new_tags=3, max_total_tags=3, gpt_completion_count=15):
    
    with open("tags.json", 'r') as f:
        all_tags = json.load(f)['tags']

    openai.api_key = os.getenv("OPENAI_KEY")

    if category == "Visual Fiction":
        # Tell the model to only use tags from the list for 'Visual Fiction' category
        prompt = (
            f"I need you to identify the primary themes in the following 'Visual Fiction' text. "
            f"Your goal is to choose thematic keywords that capture the essence of this text. "
            f"These keywords should be from the existing tags list: {', '.join(all_tags)}. "
            f"Do not invent new keywords. You have to select suitable tags from the given list. Choose exactly 3!\n"
            f"\nHere's the text you should analyze, respond only with the themes themselves, not other words:\n\n"
            f"{content}\n"
        )
    elif category == "Digital Garden":
        # We can still allow the model to invent new tags for 'Digital Garden' category
        prompt = (
            f"I need you to identify the primary themes in the following text. "
            f"Your goal is to generate thematic keywords that capture the essence of this text. "
            f"These keywords should be meaningful, specific, and concise. "
            f"Each keyword you generate should reflect one distinct theme or topic in the text, and "
            f"should be limited to one to three words whenever possible. "
            f"For example, instead of 'Making You Believe', a more appropriate tag could be 'Belief'. "
            f"Your keywords should lean more towards the insightful representation of the content rather than being salesy, "
            f"marketing oriented or vague. Also, while you are free to invent new keywords, "
            f"try to use the existing tags from this list when appropriate: {', '.join(all_tags)}.\n"
            f"\nHere's the text you should analyze, respond only with the themes themselves, not other words:\n\n"
            f"{content}\n"
        )
    else:
        # You can define a generic prompt here for other categories or just skip them
        print(f"Unrecognized category {category} for the content with title {title}. Skipping.")
        return []

    # use chat models
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are to only ever return a list of keywords separated by comma. Nothing else"},
            {"role": "user", "content": prompt}
        ],
        max_tokens=gpt_completion_count,
        n=1,
        temperature=0,
    )

    # Get the response from the assistant
    assistant_message = response['choices'][0]['message']['content']

    suggested_tags_raw = [tag.strip().rstrip(',') for tag in assistant_message.split(", ")]

    # Capitalize the first letter of each tag
    suggested_tags_raw = [tag.title() for tag in suggested_tags_raw]

    existing_tags = [tag for tag in suggested_tags_raw if tag in all_tags]

    # Allow new tags for all categories since we're already guiding the GPT-3 model through the prompt
    new_tags = [tag for tag in suggested_tags_raw if tag not in existing_tags][:max_new_tags]

    # Extend all_tags with new_tags but don't write to the JSON file yet
    all_tags.extend(new_tags) 

    # Limit the overall number of tags giving priority to existing ones
    if len(existing_tags) < max_total_tags:
        new_tags = new_tags[:(max_total_tags - len(existing_tags))]  # Fill to max_total_tags with new tags
    else:
        existing_tags = existing_tags[:max_total_tags]  # If existing tags exceed max_total_tags, limit them
        new_tags = []  # No new tags if we already hit max_total_tags with existing ones

    total_tags = existing_tags + new_tags

    all_tags = list(set(all_tags))  # Keep only unique tags

    # Extension logic
    with open("tags.json", 'r') as f:
        existing_tags = json.load(f)['tags']

    # Extend existing_tags with new_tags
    all_tags.extend(existing_tags) 

    # Keep only unique tags
    all_tags = list(set(all_tags))  

    with open("tags.json", 'w') as f:
        json.dump({'tags': all_tags}, f)

    return total_tags

def process_files(df_markdown, df_tags, directory):
    print(f"{Fore.GREEN}Finding markdown files with empty taxonomy/post_tag...")
    if df_markdown.empty:
        print(f"{Fore.RED}No valid files found in {directory}")
        return
    empty_tags_files = df_markdown[df_markdown['taxonomy'].apply(lambda x: not x.get('post_tag', None) or len(x['post_tag']) == 0)]
    print(f"{Fore.GREEN}Found {Fore.YELLOW}{len(empty_tags_files)}{Fore.GREEN} markdown files with empty taxonomy/post_tag")

    for index, row in tqdm(empty_tags_files.iterrows(), total=empty_tags_files.shape[0]):
        uid = row.get('uid')
        filename = row.get('filename')
        print(f"{Fore.YELLOW}Working on file {Fore.CYAN}{filename}")

        content = row.get('content')
        title = row.get('title')
        category = row.get('taxonomy', {}).get('category', [None])[0]
        
        if not all([content, title, category]):
            print(f"{Fore.RED}Skipping file {Fore.CYAN}{filename}{Fore.RED} as it's missing the 'content', 'title', or 'category' key")
            continue

        suggested_tags = get_tags_from_openai(content, title, df_tags['tag'].tolist(), category)

        print(f"{Fore.BLUE}Tags generated using the OpenAI API: {Fore.CYAN}{', '.join(suggested_tags)}")
        
        if suggested_tags:
            print(f"{Fore.CYAN}Updating markdown file with new tags: {Fore.YELLOW}{', '.join(suggested_tags)}")
            update_tags(directory, uid, suggested_tags)
        else:
            print(f"{Fore.RED}No tags found for the file")

    df_tags = load_tags_from_file(TAGS_FILE)  # Update the DataFrame with updated tags

def main():
    print(f"{Fore.GREEN}Loading markdown files...")
    df_dg_markdown = load_markdown_files(DIGITAL_GARDEN_FOLDER, 'Digital Garden')
    df_vf_markdown = load_markdown_files(VISUAL_FICTION_FOLDER, 'Visual Fiction')
    df_tags = load_tags_from_file(TAGS_FILE)

    print(f"{Fore.GREEN}Processing Digital Garden files...")
    process_files(df_dg_markdown, df_tags, DIGITAL_GARDEN_FOLDER)

    print(f"{Fore.GREEN}Processing Visual Fiction files...")
    process_files(df_vf_markdown, df_tags, VISUAL_FICTION_FOLDER)

    print(f"{Fore.GREEN}Completed tagging markdown files.{Style.RESET_ALL}")

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}**********************************")
    print(f"🏷️ Welcome to TagFlare! 🔥")
    print(f"**********************************{Style.RESET_ALL}\n")
    main()