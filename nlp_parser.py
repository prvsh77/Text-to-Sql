
import re
import spacy
from typing import Dict, List, Tuple, Optional

class TextToSQLParser:
    """Convert natural language queries to SQL statements."""
    
    def __init__(self):
        # Try to load spacy model, fallback to basic parsing if not available
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.use_spacy = True
        except OSError:
            print("Warning: spaCy model not found. Using basic rule-based parsing.")
            self.use_spacy = False
            self.nlp = None
        
        # Define table and column mappings
        self.schema = {
            'customers': ['customer_id', 'name', 'email', 'city', 'state', 'phone', 'created_date'],
            'products': ['product_id', 'name', 'category', 'price', 'stock_quantity', 'description'],
            'orders': ['order_id', 'customer_id', 'order_date', 'total_amount', 'status', 'shipping_city'],
            'order_items': ['item_id', 'order_id', 'product_id', 'quantity', 'unit_price']
        }
        
        # Keywords for different query types
        self.query_patterns = {
            'select': ['show', 'list', 'get', 'find', 'display', 'retrieve'],
            'aggregate': ['total', 'sum', 'count', 'average', 'avg', 'max', 'min'],
            'filter': ['from', 'in', 'where', 'with', 'having'],
            'time': ['after', 'before', 'between', 'since', 'until'],
            'group': ['by', 'per', 'each', 'grouped']
        }
        
        # Entity mappings
        self.entity_mappings = {
            'customers': ['customer', 'customers', 'client', 'clients', 'user', 'users'],
            'products': ['product', 'products', 'item', 'items'],
            'orders': ['order', 'orders', 'purchase', 'purchases', 'sale', 'sales'],
            'order_items': ['order item', 'order items', 'item details']
        }
        
        # Common column aliases
        self.column_aliases = {
            'customer name': 'customers.name',
            'product name': 'products.name',
            'price': 'products.price',
            'total': 'orders.total_amount',
            'amount': 'orders.total_amount',
            'date': 'orders.order_date',
            'city': 'customers.city',
            'category': 'products.category',
            'status': 'orders.status',
            'quantity': 'order_items.quantity'
        }
    
    def preprocess_query(self, query: str) -> str:
        """Clean and normalize the input query."""
        query = query.lower().strip()
        # Handle common variations
        query = re.sub(r'\bshowing\b', 'show', query)
        query = re.sub(r'\blisting\b', 'list', query)
        query = re.sub(r'\bgetting\b', 'get', query)
        return query
    
    def extract_entities_spacy(self, query: str) -> Dict:
        """Extract entities using spaCy NLP."""
        doc = self.nlp(query)
        entities = {
            'locations': [],
            'dates': [],
            'numbers': [],
            'organizations': []
        }
        
        for ent in doc.ents:
            if ent.label_ in ['GPE', 'LOC']:  # Geographic/Location entities
                entities['locations'].append(ent.text)
            elif ent.label_ in ['DATE', 'TIME']:
                entities['dates'].append(ent.text)
            elif ent.label_ in ['MONEY', 'QUANTITY', 'CARDINAL']:
                entities['numbers'].append(ent.text)
            elif ent.label_ in ['ORG']:
                entities['organizations'].append(ent.text)
        
        return entities
    
    def extract_entities_basic(self, query: str) -> Dict:
        """Basic entity extraction using regex patterns."""
        entities = {
            'locations': [],
            'dates': [],
            'numbers': [],
            'organizations': []
        }
        
        # Extract dates (simple patterns)
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, query)
            entities['dates'].extend(matches)
        
        # Extract numbers
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        entities['numbers'].extend(re.findall(number_pattern, query))
        
        # Extract potential city names (capitalized words)
        city_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'
        potential_cities = re.findall(city_pattern, query)
        entities['locations'].extend(potential_cities)
        
        return entities
    
    def identify_table(self, query: str) -> str:
        """Identify the main table based on entity mentions."""
        query_lower = query.lower()
        
        for table, aliases in self.entity_mappings.items():
            for alias in aliases:
                if alias in query_lower:
                    return table
        
        # Default to customers if no specific table identified
        return 'customers'
    
    def identify_query_type(self, query: str) -> str:
        """Identify the type of query (select, aggregate, etc.)."""
        query_lower = query.lower()
        
        # Check for aggregation keywords
        for agg_word in self.query_patterns['aggregate']:
            if agg_word in query_lower:
                return 'aggregate'
        
        # Default to select
        return 'select'
    
    def build_select_query(self, query: str, main_table: str, entities: Dict) -> str:
        """Build a SELECT query based on parsed information."""
        query_lower = query.lower()
        
        # Determine columns to select
        if 'all' in query_lower or 'everything' in query_lower:
            select_clause = f"{main_table}.*"
        else:
            # Try to identify specific columns mentioned
            columns = []
            for alias, full_col in self.column_aliases.items():
                if alias in query_lower:
                    columns.append(full_col)
            
            if not columns:
                select_clause = f"{main_table}.*"
            else:
                select_clause = ", ".join(columns)
        
        # Build FROM clause with potential JOINs
        from_clause = main_table
        joins = []
        
        if main_table == 'customers' and ('order' in query_lower or 'purchase' in query_lower):
            joins.append("LEFT JOIN orders ON customers.customer_id = orders.customer_id")
        elif main_table == 'orders':
            joins.append("LEFT JOIN customers ON orders.customer_id = customers.customer_id")
            if 'product' in query_lower or 'item' in query_lower:
                joins.append("LEFT JOIN order_items ON orders.order_id = order_items.order_id")
                joins.append("LEFT JOIN products ON order_items.product_id = products.product_id")
        
        if joins:
            from_clause = f"{main_table} " + " ".join(joins)
        
        # Build WHERE clause
        where_conditions = []
        
        # Location filters
        if entities['locations']:
            for location in entities['locations']:
                # Check if it's a known city
                known_cities = ['bangalore', 'mumbai', 'delhi', 'chennai', 'hyderabad', 'pune', 'kolkata', 'ahmedabad']
                if location.lower() in known_cities:
                    where_conditions.append(f"customers.city = '{location}'")
        
        # Date filters
        if entities['dates']:
            for date in entities['dates']:
                if 'after' in query_lower:
                    where_conditions.append(f"orders.order_date > '{date}'")
                elif 'before' in query_lower:
                    where_conditions.append(f"orders.order_date < '{date}'")
                else:
                    where_conditions.append(f"orders.order_date = '{date}'")
        
        # Status filters
        if 'completed' in query_lower:
            where_conditions.append("orders.status = 'Completed'")
        elif 'processing' in query_lower:
            where_conditions.append("orders.status = 'Processing'")
        elif 'shipped' in query_lower:
            where_conditions.append("orders.status = 'Shipped'")
        elif 'delivered' in query_lower:
            where_conditions.append("orders.status = 'Delivered'")
        
        # Build final query
        sql_query = f"SELECT {select_clause} FROM {from_clause}"
        
        if where_conditions:
            sql_query += " WHERE " + " AND ".join(where_conditions)
        
        return sql_query
    
    def build_aggregate_query(self, query: str, main_table: str, entities: Dict) -> str:
        """Build an aggregation query (COUNT, SUM, AVG, etc.)."""
        query_lower = query.lower()
        
        # Determine aggregation function
        agg_function = "COUNT(*)"
        if 'total' in query_lower or 'sum' in query_lower:
            if 'sales' in query_lower or 'amount' in query_lower:
                agg_function = "SUM(orders.total_amount)"
            elif 'quantity' in query_lower:
                agg_function = "SUM(order_items.quantity)"
        elif 'average' in query_lower or 'avg' in query_lower:
            agg_function = "AVG(orders.total_amount)"
        elif 'count' in query_lower:
            if 'customer' in query_lower:
                agg_function = "COUNT(DISTINCT customers.customer_id)"
            elif 'order' in query_lower:
                agg_function = "COUNT(DISTINCT orders.order_id)"
            else:
                agg_function = "COUNT(*)"
        
        # Determine GROUP BY
        group_by = None
        if 'by city' in query_lower or 'per city' in query_lower:
            group_by = "customers.city"
        elif 'by category' in query_lower or 'per category' in query_lower:
            group_by = "products.category"
        elif 'by status' in query_lower or 'per status' in query_lower:
            group_by = "orders.status"
        elif 'by customer' in query_lower or 'per customer' in query_lower:
            group_by = "customers.name"
        
        # Build FROM clause with JOINs
        from_clause = main_table
        if group_by and 'customers.' in group_by and main_table != 'customers':
            from_clause = "orders LEFT JOIN customers ON orders.customer_id = customers.customer_id"
        elif group_by and 'products.' in group_by:
            from_clause = "order_items LEFT JOIN products ON order_items.product_id = products.product_id"
            if 'orders.' in agg_function:
                from_clause += " LEFT JOIN orders ON order_items.order_id = orders.order_id"
        
        # Build query
        if group_by:
            sql_query = f"SELECT {group_by}, {agg_function} as result FROM {from_clause}"
            sql_query += f" GROUP BY {group_by}"
        else:
            sql_query = f"SELECT {agg_function} as result FROM {from_clause}"
        
        # Add WHERE conditions if any
        where_conditions = []
        if entities['locations']:
            for location in entities['locations']:
                if location.lower() in ['bangalore', 'mumbai', 'delhi', 'chennai', 'hyderabad', 'pune', 'kolkata', 'ahmedabad']:
                    where_conditions.append(f"customers.city = '{location}'")
        
        if where_conditions:
            if 'WHERE' not in sql_query:
                sql_query += " WHERE " + " AND ".join(where_conditions)
        
        return sql_query
    
    def parse_query(self, natural_language_query: str) -> Tuple[str, Dict]:
        """
        Convert natural language query to SQL.
        
        Returns:
            tuple: (sql_query, metadata)
        """
        try:
            # Preprocess query
            processed_query = self.preprocess_query(natural_language_query)
            
            # Extract entities
            if self.use_spacy:
                entities = self.extract_entities_spacy(processed_query)
            else:
                entities = self.extract_entities_basic(processed_query)
            
            # Identify main table and query type
            main_table = self.identify_table(processed_query)
            query_type = self.identify_query_type(processed_query)
            
            # Build SQL query based on type
            if query_type == 'aggregate':
                sql_query = self.build_aggregate_query(processed_query, main_table, entities)
            else:
                sql_query = self.build_select_query(processed_query, main_table, entities)
            
            # Add LIMIT if not an aggregation
            if query_type != 'aggregate' and 'LIMIT' not in sql_query.upper():
                sql_query += " LIMIT 100"
            
            metadata = {
                'original_query': natural_language_query,
                'processed_query': processed_query,
                'entities': entities,
                'main_table': main_table,
                'query_type': query_type,
                'confidence': self._calculate_confidence(processed_query, entities)
            }
            
            return sql_query, metadata
            
        except Exception as e:
            # Fallback to simple SELECT query
            fallback_sql = "SELECT customers.* FROM customers LIMIT 10"
            metadata = {
                'original_query': natural_language_query,
                'error': str(e),
                'confidence': 0.3
            }
            return fallback_sql, metadata
    
    def _calculate_confidence(self, query: str, entities: Dict) -> float:
        """Calculate confidence score for the parsed query."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if we found entities
        if any(entities.values()):
            confidence += 0.2
        
        # Increase confidence if query contains known keywords
        for pattern_type, keywords in self.query_patterns.items():
            if any(keyword in query for keyword in keywords):
                confidence += 0.1
        
        # Increase confidence if we identified table entities
        query_lower = query.lower()
        for table, aliases in self.entity_mappings.items():
            if any(alias in query_lower for alias in aliases):
                confidence += 0.15
        
        return min(confidence, 1.0)
    
    def get_query_suggestions(self) -> List[str]:
        """Return sample queries that the parser can handle."""
        return [
            "Show all customers from Bangalore",
            "List orders placed after 2024-01-01",
            "Count total orders",
            "Show total sales by city",
            "Find customers with orders",
            "List products in Electronics category",
            "Show average order amount",
            "Count customers per city",
            "List completed orders",
            "Show products with price greater than 10000",
            "Display recent orders",
            "Show customer details for orders",
            "List top selling products",
            "Show orders by status",
            "Find customers from Mumbai"
        ]

# Example usage and testing
if __name__ == "__main__":
    parser = TextToSQLParser()
    
    # Test queries
    test_queries = [
        "Show all customers from Bangalore",
        "List orders placed after 2024-01-01",
        "Count total orders",
        "Show total sales by city",
        "Find all products in Electronics category",
        "Show average order amount per customer"
    ]
    
    print("Testing Text-to-SQL Parser:")
    print("=" * 50)
    
    for query in test_queries:
        sql, metadata = parser.parse_query(query)
        print(f"\nNatural Language: {query}")
        print(f"Generated SQL: {sql}")
        print(f"Confidence: {metadata['confidence']:.2f}")
        print(f"Main Table: {metadata.get('main_table', 'Unknown')}")
        print("-" * 30)
