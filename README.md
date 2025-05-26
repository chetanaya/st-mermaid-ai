# 🎨 AI-Powered Mermaid Diagram Generator

Transform your ideas into beautiful diagrams using AI-powered analysis and generation! This sophisticated Streamlit application uses LangChain and LangGraph to intelligently analyze user input and generate appropriate Mermaid diagrams with advanced features for editing, validation, and enhancement.

## ✨ Key Features

### 🤖 Advanced AI Capabilities
- **Multi-Agent Workflow**: 4-node LangGraph workflow (intent analysis → diagram suggestions → generation → recommendations)
- **Deep Intent Analysis**: Analyzes domain, complexity, entities, relationships, and temporal aspects
- **Dynamic Inspiration**: AI generates contextual diagram ideas on startup to guide users
- **Intelligent Error Correction**: AI-powered syntax error detection and automatic fixing
- **Smart Recommendations**: Context-aware suggestions for follow-up diagrams

### 🎨 Enhanced User Experience
- **Real-Time Live Editor**: Edit Mermaid code with instant preview and syntax validation
- **Interactive Diagram Ideas**: Click-to-try inspirational examples across various domains
- **Conversation History**: Persistent session tracking with ability to recreate previous diagrams
- **Progressive Workflow**: Guided step-by-step process from analysis to final diagram
- **Enhanced Error Handling**: Graceful error recovery with fallback mechanisms

### 🔧 Specialized Diagram Generators
- **10 Optimized Generators**: Each diagram type has specialized prompts and validation
- **Advanced Syntax Support**: Comprehensive templates and validation rules
- **Context-Aware Generation**: Tailored output based on user domain and complexity requirements
- **Fallback Systems**: Robust diagram generation even when primary methods fail

### 📥 Advanced Export & Editing
- **Multiple Download Formats**: Mermaid code (.mmd), HTML files, and more
- **Live Code Editing**: Real-time syntax checking with auto-fix suggestions
- **Version Control**: Track changes and revert to previous versions
- **Copy & Share**: Easy sharing of diagram codes and rendered outputs

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

### 🚀 Getting Started

1. **Browse Inspiration** - View AI-generated diagram ideas on the homepage for quick starts
2. **Describe Your Vision** - Enter a detailed description of what you want to visualize
3. **AI Analysis** - Click "Analyze & Generate Suggestions" for intelligent intent analysis
4. **Choose Your Diagram** - Review AI-suggested diagram types with explanations and use cases
5. **Generate & Edit** - Create your diagram with real-time editing capabilities
6. **Download & Share** - Export in multiple formats or continue with recommended diagrams

### 🎯 Advanced Features

- **Live Editor**: Edit generated Mermaid code with instant preview and syntax validation
- **AI Auto-Fix**: Let AI automatically correct syntax errors in your diagrams
- **Conversation History**: Access and recreate previous diagrams from the sidebar
- **Smart Recommendations**: Get suggestions for related diagrams after generation
- **Fallback Recovery**: Robust error handling ensures you always get a usable diagram

## 💡 Example Inputs

- "I want to show the user registration process with validation and database operations"
- "Create a project timeline for developing a mobile app over 6 months"
- "Show the class structure for an e-commerce system with products, users, and orders"
- "Visualize the states of an order from creation to delivery"
- "Display the customer journey for an online shopping experience"

## 🛠️ Technical Architecture

### 🏗️ Core Components

- **Frontend**: Streamlit with custom CSS styling and enhanced UI components
- **AI Framework**: LangChain for LLM interactions with advanced prompt engineering
- **Workflow Engine**: LangGraph for sophisticated multi-agent workflows and state management
- **LLM**: OpenAI GPT-4o-mini for intelligent analysis, generation, and error correction
- **Diagram Rendering**: Streamlit-Mermaid integration with Mermaid.js v11.6.0
- **Validation System**: MermaidSyntax class with comprehensive templates and error handling

### 🔄 AI Workflow Pipeline

