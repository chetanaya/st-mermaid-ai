# 🎨 AI-Powered Mermaid Diagram Generator

Transform your ideas into beautiful diagrams using AI-powered analysis and generation! This Streamlit application uses LangChain and LangGraph to intelligently analyze user input and generate appropriate Mermaid diagrams.

## ✨ Features

- **AI-Powered Analysis**: Automatically analyzes your text to understand intent and suggest diagram types
- **Multiple Diagram Types**: Supports 10+ Mermaid diagram types including flowcharts, sequence diagrams, Gantt charts, and more
- **Interactive Workflow**: Uses LangGraph for a multi-step AI agent workflow with specialized code generators
- **Syntax Validation**: Utilizes MermaidSyntax class for validation and diagram-specific templates
- **Smart Recommendations**: Provides suggestions for related diagrams and improvements
- **Download Options**: Export diagrams as Mermaid code or HTML files
- **Conversation History**: Keeps track of your diagram generation sessions

## 🔧 Supported Diagram Types

- 📊 Flowcharts
- 🔄 Sequence Diagrams  
- 📅 Gantt Charts
- 🏗️ Class Diagrams
- ⚡ State Diagrams
- 🗄️ ER Diagrams
- 🚶 User Journeys
- 🥧 Pie Charts
- 🌳 Git Graphs
- 🧠 Mind Maps

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/chetanaya/st-mermaid-ai.git
   cd st-mermaid-ai
   ```

2. **Set up your OpenAI API key**
   
   Option A: Environment variable
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Option B: Create a `.env` file in the project root
   ```
   OPENAI_API_KEY="your-api-key-here"
   ```
   
   Option C: Streamlit secrets (create `.streamlit/secrets.toml`)
   ```toml
   OPENAI_API_KEY = "your-api-key-here"
   ```

3. **Run the startup script**
   ```bash
   ./start.sh
   ```
   
   The script will:
   - Create a virtual environment if one doesn't exist
   - Install required dependencies
   - Activate the environment and start the Streamlit app
   
   Or manually set up and run:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py
   ```

4. **Open your browser** to `http://localhost:8501`

## 📝 How to Use

1. **Describe what you want to visualize** in the text area
2. **Click "Analyze & Generate Suggestions"** to let the AI analyze your input
3. **Review the suggested diagram types** and their use cases
4. **Select a diagram type** to generate the actual Mermaid code
5. **View, download, or get recommendations** for additional diagrams

## 💡 Example Inputs

- "I want to show the user registration process with validation and database operations"
- "Create a project timeline for developing a mobile app over 6 months"
- "Show the class structure for an e-commerce system with products, users, and orders"
- "Visualize the states of an order from creation to delivery"
- "Display the customer journey for an online shopping experience"

## 🛠️ Technical Architecture

- **Frontend**: Streamlit for the web interface
- **AI Framework**: LangChain for LLM interactions
- **Workflow Engine**: LangGraph for multi-step agent workflows and state management
- **LLM**: OpenAI GPT-4o-mini for intelligent analysis and diagram generation
- **Diagram Rendering**: Mermaid.js v11.6.0 for client-side rendering
- **Diagram Validation**: MermaidSyntax class for validation and template management

## 📁 Project Structure

```
st-mermaid-ai/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── start.sh               # Startup script for environment setup
├── app.log                # Application logs
├── src/                   # Source code modules
│   ├── agents.py          # LangGraph agent workflow definitions
│   ├── diagram_generators.py # Specialized diagram type generators
│   ├── mermaid_syntax.py  # Mermaid syntax validation and templates
│   └── utils.py           # Utility functions for the application
├── .streamlit/
│   └── config.toml        # Streamlit configuration (if available)
└── README.md              # This file
```

## 🔧 Configuration

### Streamlit Settings

The app includes optimized Streamlit configuration in `.streamlit/config.toml`:
- Custom theme colors
- Disabled usage stats collection
- Optimized for development

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

## 🐛 Troubleshooting

### Common Issues

1. **"Please set your OpenAI API key"**
   - Make sure you've set the `OPENAI_API_KEY` environment variable or added it to Streamlit secrets

2. **Import errors during startup**
   - Run `pip install -r requirements.txt` to install all dependencies

3. **Diagram not rendering properly**
   - Check the Mermaid code syntax in the "View Mermaid Code" section
   - Try refreshing the page

4. **AI agent errors**
   - The app includes fallback mechanisms for robustness
   - Check your internet connection and API key validity

### Getting Help

- Check the Streamlit logs in the terminal for detailed error messages
- Ensure you have the latest versions of all dependencies
- Verify your OpenAI API key has sufficient credits

## 🎯 Development

### Adding New Diagram Types

1. Add the new type to the `DiagramType` enum
2. Add a corresponding prompt template in `generate_mermaid_diagram`
3. Update the sidebar list in the main application

### Customizing the AI Workflow

The LangGraph workflow is defined in the `create_agent_workflow()` function. You can:
- Add new nodes for additional processing steps
- Modify the existing prompts for different behavior
- Add conditional routing between nodes

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Built with ❤️ using Streamlit, LangChain, and LangGraph**
