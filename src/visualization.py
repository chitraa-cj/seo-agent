import pandas as pd
import matplotlib.pyplot as plt

def visualize_crawler_comparison(bs_result, fc_result):
    """Create visualization comparing the two crawlers"""
    if 'error' in bs_result and 'error' in fc_result:
        return None, None
    
    # Prepare data for visualization
    metrics = ['word_count', 'link_count', 'image_count', 'images_with_alt']
    bs_values = [bs_result.get(metric, 0) for metric in metrics]
    fc_values = [fc_result.get(metric, 0) for metric in metrics]
    
    # Create DataFrame for the visualization
    df = pd.DataFrame({
        'Metric': ['Word Count', 'Link Count', 'Image Count', 'Images with Alt'],
        'BeautifulSoup': bs_values,
        'Firecrawl': fc_values
    })
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(metrics))
    width = 0.35
    
    # Create the bars
    ax.bar([i - width/2 for i in x], bs_values, width, label='BeautifulSoup')
    ax.bar([i + width/2 for i in x], fc_values, width, label='Firecrawl')
    
    # Add labels and title
    ax.set_ylabel('Count')
    ax.set_title('Crawler Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(['Word Count', 'Link Count', 'Image Count', 'Images with Alt'])
    ax.legend()
    
    # Add execution time comparison if available
    bs_time = getattr(bs_result, 'execution_time', 0) if hasattr(bs_result, 'execution_time') else bs_result.get('execution_time', 0)
    fc_time = getattr(fc_result, 'execution_time', 0) if hasattr(fc_result, 'execution_time') else fc_result.get('execution_time', 0)
    
    if bs_time and fc_time:
        time_fig, time_ax = plt.subplots(figsize=(8, 4))
        time_ax.bar(['BeautifulSoup', 'Firecrawl'], [bs_time, fc_time])
        time_ax.set_ylabel('Execution Time (seconds)')
        time_ax.set_title('Crawler Performance Comparison')
        
        return fig, time_fig
    
    return fig, None