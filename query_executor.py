import sqlite3
import pandas as pd
import re
from typing import Tuple, Optional, Dict, Any, List

class QueryExecutor:
    """Safely execute SQL queries and return results as DataFrames."""
    
    def __init__(self, db_path: str = 'data/sample_db.sqlite'):
        self.db_path = db_path
        
        # Define allowed SQL operations for safety
        self.allowed_operations = [
            'SELECT', 'select', 'Select',
            'WITH', 'with', 'With'  # Allow CTEs
        ]
        
        # Dangerous operations to block
        self.blocked_operations = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
            'TRUNCATE', 'REPLACE', 'ATTACH', 'DETACH'
        ]
    
    def validate_query(self, sql_query: str) -> Tuple[bool, str]:
        """
        Validate SQL query for safety.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not sql_query or not sql_query.strip():
            return False, "Empty query"
        
        # Remove comments and normalize whitespace
        cleaned_query = re.sub(r'--.*$', '', sql_query, flags=re.MULTILINE)
        cleaned_query = re.sub(r'/\*.*?\*/', '', cleaned_query, flags=re.DOTALL)
        cleaned_query = ' '.join(cleaned_query.split())
        
        # Check for blocked operations
        query_upper = cleaned_query.upper()
        for blocked_op in self.blocked_operations:
            if blocked_op in query_upper:
                return False, f"Operation '{blocked_op}' is not allowed for safety reasons"
        
        # Ensure query starts with allowed operation
        first_word = cleaned_query.split()[0].upper() if cleaned_query.split() else ""
        if first_word not in [op.upper() for op in self.allowed_operations]:
            return False, f"Query must start with one of: {', '.join(self.allowed_operations)}"
        
        # Basic syntax checks
        if cleaned_query.count('(') != cleaned_query.count(')'):
            return False, "Mismatched parentheses"
        
        return True, "Valid query"
    
    def execute_query(self, sql_query: str) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
        """
        Execute SQL query and return results with metadata.
        
        Returns:
            tuple: (dataframe, metadata)
        """
        metadata = {
            'success': False,
            'error': None,
            'row_count': 0,
            'execution_time': 0,
            'query': sql_query
        }
        
        try:
            # Validate query first
            is_valid, validation_message = self.validate_query(sql_query)
            if not is_valid:
                metadata['error'] = validation_message
                return None, metadata
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # Execute query and measure time
            import time
            start_time = time.time()
            
            try:
                df = pd.read_sql_query(sql_query, conn)
                execution_time = time.time() - start_time
                
                metadata.update({
                    'success': True,
                    'row_count': len(df),
                    'execution_time': execution_time,
                    'columns': list(df.columns) if not df.empty else []
                })
                
                return df, metadata
                
            except pd.io.sql.DatabaseError as e:
                metadata['error'] = f"Database error: {str(e)}"
                return None, metadata
            except Exception as e:
                metadata['error'] = f"Execution error: {str(e)}"
                return None, metadata
            
            finally:
                conn.close()
        
        except sqlite3.Error as e:
            metadata['error'] = f"Database connection error: {str(e)}"
            return None, metadata
        except Exception as e:
            metadata['error'] = f"Unexpected error: {str(e)}"
            return None, metadata
    
    def get_table_info(self, table_name: str) -> Optional[pd.DataFrame]:
        """Get information about a specific table."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get table schema
            schema_query = f"PRAGMA table_info({table_name})"
            schema_df = pd.read_sql_query(schema_query, conn)
            
            conn.close()
            return schema_df
            
        except Exception as e:
            print(f"Error getting table info: {e}")
            return None
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> Optional[pd.DataFrame]:
        """Get sample data from a table."""
        try:
            sample_query = f"SELECT * FROM {table_name} LIMIT {limit}"
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(sample_query, conn)
            conn.close()
            return df
            
        except Exception as e:
            print(f"Error getting sample data: {e}")
            return None
    
    def get_database_schema(self) -> Dict[str, pd.DataFrame]:
        """Get schema information for all tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get all table names
            tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables_df = pd.read_sql_query(tables_query, conn)
            
            schema_info = {}
            for table_name in tables_df['name']:
                schema_query = f"PRAGMA table_info({table_name})"
                schema_df = pd.read_sql_query(schema_query, conn)
                schema_info[table_name] = schema_df
            
            conn.close()
            return schema_info
            
        except Exception as e:
            print(f"Error getting database schema: {e}")
            return {}
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test database connection."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return True, "Connection successful"
            else:
                return False, "Connection test failed"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_query_stats(self, sql_query: str) -> Dict[str, Any]:
        """Get statistics about the query without executing it."""
        stats = {
            'estimated_complexity': 'Low',
            'has_joins': False,
            'has_aggregation': False,
            'has_subqueries': False,
            'estimated_result_size': 'Small'
        }
        
        query_upper = sql_query.upper()
        
        # Check for JOINs
        if 'JOIN' in query_upper:
            stats['has_joins'] = True
            stats['estimated_complexity'] = 'Medium'
        
        # Check for aggregation functions
        agg_functions = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'GROUP BY']
        if any(func in query_upper for func in agg_functions):
            stats['has_aggregation'] = True
        
        # Check for subqueries
        if '(' in sql_query and 'SELECT' in sql_query[sql_query.find('('):]:
            stats['has_subqueries'] = True
            stats['estimated_complexity'] = 'High'
        
        # Estimate result size based on LIMIT
        if 'LIMIT' in query_upper:
            try:
                limit_match = re.search(r'LIMIT\s+(\d+)', query_upper)
                if limit_match:
                    limit_val = int(limit_match.group(1))
                    if limit_val <= 10:
                        stats['estimated_result_size'] = 'Very Small'
                    elif limit_val <= 100:
                        stats['estimated_result_size'] = 'Small'
                    elif limit_val <= 1000:
                        stats['estimated_result_size'] = 'Medium'
                    else:
                        stats['estimated_result_size'] = 'Large'
            except:
                pass
        else:
            stats['estimated_result_size'] = 'Unknown'
        
        return stats
    
    def suggest_optimizations(self, sql_query: str) -> List[str]:
        """Suggest query optimizations."""
        suggestions = []
        query_upper = sql_query.upper()
        
        # Suggest adding LIMIT if not present
        if 'LIMIT' not in query_upper and 'COUNT' not in query_upper:
            suggestions.append("Consider adding LIMIT clause to prevent large result sets")
        
        # Suggest specific column selection instead of SELECT *
        if 'SELECT *' in query_upper:
            suggestions.append("Consider selecting specific columns instead of SELECT * for better performance")
        
        # Suggest using indexes for WHERE clauses
        if 'WHERE' in query_upper:
            suggestions.append("Ensure WHERE clause columns are indexed for better performance")
        
        # Check for potential Cartesian products
        if 'JOIN' in query_upper and 'ON' not in query_upper:
            suggestions.append("Warning: JOIN without ON clause may result in Cartesian product")
        
        return suggestions
    
    def format_result_summary(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
        """Create a formatted summary of query results."""
        if df is None:
            return f"Query failed: {metadata.get('error', 'Unknown error')}"
        
        summary = []
        summary.append(f"Query executed successfully")
        summary.append(f"Rows returned: {metadata['row_count']}")
        summary.append(f"Columns: {len(metadata.get('columns', []))}")
        summary.append(f"Execution time: {metadata['execution_time']:.3f} seconds")
        
        if not df.empty:
            summary.append(f"Column names: {', '.join(df.columns.tolist())}")
        
        return "\n".join(summary)


# Example usage and testing
if __name__ == "__main__":
    # Test the query executor
    executor = QueryExecutor()
    
    # Test connection
    is_connected, connection_msg = executor.test_connection()
    print(f"Database connection: {connection_msg}")
    
    if is_connected:
        # Test sample queries
        test_queries = [
            "SELECT * FROM customers LIMIT 5",
            "SELECT city, COUNT(*) as customer_count FROM customers GROUP BY city",
            "SELECT customers.name, orders.total_amount FROM customers LEFT JOIN orders ON customers.customer_id = orders.customer_id LIMIT 10",
            "DROP TABLE customers",  # This should be blocked
        ]
        
        print("\nTesting queries:")
        print("=" * 50)
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            
            # Get query stats
            stats = executor.get_query_stats(query)
            print(f"Complexity: {stats['estimated_complexity']}")
            print(f"Has JOINs: {stats['has_joins']}")
            
            # Execute query
            df, metadata = executor.execute_query(query)
            
            if metadata['success']:
                print(f"✓ Success - {metadata['row_count']} rows returned")
                if df is not None and not df.empty:
                    print(df.head())
            else:
                print(f"✗ Failed - {metadata['error']}")
            
            # Get suggestions
            suggestions = executor.suggest_optimizations(query)
            if suggestions:
                print("Suggestions:")
                for suggestion in suggestions:
                    print(f"  • {suggestion}")
            
            print("-" * 30)