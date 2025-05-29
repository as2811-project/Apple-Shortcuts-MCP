## Claude + MacOS Shortcuts

This is a simple MCP server that leverages the MacOS Shortcuts functionality to perform specific tasks:

1. Hit Gemini Video Understanding API to extract ingredients from a recipe (this is why I began building this in the first place)
2. Add the extracted ingredients to a list in the Reminders app (this assumes you have a "Groceries" list in your Reminders app)
3. Summarise a chat conversation and add the summary to a new note.
4. Create a calendar event

All the above functionalities require the following Shortcuts to be setup on your Mac:

1. Add to Groceries list: https://www.icloud.com/shortcuts/6f696d784722468097df8ed238f8eaf2
2. Summarise and create note: https://www.icloud.com/shortcuts/bb0d13d3790c48e5b78eb26dbc7e3aca
3. Calendar: https://www.icloud.com/shortcuts/c01969b7e92343dfa3f38caad3a08f40

After adding the shorts mentioned above, follow these steps to setup the MCP server:

1. Clone the repo
2. Install uv (brew install uv)
3. cd into the directory of this repo, run `uv sync` followed by `uv pip install google-genai`
4. Copy the Claude Config JSON specified below with your Gemini API key and update your claude_desktop_config.json file
5. Open/Reopen Claude, you should be able to see the tools now.

Config:

```
{
  "mcpServers": {
    "Shortcuts-MCP": {
      "command": "uv",
      "args": [
        "--directory",
        "ABSOLUTE/PATH/TO/THIS/DIRECTORY",
        "run",
        "main.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key"
      }
    }
  }
}
```

#### Usage

1. Extract ingredients and create shopping list: Simply send the URL to a recipe on YouTube and ask Claude to add the ingredients to your list.
2. Calendar: Provide some context on what the event is about, and the start and end datetime values.

You can daisy chain the usage of these tools, for example: You can ask it to simply get the ingredients first, then separately ask it to create the list and add a calendar event.

#### Troubleshooting

Ensure you have Python, uv and other dependencies installed. On your Mac, create a "Groceries" list in your reminders app for the Shortcut itself to work properly.

#### Contributing

If you have other interesting Mac Shortcuts that can be triggered via Claude/MCP, feel free to add your tool here.
