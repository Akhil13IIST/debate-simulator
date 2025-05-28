# Debate Simulator

A sophisticated platform for simulating structured debates between AI agents using large language models.

## Overview

The Debate Simulator is designed to create and simulate structured debates between AI agents. This application leverages large language models to generate contextually appropriate arguments, rebuttals, and discourse between multiple AI personas. It provides a realistic environment for observing how language models engage with complex topics from different perspectives.

## Features

- **Multi-Agent Architecture**: Orchestrates interactions between debater agents and a moderator
- **Customizable Personas**: Configure detailed personas with specific attributes, debate styles, and stances
- **Structured Debate Formats**: Support for various debate structures with opening statements, rebuttals, cross-examination, and closing remarks
- **Real-time UI**: Streamlit-based interface for configuring debates and observing them in real-time
- **Fact Checking**: Optional fact-checking capabilities using external knowledge sources
- **Complete Transcripts**: Comprehensive logging and transcript generation for analysis

## Project Structure

```
debate_simulator/
├── app.py                  # Main Streamlit application
├── debate_engine.py        # Core debate orchestration engine
├── agents/
│   ├── base_agent.py       # Base agent class
│   ├── debater_agent.py    # Debater agent implementation  
│   └── moderator_agent.py  # Moderator agent implementation
├── config/
│   ├── config_manager.py   # Configuration management
│   ├── debates/            # Predefined debate templates
│   ├── personas/           # Agent persona configurations
│   └── prompt_templates/   # LLM prompt templates
├── ui/                     # UI components
└── utils/                  # Utility functions and helpers
```

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/debate-simulator.git
   cd debate-simulator
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your API keys (see `.env.example` for format)

## Usage

1. Run the Streamlit application:
   ```
   streamlit run app.py
   ```

2. Configure your debate:
   - Select a debate topic and format
   - Configure debater and moderator personas
   - Set debate parameters (turn count, time limits, etc.)

3. Start the debate and observe the AI agents engage in structured discourse

4. Review debate transcripts and summaries after completion

## Customization

### Adding Custom Personas

Create new persona configuration files in the `config/personas/` directory following the existing schema.

### Creating Debate Templates

Define new debate structures in the `config/debates/` directory, specifying formats, topics, and rules.

### Extending Agent Capabilities

The modular design allows for extending agent capabilities by modifying the respective agent classes.

## Requirements

- Python 3.8+
- OpenAI API key or other supported LLM API keys
- Streamlit
- Other dependencies listed in `requirements.txt`

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
