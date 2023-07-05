# TagFlare 🏷️🔥

Welcome to **TagFlare** — a Python script that auto-generates tags for your markdown files using OpenAI's GPT-3 model. Specially designed to handle files in 'Digital Garden' and 'Visual Fiction' categories, TagFlare is your one-stop solution for intelligent and efficient tagging. Let's harness the power of AI! 🚀💡

## Overview 💡

TagFlare processes markdown files divided into two categories: 'Digital Garden' and 'Visual Fiction'. The script is set to work on 'Digital Garden' files first, where it generates new tags based on the content. Subsequently, 'Visual Fiction' files are addressed, with TagFlare assigning suitable tags from the existing list created earlier, rather than generating new ones.

## Features ✨

- **Efficient Data Handling**: All markdown files are loaded into a Pandas DataFrame, allowing for seamless data processing.
  
- **Two-stage Processing**: The script processes the 'Digital Garden' files first, allowing for new tag generation, and proceeds with 'Visual Fiction' files, leveraging already defined tags.
  
- **GPT-3 Integration**: Makes use of OpenAI's powerful GPT-3 model to generate or select relevant and insightful tags.

- **Dynamic Updates**: Any fresh tags created are added to the `tags.json` file, ensuring consistent updates.

- **User-friendly Console Output**: Utilizes the colorama library for colored terminal text output, easing user readability.

## Usage 🚀

1. Clone the repository.
   ```bash
   git clone https://github.com/yourusername/tagflare
   cd tagflare
   ```

2. Install necessary Python libraries.
   ```bash
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key in a `.env` file in the project root directory.
   ```text
   OPENAI_KEY=your_api_key
   ```

4. Adjust `DIGITAL_GARDEN_FOLDER`, `VISUAL_FICTION_FOLDER`, and `TAGS_FILE` paths as per your directory structure.

5. Run the script.
   ```bash
   python main.py
   ```

TagFlare is here to illuminate your content with perfectly fitted tags! Happy blogging! 🎉🥳

*As GPT-3 is powerful yet not perfect, a manual review of the generated tags is suggested to fine-tune your content tagging.*