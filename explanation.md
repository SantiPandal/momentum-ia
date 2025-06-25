# How to design and create code 

## Silicon Valley Engineering Philosophy
- Think like a Y Combinator-backed founder
- Build with the speed and precision of a Vercel senior engineer
- Focus on high-impact, simple solutions
- Always optimize for simplicity and elegance

## First Principles Thinking
- Break down complex problems to their fundamental truths
- Build up from the simplest possible components
- Question assumptions and conventional approaches
- Think deeply about core user needs

## Vercel-Style Development Standards
- Deploy fast, deploy often
- Optimize for developer experience
- Build with edge-first architecture in mind
- Focus on performance and reliability
- Keep solutions minimal but powerful

## Engineering Workflow
- Run thorough typechecks before commits
- Ensure clean builds before deployment
- Debug issues immediately when found
- Remove tests after validation
- Document everything clearly and concisely in this file, so that we always have up to date context

## Communication & Documentation
- Write with Richard Feynman's clarity
- Explain complex concepts simply
- Focus on fundamental understanding


# Momentum-IA: AI Accountability Coach - Detailed Codebase Analysis

## Overview

**Momentum-IA** is an AI-powered accountability coaching system that helps users set and achieve goals through structured commitments with financial stakes. The system uses WhatsApp as the primary communication interface and integrates with multiple services to provide intelligent, conversational goal tracking and accountability coaching.

## Architecture Overview

The application follows a microservices-oriented architecture built on **FastAPI** with the following key components:

- **AI Agent System**: LangChain + LangGraph-powered conversational AI
- **Communication Layer**: WhatsApp integration via Twilio
- **Database Layer**: Supabase (PostgreSQL) for data persistence
- **API Layer**: FastAPI REST endpoints

## Project Structure

```
momentum-ia/
├── main.py                           # FastAPI application entry point
├── apis/
│   └── whatsapp.py                   # WhatsApp webhook and messaging endpoints
├── services/
│   ├── agents.py                     # AI agent configuration and logic
│   └── tools/
│       ├── communication_tools.py    # WhatsApp messaging tools
│       └── database_tools.py         # Database interaction tools
├── pyproject.toml                    # Poetry dependencies and configuration
├── poetry.lock                       # Dependency lock file
└── README.md                         # Project documentation (empty)
```

## Dependencies Analysis

### Core Framework Stack
- **FastAPI** (0.115.12): Modern, high-performance web framework for Python APIs
- **Uvicorn** (0.34.3): ASGI server for serving FastAPI applications
- **Python-multipart** (0.0.20): For handling multipart form data (WhatsApp webhooks)
### Development Tools
- **Ngrok** (3.8.0): Secure tunneling for local development
  - Exposes local server to the internet for webhook testing
  - Provides HTTPS endpoints for Twilio integration
  - Command: `ngrok http 8000` creates tunnel to FastAPI server
  - Dashboard shows request/response logs for debugging


### AI/ML Stack
- **LangChain** (0.3.25): Framework for developing LLM-powered applications
- **LangChain-OpenAI** (0.3.19): OpenAI integration for LangChain
- **LangGraph** (0.2.0): Framework for building stateful, multi-actor applications with LLMs

### External Services
- **Twilio** (9.6.2): WhatsApp Business API integration
- **Supabase** (2.15.2): Backend-as-a-Service for database and authentication
- **Python-dotenv** (1.1.0): Environment variable management

## Detailed Component Analysis

### 1. Main Application (`main.py`)

**Purpose**: Entry point for the FastAPI application

**Key Features**:
- Creates FastAPI application instance
- Includes WhatsApp router with `/whatsapp` prefix
- Provides basic health check endpoint at root (`/`)