1. **Intent Analysis Node**: Deep analysis of user input (domain, complexity, entities, relationships)
2. **Suggestion Node**: Context-aware diagram type recommendations with use cases
3. **Generation Node**: Specialized diagram generators with optimized prompts
4. **Recommendation Node**: Smart suggestions for follow-up diagrams and improvements

### 🧠 Advanced Features

- **Multi-Generator Architecture**: 10 specialized generators with diagram-specific optimizations
- **Real-Time Validation**: Live syntax checking with auto-fix capabilities
- **Session Management**: Persistent conversation history and state tracking
- **Error Recovery**: Comprehensive fallback mechanisms and graceful error handling
- **Dynamic Content**: AI-generated inspiration ideas and contextual recommendations

## 📁 Project Structure

```text
st-mermaid-ai/
├── app.py                 # Main Streamlit application with enhanced UI
├── requirements.txt       # Python dependencies (streamlit, langchain, langgraph, etc.)
├── start.sh              # Automated startup script with environment setup
├── logs/
│   └── app.log           # Comprehensive application logging
├── src/                  # Modular source code architecture
│   ├── agents.py         # LangGraph multi-agent workflow and state management
│   ├── diagram_generators.py # 10 specialized diagram generators with optimized prompts
│   ├── mermaid_syntax.py # Advanced syntax validation, templates, and error correction
│   └── utils.py          # Enhanced utilities (rendering, editing, history, downloads)
├── .streamlit/
│   └── config.toml       # Optimized Streamlit configuration and custom theming
└── README.md             # Comprehensive documentation
```

### 🔧 Module Breakdown

- **`agents.py`**: 4-node LangGraph workflow with intent analysis, suggestions, generation, and recommendations
- **`diagram_generators.py`**: Specialized generators for each diagram type with context-aware prompts
- **`mermaid_syntax.py`**: Comprehensive syntax templates, validation rules, and auto-fix capabilities
- **`utils.py`**: Enhanced UI components, live editing, conversation history, and download functionality

## 🔧 Configuration & Customization

### 🎨 Streamlit Configuration

The app includes optimized configuration in `.streamlit/config.toml`:

