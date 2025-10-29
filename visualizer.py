
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Optional, Dict, Any, Tuple

class DataVisualizer:
    """Create visualizations from query results."""
    
    def __init__(self):
        self.color_palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
    
    def analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze DataFrame structure to determine best visualization type."""
        if df.empty:
            return {'type': 'no_data', 'reason': 'Empty dataset'}
        
        analysis = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'numeric_columns': [],
            'categorical_columns': [],
            'date_columns': [],
            'has_aggregation': False,
            'suggested_chart': 'table'
        }
        
        # Analyze each column
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                analysis['numeric_columns'].append(col)
            elif df[col].dtype == 'object':
                # Check if it might be a date
                if self._is_date_column(df[col]):
                    analysis['date_columns'].append(col)
                else:
                    analysis['categorical_columns'].append(col)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                analysis['date_columns'].append(col)
        
        # Check for aggregation patterns
        if len(df) <= 20 and len(analysis['numeric_columns']) > 0:
            analysis['has_aggregation'] = True
        
        # Suggest chart type
        analysis['suggested_chart'] = self._suggest_chart_type(analysis)
        
        return analysis
    
    def _is_date_column(self, series: pd.Series) -> bool:
        """Check if a series contains date-like strings."""
        if series.empty:
            return False
        
        sample_values = series.dropna().head(10)
        date_count = 0
        
        for value in sample_values:
            try:
                pd.to_datetime(str(value))
                date_count += 1
            except:
                continue
        
        return date_count / len(sample_values) > 0.7
    
    def _suggest_chart_type(self, analysis: Dict[str, Any]) -> str:
        """Suggest the best chart type based on data analysis."""
        numeric_cols = len(analysis['numeric_columns'])
        categorical_cols = len(analysis['categorical_columns'])
        date_cols = len(analysis['date_columns'])
        row_count = analysis['row_count']
        
        # Time series
        if date_cols > 0 and numeric_cols > 0:
            return 'line'
        
        # Aggregated data with categories
        if categorical_cols == 1 and numeric_cols == 1 and row_count <= 20:
            if row_count <= 10:
                return 'pie'  # For small number of categories
            else:
                return 'bar'
        
        # Multiple categories or larger datasets
        if categorical_cols >= 1 and numeric_cols >= 1:
            return 'bar'
        
        # Two numeric columns
        if numeric_cols == 2 and row_count > 5:
            return 'scatter'
        
        # Multiple numeric columns
        if numeric_cols > 2:
            return 'correlation'
        
        # Default to table for complex data
        return 'table'
    
    def create_visualization(self, df: pd.DataFrame, chart_type: Optional[str] = None) -> Tuple[Optional[go.Figure], str]:
        """
        Create appropriate visualization for the DataFrame.
        
        Returns:
            tuple: (plotly_figure, chart_description)
        """
        if df.empty:
            return None, "No data to visualize"
        
        analysis = self.analyze_dataframe(df)
        
        if chart_type is None:
            chart_type = analysis['suggested_chart']
        
        try:
            if chart_type == 'bar':
                return self._create_bar_chart(df, analysis)
            elif chart_type == 'pie':
                return self._create_pie_chart(df, analysis)
            elif chart_type == 'line':
                return self._create_line_chart(df, analysis)
            elif chart_type == 'scatter':
                return self._create_scatter_plot(df, analysis)
            elif chart_type == 'correlation':
                return self._create_correlation_heatmap(df, analysis)
            elif chart_type == 'histogram':
                return self._create_histogram(df, analysis)
            else:
                return None, f"Showing data as table ({len(df)} rows)"
                
        except Exception as e:
            return None, f"Could not create visualization: {str(e)}"
    
    def _create_bar_chart(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> Tuple[go.Figure, str]:
        """Create a bar chart."""
        categorical_col = analysis['categorical_columns'][0] if analysis['categorical_columns'] else df.columns[0]
        numeric_col = analysis['numeric_columns'][0] if analysis['numeric_columns'] else df.columns[-1]
        
        # Aggregate data if needed
        if len(df) > 50:
            df_agg = df.groupby(categorical_col)[numeric_col].sum().reset_index()
        else:
            df_agg = df
        
        fig = px.bar(
            df_agg,
            x=categorical_col,
            y=numeric_col,
            title=f'{numeric_col} by {categorical_col}',
            color_discrete_sequence=self.color_palette
        )
        
        fig.update_layout(
            xaxis_title=categorical_col.replace('_', ' ').title(),
            yaxis_title=numeric_col.replace('_', ' ').title(),
            showlegend=False
        )
        
        return fig, f"Bar chart showing {numeric_col} by {categorical_col}"
    
    def _create_pie_chart(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> Tuple[go.Figure, str]:
        """Create a pie chart."""
        categorical_col = analysis['categorical_columns'][0] if analysis['categorical_columns'] else df.columns[0]
        numeric_col = analysis['numeric_columns'][0] if analysis['numeric_columns'] else None
        
        if numeric_col:
            # Use numeric values
            fig = px.pie(
                df,
                names=categorical_col,
                values=numeric_col,
                title=f'Distribution of {numeric_col} by {categorical_col}'
            )
        else:
            # Count occurrences
            value_counts = df[categorical_col].value_counts()
            fig = px.pie(
                names=value_counts.index,
                values=value_counts.values,
                title=f'Distribution of {categorical_col}'
            )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        return fig, f"Pie chart showing distribution by {categorical_col}"
    
    def _create_line_chart(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> Tuple[go.Figure, str]:
        """Create a line chart for time series data."""
        date_col = analysis['date_columns'][0]
        numeric_col = analysis['numeric_columns'][0]
        
        # Convert date column to datetime
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col])
        df_copy = df_copy.sort_values(date_col)
        
        fig = px.line(
            df_copy,
            x=date_col,
            y=numeric_col,
            title=f'{numeric_col} Over Time',
            markers=True
        )
        
        fig.update_layout(
            xaxis_title=date_col.replace('_', ' ').title(),
            yaxis_title=numeric_col.replace('_', ' ').title()
        )
        
        return fig, f"Time series chart of {numeric_col}"
    
    def _create_scatter_plot(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> Tuple[go.Figure, str]:
        """Create a scatter plot."""
        numeric_cols = analysis['numeric_columns'][:2]
        
        fig = px.scatter(
            df,
            x=numeric_cols[0],
            y=numeric_cols[1],
            title=f'{numeric_cols[1]} vs {numeric_cols[0]}',
            color_discrete_sequence=self.color_palette
        )
        
        fig.update_layout(
            xaxis_title=numeric_cols[0].replace('_', ' ').title(),
            yaxis_title=numeric_cols[1].replace('_', ' ').title()
        )
        
        return fig, f"Scatter plot of {numeric_cols[1]} vs {numeric_cols[0]}"
    
    def _create_correlation_heatmap(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> Tuple[go.Figure, str]:
        """Create a correlation heatmap for numeric columns."""
        numeric_cols = analysis['numeric_columns']
        correlation_matrix = df[numeric_cols].corr()
        
        fig = px.imshow(
            correlation_matrix,
            text_auto=True,
            aspect="auto",
            title="Correlation Matrix",
            color_continuous_scale='RdBu_r'
        )
        
        return fig, "Correlation heatmap of numeric columns"
    
    def _create_histogram(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> Tuple[go.Figure, str]:
        """Create a histogram."""
        numeric_col = analysis['numeric_columns'][0]
        
        fig = px.histogram(
            df,
            x=numeric_col,
            nbins=20,
            title=f'Distribution of {numeric_col}',
            color_discrete_sequence=self.color_palette
        )
        
        fig.update_layout(
            xaxis_title=numeric_col.replace('_', ' ').title(),
            yaxis_title='Count'
        )
        
        return fig, f"Histogram showing distribution of {numeric_col}"
    
    def create_summary_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create summary statistics for numeric columns."""
        if df.empty:
            return pd.DataFrame()
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return pd.DataFrame()
        
        summary = df[numeric_cols].describe()
        return summary
    
    def get_chart_recommendations(self, df: pd.DataFrame) -> Dict[str, str]:
        """Get recommendations for different chart types."""
        analysis = self.analyze_dataframe(df)
        recommendations = {}
        
        if analysis['numeric_columns'] and analysis['categorical_columns']:
            recommendations['bar'] = "Bar chart - Good for comparing categories"
            
            if len(df) <= 10:
                recommendations['pie'] = "Pie chart - Good for showing proportions (small datasets)"
        
        if analysis['date_columns'] and analysis['numeric_columns']:
            recommendations['line'] = "Line chart - Perfect for time series data"
        
        if len(analysis['numeric_columns']) >= 2:
            recommendations['scatter'] = "Scatter plot - Shows relationship between two variables"
            
        if len(analysis['numeric_columns']) > 2:
            recommendations['correlation'] = "Correlation matrix - Shows relationships between multiple variables"
        
        if analysis['numeric_columns']:
            recommendations['histogram'] = "Histogram - Shows distribution of values"
        
        return recommendations
    
    def format_table_display(self, df: pd.DataFrame, max_rows: int = 100) -> pd.DataFrame:
        """Format DataFrame for better table display."""
        if df.empty:
            return df
        
        display_df = df.copy()
        
        # Limit rows
        if len(display_df) > max_rows:
            display_df = display_df.head(max_rows)
        
        # Format numeric columns
        for col in display_df.select_dtypes(include=[np.number]).columns:
            if display_df[col].dtype == 'float64':
                display_df[col] = display_df[col].round(2)
        
        # Format column names
        display_df.columns = [col.replace('_', ' ').title() for col in display_df.columns]
        
        return display_df


# Example usage and testing
if __name__ == "__main__":
    # Create sample data for testing
    sample_data = {
        'city': ['Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Hyderabad'],
        'customer_count': [25, 30, 20, 15, 10],
        'total_sales': [125000, 180000, 95000, 75000, 60000]
    }
    
    df = pd.DataFrame(sample_data)
    
    visualizer = DataVisualizer()
    
    print("Testing Data Visualizer:")
    print("=" * 40)
    
    # Analyze data
    analysis = visualizer.analyze_dataframe(df)
    print(f"Data Analysis: {analysis}")
    
    # Get recommendations
    recommendations = visualizer.get_chart_recommendations(df)
    print(f"\nChart Recommendations:")
    for chart_type, description in recommendations.items():
        print(f"  {chart_type}: {description}")
    
    # Create visualization
    fig, description = visualizer.create_visualization(df, 'bar')
    print(f"\nVisualization: {description}")
    
    # Summary stats
    summary = visualizer.create_summary_stats(df)
    if not summary.empty:
        print(f"\nSummary Statistics:")
        print(summary)