**Code Structure**:
```python
app = FastAPI()
app.include_router(whatsapp_router, prefix="/whatsapp")

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

### 2. WhatsApp API Layer (`apis/whatsapp.py`)

**Purpose**: Handles WhatsApp webhook integration and messaging endpoints

**Key Endpoints**:

#### `/whatsapp/webhook` (POST)
- **Function**: Receives incoming WhatsApp messages from Twilio
- **Process Flow**:
  1. Extracts message body and sender phone number from form data
  2. Creates thread ID from phone number for conversation continuity
  3. Formats message for AI agent processing
  4. Invokes agent asynchronously with message context
  5. Agent handles response automatically via tools

#### `/whatsapp/send_proof_flow` (POST)
- **Function**: Sends WhatsApp Flow for proof submission
- **Input**: JSON with `to` field (phone number)
- **Process**: Uses environment-configured Flow ID to send interactive form

#### `/whatsapp/send_test_message` (POST)
- **Function**: Sends plain text WhatsApp messages for testing
- **Input**: JSON with `to` and `body` fields
- **Purpose**: Development and debugging support

**Integration Points**:
- Imports agent executor from `services.agents`
- Uses communication tools for message sending
- Handles async processing for webhook responses

### 3. AI Agent System (`services/agents.py`)

**Purpose**: Core AI logic implementing the accountability coaching workflow

**AI Stack Configuration**:
- **Model**: GPT-4.1 with temperature=1 for varied responses
- **Framework**: LangGraph's `create_react_agent` with ReAct pattern
- **Memory**: MemorySaver for conversation persistence
- **Tools**: 5 custom tools for database and communication operations

**Agent Personality**:
Combines traits of David Goggins (intensity), Ryan Reynolds (wit), and Marcus Aurelius (wisdom) for effective accountability coaching.

**Core Workflow Stages**:

#### Stage 1: User Setup
- **Trigger**: `get_user_status` returns `'new_user'`
- **Process**:
  1. Request user's first name via WhatsApp
  2. Save name using `update_user_name` tool
  3. Confirm registration completion
- **Constraint**: No goal discussion until setup complete

#### Stage 2: Goal Setting
- **Trigger**: `get_user_status` returns `'user_exists_no_goal'`
- **Process**: Sequential data collection:
  1. Goal description
  2. Start date (YYYY-MM-DD)
  3. End date (YYYY-MM-DD)
  4. Financial stake amount
  5. Verification method
- **Completion**: Creates commitment via `create_commitment` tool

#### Stage 3: Active Coaching
- **Trigger**: `get_user_status` returns `'user_exists_active_goal'`
- **Process**:
  1. Retrieve active commitment details
  2. Provide personalized check-ins
  3. Offer motivation and progress support

**Tool Integration**:
```python
tools = [get_user_status, update_user_name, send_whatsapp_message, 
         create_commitment, get_active_commitment]
