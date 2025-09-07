import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Configure Streamlit page
st.set_page_config(
    page_title="📚 Book Recommendation Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .chat-container {
        height: 500px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #fafafa;
        margin-bottom: 20px;
    }
    
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 5px 15px;
        margin: 10px 0;
        max-width: 70%;
        margin-left: auto;
        word-wrap: break-word;
        text-align: right;
    }
    
    .bot-message {
        background-color: #f0f2f6;
        color: black;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 5px;
        margin: 10px 0;
        max-width: 70%;
        word-wrap: break-word;
        white-space: pre-wrap;
    }
    
    .timestamp {
        font-size: 0.8em;
        color: #666;
        margin-top: 5px;
    }
    
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    
    .status-online {
        background-color: #28a745;
    }
    
    .status-offline {
        background-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Rasa server configuration
RASA_SERVER_URL = "http://localhost:5005/webhooks/rest/webhook"
RASA_HEALTH_URL = "http://localhost:5005"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add welcome message
    welcome_msg = """Hello! 👋 Welcome to the Book Recommendation Chatbot!

I can help you with:
📖 Finding books by title
👤 Searching books by author  
📚 Browsing books by genre
⭐ Getting top-rated books
📄 Book details (pages, description, rating, etc.)
🎲 Random book recommendations

Try asking me something like:
• "Recommend me a book"
• "Find books by Stephen King"  
• "Show me fantasy books"
• "What are the top rated books?"

What would you like to know? 😊"""

    st.session_state.messages.append({
        "sender": "bot",
        "message": welcome_msg,
        "timestamp": datetime.now()
    })

if "user_id" not in st.session_state:
    st.session_state.user_id = f"streamlit_user_{int(time.time())}"

def check_rasa_connection():
    """Check if Rasa server is running"""
    try:
        response = requests.get(RASA_HEALTH_URL, timeout=3)
        return response.status_code == 200
    except:
        return False

def send_message_to_rasa(message, user_id=None):
    """Send message to Rasa server and get response"""
    if user_id is None:
        user_id = st.session_state.user_id
    
    try:
        payload = {
            "sender": user_id,
            "message": message
        }
        
        response = requests.post(
            RASA_SERVER_URL,
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return [{"text": f"❌ Server error (Status: {response.status_code}). Please try again."}]
    
    except requests.exceptions.ConnectionError:
        return [{"text": "❌ Cannot connect to the chatbot server.\n\nPlease make sure Rasa is running:\n1. Open terminal in your Rasa project directory\n2. Run: rasa run --enable-api --cors \"*\" --port 5005"}]
    except requests.exceptions.Timeout:
        return [{"text": "⏰ Request timeout. The server is taking too long to respond. Please try again."}]
    except Exception as e:
        return [{"text": f"❌ An error occurred: {str(e)}"}]

def display_message(message, sender, timestamp):
    """Display a chat message with proper styling"""
    if sender == "user":
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
            <div class="user-message">
                {message}
                <div class="timestamp" style="color: rgba(255,255,255,0.8);">
                    {timestamp.strftime('%H:%M')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
            <div class="bot-message">
                {message}
                <div class="timestamp">
                    🤖 Bot • {timestamp.strftime('%H:%M')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Main app layout
st.title("📚 Book Recommendation Chatbot")
st.markdown("*Powered by Rasa & Streamlit*")

# Check Rasa connection status
rasa_online = check_rasa_connection()

# Sidebar with information and controls
with st.sidebar:
    # Connection status
    st.header("🔧 Server Status")
    if rasa_online:
        st.markdown('<span class="status-indicator status-online"></span>**Rasa Server: Online**', unsafe_allow_html=True)
        st.success("Connected to chatbot service")
    else:
        st.markdown('<span class="status-indicator status-offline"></span>**Rasa Server: Offline**', unsafe_allow_html=True)
        st.error("Cannot connect to chatbot service")
        st.info("To start Rasa server:\n```\nrasa run --enable-api --cors \"*\" --port 5005\n```")
    
    st.markdown("---")
    
    # App information
    st.header("📋 About This Chatbot")
    st.write("""
    This intelligent chatbot can help you discover books and get detailed information about them.
    
    **Features:**
    - 📖 Search books by title
    - 👤 Find books by author  
    - 📚 Browse books by genre
    - ⭐ Get top-rated recommendations
    - 📄 Get book details (pages, rating, description)
    - 🎲 Random book suggestions
    - 📅 Publication dates and publisher info
    """)
    
    st.markdown("---")
    
    # Quick commands
    st.header("💡 Try These Examples")
    quick_commands = [
        "Recommend me a book",
        "Find books by J.K. Rowling",
        "Show me science fiction books", 
        "What are the top rated books?",
        "Tell me about The Great Gatsby",
        "How many pages does Dune have?",
        "Who published Harry Potter?",
        "Show me the book cover for 1984"
    ]
    
    selected_command = st.selectbox(
        "Choose a sample question:",
        ["Select an example..."] + quick_commands
    )
    
    if st.button("📤 Use This Example") and selected_command != "Select an example...":
        st.session_state.selected_example = selected_command
    
    st.markdown("---")
    
    # Chat controls
    st.header("⚙️ Chat Controls")
    
    if st.button("🗑️ Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.session_state.messages.append({
            "sender": "bot",
            "message": "Chat cleared! 🧹 How can I help you find books today?",
            "timestamp": datetime.now()
        })
        st.experimental_rerun()
    
    if st.button("🔄 Refresh Connection"):
        st.experimental_rerun()
    
    # Statistics
    st.markdown("---")
    st.header("📊 Chat Statistics")
    user_msgs = sum(1 for msg in st.session_state.messages if msg["sender"] == "user")
    bot_msgs = sum(1 for msg in st.session_state.messages if msg["sender"] == "bot")
    st.metric("Your Messages", user_msgs)
    st.metric("Bot Responses", bot_msgs)

# Main chat area
col1, col2 = st.columns([3, 1])

with col1:
    st.header("💬 Chat")
    
    # Create chat container
    chat_container = st.container()
    
    # Display all messages
    with chat_container:
        for msg in st.session_state.messages:
            display_message(msg["message"], msg["sender"], msg["timestamp"])
    
    # Handle example selection
    if hasattr(st.session_state, 'selected_example'):
        user_input = st.session_state.selected_example
        del st.session_state.selected_example
        
        # Add user message
        st.session_state.messages.append({
            "sender": "user",
            "message": user_input,
            "timestamp": datetime.now()
        })
        
        # Get bot response
        if rasa_online:
            with st.spinner("🤔 Thinking..."):
                bot_responses = send_message_to_rasa(user_input)
            
            # Add bot responses
            for response in bot_responses:
                bot_message = response.get("text", "I'm sorry, I didn't understand that. Could you please rephrase?")
                st.session_state.messages.append({
                    "sender": "bot",
                    "message": bot_message,
                    "timestamp": datetime.now()
                })
        else:
            st.session_state.messages.append({
                "sender": "bot", 
                "message": "❌ I can't process your request right now because the Rasa server is not running. Please check the connection status in the sidebar.",
                "timestamp": datetime.now()
            })
        
        st.experimental_rerun()

with col2:
    st.header("🎯 Quick Actions")
    
    quick_actions = [
        ("🎲", "Random book", "Recommend me a random book"),
        ("⭐", "Top rated", "Show me top rated books"),
        ("📚", "Fantasy books", "Find fantasy books"),
        ("🔍", "Search help", "How can I search for books?")
    ]
    
    for emoji, label, command in quick_actions:
        if st.button(f"{emoji} {label}", key=f"quick_{label}"):
            st.session_state.selected_example = command
            st.experimental_rerun()

# Input area (fixed at bottom)
st.markdown("---")
st.header("✍️ Send a Message")

# Create input form
with st.form("message_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Your message:",
            placeholder="Ask me about books! Try 'recommend me a book' or 'find books by [author]'",
            help="Type your question about books and press Enter or click Send"
        )
    
    with col2:
        send_button = st.form_submit_button("Send 📤", type="primary", use_container_width=True)

# Handle form submission
if send_button and user_input.strip():
    # Add user message to chat
    st.session_state.messages.append({
        "sender": "user", 
        "message": user_input.strip(),
        "timestamp": datetime.now()
    })
    
    # Get bot response
    if rasa_online:
        with st.spinner("🤔 Processing your request..."):
            bot_responses = send_message_to_rasa(user_input.strip())
        
        # Add bot responses to chat
        for response in bot_responses:
            bot_message = response.get("text", "I'm sorry, I didn't understand that. Could you please rephrase your question?")
            st.session_state.messages.append({
                "sender": "bot",
                "message": bot_message,
                "timestamp": datetime.now()
            })
    else:
        # Server offline message
        st.session_state.messages.append({
            "sender": "bot",
            "message": "❌ I can't process your request right now because the Rasa server is not running.\n\nTo fix this:\n1. Open a terminal in your Rasa project directory\n2. Run: `rasa run --enable-api --cors \"*\" --port 5005`\n3. Wait for the server to start\n4. Refresh this page",
            "timestamp": datetime.now()
        })
    
    # Rerun to show new messages
    st.experimental_rerun()

elif send_button and not user_input.strip():
    st.warning("⚠️ Please enter a message before sending!")

# Auto-scroll JavaScript (optional enhancement)
if st.session_state.messages:
    st.markdown("""
    <script>
        // Auto-scroll to bottom
        setTimeout(function() {
            var chatContainer = window.parent.document.querySelector('.main .block-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }, 100);
    </script>
    """, unsafe_allow_html=True)

# Footer with instructions
st.markdown("---")
st.markdown("""
### 🚀 Getting Started

**To use this chatbot:**

1. **Start the Rasa server** (if not already running):
   ```bash
   cd your-rasa-project-directory
   rasa run --enable-api --cors "*" --port 5005
   ```

2. **Make sure your data is ready**:
   - Ensure `Books.csv` is in your `data/` directory
   - Verify your Rasa model is trained (`rasa train`)

3. **Start chatting**:
   - Type questions in the input box above
   - Use the quick examples in the sidebar
   - Try the quick action buttons

**Example questions to try:**
- "Find me a good mystery book"
- "What books did Agatha Christie write?"  
- "Show me books with 5-star ratings"
- "How many pages does Pride and Prejudice have?"
""")

st.markdown("""
---
<div style='text-align: center; color: #666; padding: 20px;'>
    <small>📚 Book Recommendation Chatbot | Built with Rasa & Streamlit</small><br>
    <small>💡 Need help? Check the sidebar for examples and tips!</small>
</div>
""", unsafe_allow_html=True)
