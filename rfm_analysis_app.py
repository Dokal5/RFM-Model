# IMPORT IMPORTANT PACKAGES
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import streamlit as st

# SET PLOTLY DEFAULT TEMPLATE
pio.templates.default = "plotly_white"

# STREAMLIT HEADER
st.title('RFM Customer Segmentation Analysis')
st.write("This app analyzes customer data using the RFM (Recency, Frequency, Monetary) framework.")

# FILE UPLOAD
uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    st.write("Data Preview:", data.head())

    # Convert 'PurchaseDate' to datetime
    data['PurchaseDate'] = pd.to_datetime(data['PurchaseDate'])

    # Calculate Recency using today's date
    data['Recency'] = (pd.to_datetime(datetime.now()) - data['PurchaseDate']).dt.days

    # Calculate Frequency and Monetary Value
    frequency_data = data.groupby('CustomerID')['OrderID'].count().reset_index()
    frequency_data.rename(columns={'OrderID': 'Frequency'}, inplace=True)
    monetary_data = data.groupby('CustomerID')['TransactionAmount'].sum().reset_index()
    monetary_data.rename(columns={'TransactionAmount': 'MonetaryValue'}, inplace=True)
    
    # Merge Frequency and Monetary data back into the original dataframe
    data = data.merge(frequency_data, on='CustomerID', how='left')
    data = data.merge(monetary_data, on='CustomerID', how='left')

    # Define scoring criteria for each RFM value using qcut for a balanced distribution
    recency_scores = [5, 4, 3, 2, 1]
    frequency_scores = [1, 2, 3, 4, 5]
    monetary_scores = [1, 2, 3, 4, 5]

    # Assign RFM scores using qcut for better distribution
    data['RecencyScore'] = pd.qcut(data['Recency'], q=5, labels=recency_scores).astype(int)
    data['FrequencyScore'] = pd.qcut(data['Frequency'], q=5, labels=frequency_scores).astype(int)
    data['MonetaryScore'] = pd.qcut(data['MonetaryValue'], q=5, labels=monetary_scores).astype(int)

    # Calculate the final RFM Score
    data['RFM_Score'] = data['RecencyScore'] + data['FrequencyScore'] + data['MonetaryScore']

    # Create RFM segments based on the RFM score
    segment_labels = ['Low-Value', 'Mid-Value', 'High-Value']
    data['Value Segment'] = pd.qcut(data['RFM_Score'], q=3, labels=segment_labels)

    # Assign RFM Customer Segments
    data['RFM Customer Segments'] = ''
    data.loc[data['RFM_Score'] >= 9, 'RFM Customer Segments'] = 'Champions'
    data.loc[(data['RFM_Score'] >= 6) & (data['RFM_Score'] < 9), 'RFM Customer Segments'] = 'Potential Loyalists'
    data.loc[(data['RFM_Score'] >= 5) & (data['RFM_Score'] < 6), 'RFM Customer Segments'] = 'At Risk Customers'
    data.loc[(data['RFM_Score'] >= 4) & (data['RFM_Score'] < 5), 'RFM Customer Segments'] = "Can't Lose"
    data.loc[(data['RFM_Score'] < 4), 'RFM Customer Segments'] = "Lost"

    # Show the RFM segmented data
    st.write("RFM Segmented Data:", data[['CustomerID', 'RFM Customer Segments']])

    # RFM Segment Distribution
    segment_counts = data['Value Segment'].value_counts().reset_index()
    segment_counts.columns = ['Value Segment', 'Count']

    # Create and show the bar chart for segment distribution
    fig_segment_dist = px.bar(segment_counts, x='Value Segment', y='Count',
                              color='Value Segment', color_discrete_sequence=px.colors.qualitative.Pastel,
                              title='RFM Value Segment Distribution')
    fig_segment_dist.update_layout(xaxis_title='RFM Value Segment', yaxis_title='Count', showlegend=False)
    st.plotly_chart(fig_segment_dist)

    # Treemap for RFM Customer Segments by Value
    segment_product_counts = data.groupby(['Value Segment', 'RFM Customer Segments']).size().reset_index(name='Count')
    fig_treemap_segment_product = px.treemap(segment_product_counts,
                                             path=['Value Segment', 'RFM Customer Segments'],
                                             values='Count',
                                             color='Value Segment', color_discrete_sequence=px.colors.qualitative.Pastel,
                                             title='RFM Customer Segments by Value')
    st.plotly_chart(fig_treemap_segment_product)

    # Filter the data to include only the customers in the Champions segment
    champions_segment = data[data['RFM Customer Segments'] == 'Champions']
    fig_box = go.Figure()
    fig_box.add_trace(go.Box(y=champions_segment['RecencyScore'], name='Recency'))
    fig_box.add_trace(go.Box(y=champions_segment['FrequencyScore'], name='Frequency'))
    fig_box.add_trace(go.Box(y=champions_segment['MonetaryScore'], name='Monetary'))

    fig_box.update_layout(title='Distribution of RFM Values within Champions Segment',
                          yaxis_title='RFM Value',
                          showlegend=True)
    st.plotly_chart(fig_box)

    # Correlation Matrix of Champions
    correlation_matrix = champions_segment[['RecencyScore', 'FrequencyScore', 'MonetaryScore']].corr()
    fig_heatmap = go.Figure(data=go.Heatmap(
                       z=correlation_matrix.values,
                       x=correlation_matrix.columns,
                       y=correlation_matrix.columns,
                       colorscale='RdBu',
                       colorbar=dict(title='Correlation')))
    fig_heatmap.update_layout(title='Correlation Matrix of RFM Values within Champions Segment')
    st.plotly_chart(fig_heatmap)

    # Comparison of RFM Segments with grouped bar chart
    segment_scores = data.groupby('RFM Customer Segments')[['RecencyScore', 'FrequencyScore', 'MonetaryScore']].mean().reset_index()
    fig_segment_scores = go.Figure()

    # Add bars for each score type
    for score, color in zip(['RecencyScore', 'FrequencyScore', 'MonetaryScore'], 
                            ['rgb(158,202,225)', 'rgb(94,158,217)', 'rgb(32,102,148)']):
        fig_segment_scores.add_trace(go.Bar(
            x=segment_scores['RFM Customer Segments'],
            y=segment_scores[score],
            name=score,
            marker_color=color
        ))

    # Update layout of the bar chart
    fig_segment_scores.update_layout(
        title='Comparison of RFM Segments based on Recency, Frequency, and Monetary Scores',
        xaxis_title='RFM Segments',
        yaxis_title='Score',
        barmode='group',
        showlegend=True
    )
    st.plotly_chart(fig_segment_scores)

else:
    st.write("Please upload a CSV file to analyze the RFM data.")