```

### 4. Communication Tools (`services/tools/communication_tools.py`)

**Purpose**: WhatsApp messaging capabilities using Twilio API

#### `send_whatsapp_message` Tool
- **Function**: Sends plain text WhatsApp messages
- **Parameters**: `to_number` (recipient), `body` (message content)
- **Implementation**:
  - Validates Twilio credentials from environment
  - Formats numbers with `whatsapp:` prefix
  - Uses Twilio Client for message delivery
  - Returns success confirmation with SID

#### `send_whatsapp_flow` Tool
- **Function**: Sends interactive WhatsApp Flows
- **Parameters**: `to_number`, `flow_id`, `body` (optional)
- **Use Case**: Proof submission forms and interactive experiences
- **Implementation**: Uses Twilio's `persistent_action` parameter

**Security Features**:
- Environment-based credential management
- Error handling with detailed logging
- Input validation and formatting

### 5. Database Tools (`services/tools/database_tools.py`)

**Purpose**: Supabase database interactions for user and commitment management

**Database Schema Integration**:
- **Users Table**: `id`, `phone_number`, `name`
- **Commitments Table**: Complex schema with goals, stakes, dates, schedules
- **Verifications Table**: Proof tracking and completion records

#### Core Tools:

##### `get_user_status`
- **Function**: User lookup and status determination
- **Logic**:
  1. Search user by phone number
  2. Create new user if not found
  3. Check name completion for setup status
  4. Query active commitments
  5. Return appropriate status string

##### `update_user_name`
- **Function**: Updates user's name during onboarding
- **Validation**: Ensures user exists before update
- **Return**: Success confirmation message

##### `create_commitment`
- **Function**: Creates new goal commitments
- **Parameters**:
  - `goal_description`: High-level goal description
  - `stake_amount`: Financial commitment amount
  - `start_date`/`end_date`: Goal timeframe
  - `task_description`: Specific daily/periodic tasks
  - `stake_type`: "per_missed_day" or "one_time_on_failure"
  - `schedule`: Frequency configuration (daily/weekly)
  - `verification_method`: Proof requirements

##### `get_active_commitment`
- **Function**: Retrieves current active commitment details
- **Output**: Formatted summary including all commitment parameters

##### `create_verification`
- **Function**: Records proof submissions for commitments
- **Parameters**: Due date, proof URL, justification text
- **Status**: Defaults to "completed_on_time"

**Database Connection**:
```python
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
```

## Data Flow Architecture

### Incoming Message Flow
1. **WhatsApp** → **Twilio Webhook** → **FastAPI** (`/whatsapp/webhook`)
2. **FastAPI** extracts message and phone number
3. **Agent** receives formatted input with context
4. **Agent** uses `get_user_status` to determine conversation stage
5. **Agent** executes appropriate workflow based on status
6. **Agent** uses `send_whatsapp_message` for response delivery

### User Journey Flow
1. **First Contact**: User creation and name collection
2. **Goal Setting**: Sequential data gathering for commitment creation
3. **Active Monitoring**: Ongoing coaching and verification tracking

### Database Interaction Patterns
- **Read Operations**: User status checks, commitment retrieval
- **Write Operations**: User creation/updates, commitment creation, verification logging
- **State Management**: Conversation threading via phone number

## Environment Configuration

**Required Environment Variables**:
- `TWILIO_ACCOUNT_SID`: Twilio account identifier
- `TWILIO_AUTH_TOKEN`: Twilio authentication token
- `TWILIO_WHATSAPP_NUMBER`: Twilio WhatsApp business number
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase service key
- `PROOF_OF_WORK_FLOWID`: WhatsApp Flow ID for proof submissions
- `OPENAI_API_KEY`: OpenAI API key for GPT-4.1 access

## Security Considerations

### Credential Management
- All sensitive credentials stored in environment variables
- No hardcoded API keys or tokens in source code
- Supabase provides built-in security features

### Data Privacy
- Phone numbers used as primary identifiers
- User data isolated by phone number
- Conversation threading prevents data leakage

### Input Validation
- Form data validation for webhook inputs
- Database query parameterization prevents injection
- Error handling prevents information disclosure

## Scalability Architecture

### Conversation Management
- Thread-based conversation isolation using phone numbers
- MemorySaver provides persistent conversation context
- Stateful agent execution with proper session handling

### Database Design
- Normalized schema with proper foreign key relationships
- Indexed phone number lookups for performance
- JSONB fields for flexible schedule configurations

### API Performance
- Async FastAPI endpoints for non-blocking operations
- Background agent processing for webhook responses
- Efficient database queries with selective field retrieval

## Development and Deployment

### Development Setup
- **Poetry** for dependency management and virtual environments
- **Python 3.11+** requirement for modern language features
- **FastAPI** development server via Uvicorn

### Testing Infrastructure
- Test endpoints for message sending (`/send_test_message`)
- Proof flow testing via dedicated endpoint
- Environment-based configuration for different deployment stages

### Extension Points
- **Tool System**: Easy addition of new LangChain tools
- **Flow Integration**: Support for additional WhatsApp Flows
- **Database Schema**: Extensible commitment and verification models
- **Agent Personality**: Configurable prompt system

## Technical Strengths

1. **Modern AI Integration**: LangChain/LangGraph provides robust LLM orchestration
2. **Conversational AI**: Natural language processing with structured workflows
3. **State Management**: Persistent conversation context and user progression tracking
4. **Flexible Commitment System**: Configurable goals, stakes, and verification methods
5. **Real-time Communication**: WhatsApp integration for immediate user engagement
6. **Scalable Database**: Supabase provides production-ready PostgreSQL backend

## Potential Enhancement Areas

1. **Error Recovery**: Enhanced error handling for failed API calls
2. **User Analytics**: Tracking of goal completion rates and engagement metrics
3. **Notification System**: Proactive reminders and check-ins
4. **Payment Integration**: Automated stake collection and distribution
5. **Proof Verification**: AI-powered validation of submitted proof
6. **Multi-language Support**: Internationalization for broader user base
7. **Web Dashboard**: Administrative interface for system monitoring

This codebase represents a well-architected AI accountability coaching system with strong separation of concerns, modern technology integration, and clear extensibility patterns for future enhancement.