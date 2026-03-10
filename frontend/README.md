# SRL Chat Frontend Setup

This directory contains the Vue.js frontend for the SRL Chat application, adapted from Moodle to work as both a standalone application and LTI integrated tool.

## 🎯 Overview

The frontend has been refactored to:

- Remove Moodle-specific dependencies
- Support both standalone and LTI modes
- Connect directly to the SRL Chat backend API
- Use Bootstrap and FontAwesome for styling

## 🚀 Quick Start

### Frontend Testing (No Backend Required)

**Quick test without any Python setup:**

```bash
# Simply open the test file in your browser
open frontend/test.html
# OR double-click frontend/test.html
```

**Test with simple server (recommended):**

```bash
# Run the simplified frontend server
python frontend_server.py

# Then open: http://localhost:8000/
# Or test page: http://localhost:8000/test
```

This provides:

- ✅ Frontend testing with mock SRL responses
- ✅ No complex setup required
- ✅ Vue.js component testing (if built)
- ✅ Chat interface testing
- ✅ Realistic conversation flow

**What you'll see:**

- If Vue.js loads properly: Full Vue.js components with mock API
- If Vue.js fails to load: Simple HTML/JS chat interface
- All SRL conversation responses are simulated
- Click "Start Test Chat" to begin the mock conversation

### Development with Backend

**1. Install Dependencies**

```bash
cd frontend
npm install
```

### 2. Build for Development

```bash
# Using the build script (recommended)
./build-dev.sh

# Or manually
npm run dev
```

### 3. Start the Backend

In a separate terminal:

```bash
# Start the main SRL Chat API
poetry run python api/main.py

# OR start the LTI provider (includes frontend serving)
python api/lti_provider.py
```

### 4. Access the Application

- **Standalone Mode**: http://localhost:5000/
- **LTI Integration**: http://localhost:5000/launch (for LMS configuration)

## 📁 Key Files

- `src/main.js` - Entry point, adapted for standalone/LTI modes
- `src/store/index.js` - Vuex store, removed Moodle dependencies
- `src/components/AgentChat.vue` - Main chat component
- `src/classes/communication.js` - API communication layer
- `index.html` - Standalone HTML entry point
- `build-dev.sh` - Development build script

## 🔧 Configuration

### Environment Detection

The app automatically detects its environment:

```javascript
// Set by the loading page
window.SRL_CLIENT = "standalone" | "lti" | "moodle";

// Configuration object
window.SRL_CONFIG = {
  userId: "user_123",
  language: "en",
  apiBaseUrl: "http://localhost:5000",
  systemName: "SRL Chat",
  isAdmin: false,
};
```

### API Endpoints

The frontend connects to these backend endpoints:

- `POST /startConversation` - Initialize chat session
- `POST /reply` - Send user message and get agent response

## 🔗 LTI Integration

For LTI integration with Learning Management Systems:

1. Configure your LMS with these settings:

   - **Launch URL**: `http://localhost:5000/launch`
   - **Consumer Key**: `moodle_key`
   - **Shared Secret**: `geheimer_schluessel_123`

2. The LTI provider will automatically:
   - Validate OAuth signatures
   - Extract user information
   - Initialize the Vue.js app with LTI context

## 🛠 Development Commands

```bash
# Install dependencies
npm install

# Development build
npm run dev

# Production build
npm run build

# Watch mode for development
npm run watch

# Hot reload server
npm run watch-hot
```

## 📦 Dependencies

Key Vue.js ecosystem packages:

- `vue@2.6.10` - Vue.js framework
- `vuex@3` - State management
- `vue-router@3` - Routing
- `axios` - HTTP client
- `bootstrap-vue` - UI components
- `@fortawesome/vue-fontawesome` - Icons

## 🎨 Styling

The app uses:

- Bootstrap 5 for layout and components
- FontAwesome 6 for icons
- Custom CSS for chat interface
- Responsive design for mobile/desktop

## 🔍 Troubleshooting

### Build Issues

1. **Node modules missing**: Run `npm install`
2. **Build fails**: Check Node.js version (recommend 14+)
3. **Module not found**: Ensure all dependencies are installed

### Runtime Issues

1. **Backend connection failed**:
   - Ensure the Python backend is running
   - Check the API base URL configuration
2. **Vue app not loading**:
   - Check browser console for errors
   - Verify the compiled JS files are generated
3. **LTI launch fails**:
   - Verify OAuth signature configuration
   - Check LMS consumer key/secret settings

### API Connection

Test the backend manually:

```bash
# Test conversation start
curl -X POST http://localhost:5000/startConversation \
  -H "Content-Type: application/json" \
  -d '{"language": "en", "client": "web", "userid": "test123"}'

# Test reply
curl -X POST http://localhost:5000/reply \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "client": "web", "userid": "test123"}'
```

## 🏗 Architecture Changes

### From Moodle Plugin → Standalone App

**Removed:**

- `core/ajax` Moodle dependency
- `core/localstorage` Moodle dependency
- Course/module context requirements
- Moodle webservice calls

**Added:**

- Environment detection (standalone/LTI)
- Direct HTTP API calls with Axios
- Flexible configuration system
- LTI provider integration

**Refactored:**

- Store initialization without Moodle context
- Component communication without Moodle events
- User management for multiple environments

This setup provides a flexible foundation for both standalone usage and LTI integration while maintaining the core SRL Chat functionality.
