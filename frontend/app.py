"""Recipier - AI Recipe Search Frontend."""
import streamlit as st
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from frontend.config import APP_CONFIG
from frontend.styles.theme import get_theme_css
from frontend.utils.state import StateManager
from frontend.utils.search_handler import SearchHandler
from frontend.components.search_bar import render_search_bar
from frontend.components.recipe_card import render_recipe_card
from frontend.components.sidebar import render_sidebar


def main():
    """Main application entry point."""
    # Page config must be first Streamlit command
    st.set_page_config(
        page_title=APP_CONFIG['page_title'],
        page_icon=APP_CONFIG['icon'],
        layout=APP_CONFIG['layout'],
        initial_sidebar_state=APP_CONFIG['initial_sidebar_state']
    )

    # Initialize state
    StateManager.initialize()

    # Apply dark theme CSS
    st.markdown(get_theme_css(), unsafe_allow_html=True)

    # Initialize search handler
    search_handler = SearchHandler()

    # Sidebar
    with st.sidebar:
        st.markdown(f"# {APP_CONFIG['icon']} {APP_CONFIG['title']}")
        st.markdown("---")

        # Search history
        render_sidebar(
            on_select=StateManager.select_history,
            on_clear=StateManager.clear_selection,
            selected_id=StateManager.get(StateManager.SELECTED_HISTORY_ID)
        )

    # Main content
    st.markdown(f"# {APP_CONFIG['icon']} {APP_CONFIG['title']}")
    st.markdown("*Your AI-powered recipe assistant*")

    # Search bar
    def handle_search(query: str):
        """Handle search submission."""
        StateManager.set_loading(True)
        StateManager.clear_error()
        StateManager.set(StateManager.SELECTED_HISTORY_ID, None)

    render_search_bar(
        on_search=handle_search,
        default_value=StateManager.get_current_query()
    )

    # Check if we need to perform a search
    if 'search_input' in st.session_state:
        query = st.session_state.search_input
        current_query = StateManager.get_current_query()

        # Only search if query changed
        if query and query != current_query:
            # Clear previous response before searching
            StateManager.set_current_response(None)
            StateManager.set_loading(True)
            StateManager.clear_error()
            StateManager.set_current_query(query)

            # Create container for streaming response
            st.markdown(f"### 🔍 Searching for: *{query}*")
            st.markdown("---")
            
            # Create a placeholder for the streaming content
            response_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            try:
                for event in search_handler.search_stream(query):
                    if event['type'] == 'chunk':
                        # Append chunk and update display
                        full_response += event['content']
                        response_placeholder.markdown(full_response)
                    elif event['type'] == 'error':
                        StateManager.set_error(event['error'])
                        StateManager.set_current_response(None)
                        StateManager.set_loading(False)
                        st.rerun()
                        break
                    elif event['type'] == 'done':
                        # Save the complete response
                        StateManager.set_current_response(full_response)
                        StateManager.set_loading(False)
                        # No need to rerun, response is already displayed
                        break
            except Exception as e:
                StateManager.set_error(f"Streaming failed: {str(e)}")
                StateManager.set_current_response(None)
                StateManager.set_loading(False)
                st.rerun()
        else:
            # Display current results (not loading)
            render_recipe_card(
                response=StateManager.get_current_response(),
                query=StateManager.get_current_query(),
                is_loading=False,
                error=StateManager.get_error()
            )
    else:
        # No search input yet, show empty state
        render_recipe_card(
            response=StateManager.get_current_response(),
            query=StateManager.get_current_query(),
            is_loading=StateManager.is_loading(),
            error=StateManager.get_error()
        )


if __name__ == '__main__':
    main()
