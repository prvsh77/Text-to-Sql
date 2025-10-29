import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

# Import our modules
from db_setup import create_sample_database, get_database_schema
from nlp_parser import TextToSQLParser
from query_executor import QueryExecutor
from visualizer import DataVisualizer

# Page configuration
st.set_page_config(
    page_title="Text-to-SQL Query Interface",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = False
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'parser' not in st.session_state:
        st.session_state.parser = None
    if 'executor' not in st.session_state:
        st.session_state.executor = None
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = None

def initialize_components():
    """Initialize the NLP parser, query executor, and visualizer."""
    if st.session_state.parser is None:
        with st.spinner("Initializing NLP parser..."):
            st.session_state.parser = TextToSQLParser()
    
    if st.session_state.executor is None:
        st.session_state.executor = QueryExecutor()
    
    if st.session_state.visualizer is None:
        st.session_state.visualizer = DataVisualizer()

def setup_database():
    """Setup the sample database."""
    db_path = 'data/sample_db.sqlite'
    
    if not os.path.exists('data'):
        os.makedirs('data')
    
    if not os.path.exists(db_path) or not st.session_state.db_initialized:
        with st.spinner("Setting up sample database..."):
            create_sample_database(db_path)
            st.session_state.db_initialized = True
            st.success("✅ Database setup complete!")
    
    return db_path

def display_database_info():
    """Display database schema information in sidebar."""
    st.sidebar.markdown("## 📊 Database Schema")
    
    schema_info = {
        'customers': ['customer_id', 'name', 'email', 'city', 'state', 'phone', 'created_date'],
        'products': ['product_id', 'name', 'category', 'price', 'stock_quantity', 'description'],
        'orders': ['order_id', 'customer_id', 'order_date', 'total_amount', 'status', 'shipping_city'],
        'order_items': ['item_id', 'order_id', 'product_id', 'quantity', 'unit_price']
    }
    
    for table, columns in schema_info.items():
        with st.sidebar.expander(f"📋 {table}"):
            for col in columns:
                st.write(f"• {col}")

def display_sample_queries():
    """Display sample queries in sidebar."""
    st.sidebar.markdown("## 💡 Sample Queries")
    
    sample_queries = [
        "Show all customers from Bangalore",
        "List orders placed after 2024-01-01", 
        "Count total orders",
        "Show total sales by city",
        "Find customers with orders",
        "List products in Electronics category",
        "Show average order amount",
        "Count customers per city",
        "List completed orders",
        "Show recent orders"
    ]
    
    for i, query in enumerate(sample_queries):
        if st.sidebar.button(query, key=f"sample_{i}"):
            st.session_state.selected_query = query

def process_natural_language_query(query_text):
    """Process natural language query and return results."""
    if not query_text.strip():
        return None, None, "Please enter a query"
    
    try:
        # Parse natural language to SQL
        with st.spinner("Converting natural language to SQL..."):
            sql_query, metadata = st.session_state.parser.parse_query(query_text)
        
        # Execute SQL query
        with st.spinner("Executing query..."):
            df, exec_metadata = st.session_state.executor.execute_query(sql_query)
        
        # Add to query history
        st.session_state.query_history.append({
            'natural_query': query_text,
            'sql_query': sql_query,
            'success': exec_metadata['success'],
            'row_count': exec_metadata['row_count'],
            'confidence': metadata.get('confidence', 0)
        })
        
        return df, sql_query, exec_metadata, metadata
        
    except Exception as e:
        return None, None, f"Error processing query: {str(e)}", None

def display_query_results(df, sql_query, exec_metadata, parse_metadata):
    """Display query results with visualizations."""
    
    # Show generated SQL
    st.markdown("### 🔍 Generated SQL Query")
    st.markdown(f'<div class="query-box"><code>{sql_query}</code></div>', unsafe_allow_html=True)
    
    # Show confidence and metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        confidence = parse_metadata.get('confidence', 0) if parse_metadata else 0
        st.metric("Query Confidence", f"{confidence:.1%}")
    with col2:
        st.metric("Rows Returned", exec_metadata['row_count'])
    with col3:
        st.metric("Execution Time", f"{exec_metadata['execution_time']:.3f}s")
    
    if exec_metadata['success'] and df is not None and not df.empty:
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Visualization", "📋 Data Table", "📈 Summary Stats"])
        
        with tab1:
            st.markdown("### Data Visualization")
            
            # Get visualization recommendations
            recommendations = st.session_state.visualizer.get_chart_recommendations(df)
            
            if recommendations:
                # Let user choose chart type
                chart_options = list(recommendations.keys())
                selected_chart = st.selectbox(
                    "Choose visualization type:",
                    chart_options,
                    help="Select the type of chart you want to display"
                )
                
                # Create and display visualization
                fig, description = st.session_state.visualizer.create_visualization(df, selected_chart)
                
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    st.info(f"📊 {description}")
                else:
                    st.info("📋 Data displayed as table - visualization not suitable for this data type")
            else:
                st.info("📋 No suitable visualizations available for this data")
        
        with tab2:
            st.markdown("### Data Table")
            
            # Format table for display
            display_df = st.session_state.visualizer.format_table_display(df)
            
            # Show pagination info
            if len(df) > 100:
                st.warning(f"Showing first 100 rows of {len(df)} total rows")
            
            st.dataframe(display_df, use_container_width=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"query_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with tab3:
            st.markdown("### Summary Statistics")
            
            summary_stats = st.session_state.visualizer.create_summary_stats(df)
            
            if not summary_stats.empty:
                st.dataframe(summary_stats, use_container_width=True)
            else:
                st.info("No numeric columns found for summary statistics")
            
            # Additional insights
            st.markdown("#### Data Insights")
            insights = []
            
            if not df.empty:
                insights.append(f"Dataset contains {len(df)} rows and {len(df.columns)} columns")
                
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    insights.append(f"Found {len(numeric_cols)} numeric columns")
                
                categorical_cols = df.select_dtypes(include=['object']).columns
                if len(categorical_cols) > 0:
                    insights.append(f"Found {len(categorical_cols)} text/categorical columns")
                
                # Check for missing values
                missing_data = df.isnull().sum().sum()
                if missing_data > 0:
                    insights.append(f"Dataset contains {missing_data} missing values")
                else:
                    insights.append("No missing values detected")
            
            for insight in insights:
                st.write(f"• {insight}")
    
    elif not exec_metadata['success']:
        st.markdown(f'<div class="error-box">❌ Query failed: {exec_metadata["error"]}</div>', 
                   unsafe_allow_html=True)
    else:
        st.markdown('<div class="info-box">ℹ️ Query executed successfully but returned no data</div>', 
                   unsafe_allow_html=True)

def display_query_history():
    """Display query history in sidebar."""
    if st.session_state.query_history:
        st.sidebar.markdown("## 📝 Query History")
        
        for i, query in enumerate(reversed(st.session_state.query_history[-10:])):  # Show last 10
            with st.sidebar.expander(f"Query {len(st.session_state.query_history) - i}"):
                st.write(f"**Natural Language:** {query['natural_query']}")
                st.write(f"**SQL:** `{query['sql_query'][:50]}...`")
                st.write(f"**Status:** {'✅' if query['success'] else '❌'}")
                st.write(f"**Rows:** {query['row_count']}")
                st.write(f"**Confidence:** {query['confidence']:.1%}")

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # App header
    st.markdown('<h1 class="main-header">🔍 Text-to-SQL Query Interface</h1>', unsafe_allow_html=True)
    st.markdown("Convert natural language questions into SQL queries and visualize the results!")
    
    # Setup database
    db_path = setup_database()
    
    # Initialize components
    initialize_components()
    
    # Sidebar
    display_database_info()
    display_sample_queries()
    display_query_history()
    
    # Main interface
    st.markdown("## 💬 Ask a Question About Your Data")
    
    # Handle sample query selection
    if 'selected_query' in st.session_state:
        default_query = st.session_state.selected_query
        del st.session_state.selected_query
    else:
        default_query = ""
    
    # Query input
    natural_query = st.text_area(
        "Enter your question in plain English:",
        value=default_query,
        placeholder="e.g., Show all customers from Bangalore who made orders after 2024-01-01",
        height=100,
        help="Type your question naturally. The system will convert it to SQL automatically."
    )
    
    # Query options
    col1, col2 = st.columns([3, 1])
    with col1:
        auto_visualize = st.checkbox("Auto-generate visualization", value=True)
    with col2:
        process_button = st.button("🚀 Process Query", type="primary")
    
    # Process query
    if process_button or natural_query != default_query and natural_query.strip():
        if natural_query.strip():
            # Process the query
            result = process_natural_language_query(natural_query)
            
            if len(result) == 4:
                df, sql_query, exec_metadata, parse_metadata = result
                display_query_results(df, sql_query, exec_metadata, parse_metadata)
            else:
                # Error case
                st.markdown(f'<div class="error-box">❌ {result[2]}</div>', unsafe_allow_html=True)
        else:
            st.warning("Please enter a question to process.")
    
    # Tips and help
    with st.expander("💡 Tips for Better Results"):
        st.markdown("""
        **To get better results, try these tips:**
        
        1. **Be specific about what you want:**
           - ✅ "Show customers from Bangalore"
           - ❌ "Show data"
        
        2. **Use clear filter criteria:**
           - ✅ "Orders placed after 2024-01-01"
           - ✅ "Products with price greater than 10000"
        
        3. **Ask for aggregations naturally:**
           - ✅ "Count total orders by city"
           - ✅ "Show average order amount per customer"
        
        4. **Use common terms:**
           - Use "customers" instead of "users"
           - Use "orders" instead of "transactions"
           - Use "products" instead of "items"
        
        5. **Combine tables naturally:**
           - ✅ "Show customer names with their order totals"
           - ✅ "List products ordered by customers from Mumbai"
        """)
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        st.markdown("### Query Builder")
        
        # Manual SQL input
        st.markdown("**Manual SQL Query** (for advanced users):")
        manual_sql = st.text_area(
            "Enter SQL query directly:",
            placeholder="SELECT * FROM customers WHERE city = 'Bangalore' LIMIT 10",
            height=80
        )
        
        if st.button("Execute Manual SQL"):
            if manual_sql.strip():
                with st.spinner("Executing manual SQL query..."):
                    df, exec_metadata = st.session_state.executor.execute_query(manual_sql)
                
                if exec_metadata['success'] and df is not None:
                    st.success(f"✅ Query executed successfully! {exec_metadata['row_count']} rows returned.")
                    display_query_results(df, manual_sql, exec_metadata, {'confidence': 1.0})
                else:
                    st.error(f"❌ Query failed: {exec_metadata['error']}")
        
        # Database connection status
        st.markdown("### Database Status")
        is_connected, connection_msg = st.session_state.executor.test_connection()
        if is_connected:
            st.success(f"✅ {connection_msg}")
        else:
            st.error(f"❌ {connection_msg}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666666; font-size: 0.9em;'>
            Built with ❤️ using Streamlit, spaCy, and Plotly | 
            <a href='https://github.com' target='_blank'>View Source Code</a>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()