- **Custom Theme**: Professional color scheme with primary blue (#1f77b4)
- **Performance**: Disabled usage stats collection for privacy
- **Development**: Optimized port and headless configuration

### 🌍 Environment Setup

Required environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key (required for AI functionality)

Optional configuration:

- **Logging Level**: Configured in app.py (default: INFO)
- **Mermaid Version**: Currently using v11.6.0 (displayed in version badge)
- **Temperature**: Set to 0.1 for consistent AI responses

### ⚙️ Advanced Customization

The modular architecture allows easy customization:

- **Adding Diagram Types**: Extend `DiagramType` enum and add specialized generators
- **Custom Prompts**: Modify generator prompts in `diagram_generators.py`
- **Workflow Modifications**: Adjust LangGraph nodes in `agents.py`
- **UI Enhancements**: Customize CSS and components in `app.py` and `utils.py`

## 🐛 Troubleshooting & Support

### 🚨 Common Issues

1. **"Please set your OpenAI API key"**
   - Set `OPENAI_API_KEY` environment variable or add to Streamlit secrets
   - Verify your API key has sufficient credits and correct permissions

2. **Import or dependency errors**
   - Run `pip install -r requirements.txt` to install all dependencies
   - Ensure you're using Python 3.8+ and the virtual environment is activated

3. **Diagram rendering issues**
   - Check Mermaid code syntax in the live editor
   - Use the AI Auto-Fix feature for syntax errors
   - Try refreshing the page or clearing browser cache

4. **AI workflow errors**
   - Check internet connection and API key validity
   - The app includes comprehensive fallback mechanisms
   - Review logs in `logs/app.log` for detailed error information

5. **Performance issues**
   - Ensure adequate system resources (the app uses AI processing)
   - Check OpenAI API rate limits and usage quotas
   - Monitor browser console for client-side errors

### 🔍 Debugging Tips

- **Enable Verbose Logging**: Check `logs/app.log` for detailed execution traces
- **Test API Connection**: Verify OpenAI API access with a simple test
- **Clear Session State**: Refresh the page to reset session variables
- **Browser Compatibility**: Use modern browsers (Chrome, Firefox, Safari, Edge)

### 📞 Getting Help

- **Application Logs**: Check terminal output and `logs/app.log` for detailed error messages
- **Dependencies**: Ensure latest versions of all requirements are installed
- **API Status**: Verify OpenAI service status and your account limits
- **System Requirements**: Confirm Python 3.8+ and sufficient memory (>2GB recommended)

## 🎯 Development & Extensibility

### 🔧 Adding New Diagram Types

1. **Extend Enum**: Add new type to `DiagramType` enum in `agents.py`
2. **Create Generator**: Add specialized generator function in `diagram_generators.py`
3. **Add Templates**: Include syntax templates in `mermaid_syntax.py`
4. **Update UI**: Add emoji and styling in the main application
5. **Test Thoroughly**: Validate with various input scenarios

### 🤖 Customizing AI Workflows

The LangGraph workflow in `create_agent_workflow()` supports extensive customization:

- **Add Nodes**: Insert new processing steps (e.g., additional validation, enhancement)
- **Modify Routing**: Implement conditional logic for different user scenarios  
- **Custom Prompts**: Tailor AI responses for specific domains or use cases
- **State Management**: Extend `AgentState` for additional context tracking

### 🎨 UI/UX Enhancements

The modular design enables easy customization:

- **Custom Themes**: Modify `.streamlit/config.toml` and CSS in `app.py`
- **Enhanced Components**: Extend utility functions in `utils.py`
- **New Features**: Add capabilities like diagram templates, collaboration tools
- **Mobile Optimization**: Enhance responsive design for mobile devices

### 🔬 Advanced Features to Implement

Potential enhancements for contributors:

- **Diagram Templates**: Pre-built templates for common use cases
- **Collaborative Editing**: Multi-user diagram editing capabilities
- **Version Control**: Git-like versioning for diagram iterations
- **Export Formats**: Additional formats (PNG, SVG, PDF generation)
- **Integration APIs**: Connect with external tools and platforms

## 🌟 What Makes This Special

### 🚀 Beyond Basic Diagram Generation

This isn't just another diagram generator - it's a sophisticated AI-powered visualization platform:

- **Intelligent Understanding**: Deep analysis of your intent, not just keyword matching
- **Context-Aware Suggestions**: AI recommends the most appropriate diagram types for your specific use case
- **Professional Quality**: Specialized generators ensure syntactically correct, well-structured diagrams
- **Continuous Learning**: The system provides follow-up recommendations to enhance your visualization journey

### 💡 Perfect For

- **Business Analysts**: Process flows, user journeys, and system documentation
- **Software Developers**: Architecture diagrams, sequence flows, and class structures  
- **Project Managers**: Gantt charts, milestone tracking, and workflow visualization
- **Educators**: Concept maps, learning flows, and educational content
- **Students**: Research visualization, project planning, and concept exploration

### 🏆 Key Advantages

- **Zero Learning Curve**: Natural language input means no need to learn Mermaid syntax
- **Professional Results**: AI ensures best practices and proper diagram conventions
- **Time Saving**: From idea to polished diagram in seconds, not hours
- **Iterative Improvement**: Built-in recommendations help you create comprehensive diagram sets
- **Error-Free Output**: Advanced validation and auto-correction eliminate syntax issues

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! This project offers many opportunities for enhancement:

- **New Diagram Types**: Add support for additional Mermaid diagram types
- **Enhanced AI Features**: Improve intent analysis and recommendation algorithms  
- **UI/UX Improvements**: Enhance the user interface and experience
- **Performance Optimizations**: Optimize AI workflows and rendering performance
- **Documentation**: Improve guides, tutorials, and code documentation

Please feel free to submit a Pull Request or open an issue for discussion.

---

**Built with ❤️ using Streamlit, LangChain, LangGraph, and OpenAI**

*Transform your ideas into beautiful diagrams with the power of AI!*
