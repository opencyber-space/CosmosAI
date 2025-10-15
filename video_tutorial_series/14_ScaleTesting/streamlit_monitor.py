#!/usr/bin/env python3
"""
Streamlit-based Time Series Data Visualization Tool for Block Monitoring

This tool reads config.yaml to extract block names, fetches metrics from API endpoints,
and displays configurable time series graph        if fig.data:  # Only update layout if we have data
            fig.update_layout(
                title=dict(
                    text=f'{metric_config.name} - {block_name}',
                    x=0.5,
                    xanchor='center',
                    font=dict(size=18, family="Arial, sans-serif"),
                    pad=dict(t=20, b=20)
                ),
                xaxis_title='Time',
                yaxis_title='Value',
                height=550,
                showlegend=True,
                template='plotly_white',
                margin=dict(l=60, r=200, t=100, b=60),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.95,
                    xanchor="left",
                    x=1.02,
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1,
                    font=dict(size=11)
                ),
                hovermode='x unified',
                hoverlabel=dict(
                    bgcolor="white",
                    bordercolor="black",
                    font_size=12,
                    font_family="Arial"
                )
            )
            
            # Update hover template for better readability with full text
            for trace in fig.data:
                trace.update(
                    hovertemplate=f"<b>{trace.name}</b><br>" +
                                  "Time: %{x}<br>" +
                                  "Value: %{y:,.4f}<br>" +
                                  "<extra></extra>",
                    hoverlabel=dict(
                        bgcolor="white",
                        bordercolor="black",
                        font_size=12,
                        font_family="Arial",
                        namelength=-1  # Show full trace name
                    )
                )
            
            # Update hover template for better readability
            for trace in fig.data:
                trace.update(
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                                  "Time: %{x}<br>" +
                                  "Value: %{y:,.2f}<br>" +
                                  "<extra></extra>"
                )e updates.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import yaml
import time
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
from pathlib import Path
import pytz

# Only import here to avoid circular import
from db_logger import DatabaseLogger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetricConfig:
    """Configuration for a metric to be displayed."""
    name: str
    keys: List[str]  # List of dot-notation keys like ['queue_length.average_15m']
    chart_type: str = "line"  # line, bar, area
    color_scheme: str = "viridis"

class BlockMonitor:
    """Main class for monitoring block metrics and creating visualizations."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the monitor with configuration."""
        self.config_path = config_path
        self.config = None
        self.base_url = "http://MANAGEMENTMASTER:30201/block/"
        self.data_history = {}  # Store historical data for time series
        self.load_config()

        # Get DB config from loaded config
        db_config = self.config.get('database', {})
        if not db_config.get('enabled', False):
            return

        timezone_str = self.config.get('logging', {}).get('timezone', 'Asia/Kolkata')
        self.ist_tz = pytz.timezone(timezone_str)
        self.db_logger = DatabaseLogger(db_config, timezone_str=self.ist_tz.zone)
        # --- Add IST timezone support ---
        # timezone_str = None
        # try:
        #     # Try to get from config.yaml
        #     with open(self.config_path, 'r') as file:
        #         config_yaml = yaml.safe_load(file)
        #         timezone_str = config_yaml.get('logging', {}).get('timezone', 'Asia/Kolkata')
        # except Exception:
        #     timezone_str = 'Asia/Kolkata'
        

    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            st.error(f"Error loading config: {e}")
    
    def get_block_names(self) -> List[str]:
        """Extract block names from config.yaml."""
        if not self.config or 'blocks' not in self.config:
            return []
        
        block_names = list(self.config['blocks'].keys())
        logger.info(f"Found blocks: {block_names}")
        return block_names
    
    def fetch_block_data(self, block_name: str) -> Optional[Dict[str, Any]]:
        """Fetch data for a specific block from the API endpoint."""
        try:
            url = f"{self.base_url}{block_name}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success') and 'data' in data:
                return data['data'][0] if data['data'] else None
            else:
                logger.warning(f"No data returned for block {block_name}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data for {block_name}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON for {block_name}: {e}")
            return None
    
    def extract_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """Extract value from nested dictionary using dot notation."""
        keys = key_path.split('.')
        current = data
        
        try:
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
        except (KeyError, TypeError):
            return None
    
    def backup_and_evict_data(self, block_name: str):
        """Backup evicted data points to DB before slicing history lists."""
        
        
        
        max_points = st.session_state.streamlit_config.get('data_history', {}).get('max_data_points', 1000)
        # Backup and evict timestamps and executor_data
        timestamps = self.data_history[block_name]['timestamps']
        executor_data = self.data_history[block_name]['executor_data']
        num_to_evict = len(timestamps) - max_points
        if num_to_evict > 0:
            for i in range(num_to_evict):
                ts = timestamps[i]
                exec_data = executor_data[i] if i < len(executor_data) else {}
                log_entry = {
                    'block_name': block_name,
                    'timestamp': ts,
                    'executor_data': exec_data
                }
                self.db_logger.log_streamlit_history(log_entry)
        # Backup and evict instance_data
        for instance_id, instance_history in self.data_history[block_name]['instance_data'].items():
            num_to_evict_inst = len(instance_history) - max_points
            if num_to_evict_inst > 0:
                for j in range(num_to_evict_inst):
                    entry = instance_history[j]
                    log_entry = {
                        'block_name': block_name,
                        'instance_id': instance_id,
                        'timestamp': entry['timestamp'],
                        'instance_data': entry['data']
                    }
                    self.db_logger.log_streamlit_history(log_entry)
        # Now slice lists as before
        self.data_history[block_name]['timestamps'] = timestamps[-max_points:]
        self.data_history[block_name]['executor_data'] = executor_data[-max_points:]
        for instance_id in self.data_history[block_name]['instance_data']:
            self.data_history[block_name]['instance_data'][instance_id] = self.data_history[block_name]['instance_data'][instance_id][-max_points:]

    def update_data_history(self, block_name: str, data: Dict[str, Any]) -> None:
        """Update historical data storage with new measurements."""
        timestamp = datetime.now(self.ist_tz)
        if block_name not in self.data_history:
            self.data_history[block_name] = {
                'timestamps': [],
                'executor_data': [],
                'instance_data': {}
            }
        # Store timestamp for block (for executor/global use)
        self.data_history[block_name]['timestamps'].append(timestamp)
        # Process instances
        instances = data.get('instances', [])
        for instance in instances:
            instance_id = instance.get('instanceId', 'unknown')
            if instance_id == 'executor':
                executor_metrics = {
                    'tasks_processed_total': self.extract_nested_value(
                        instance, 'tasks_processed.tasks_processed_total'
                    )
                }
                self.data_history[block_name]['executor_data'].append(executor_metrics)
            else:
                # Store per-instance (timestamp, instance) pairs
                if instance_id not in self.data_history[block_name]['instance_data']:
                    self.data_history[block_name]['instance_data'][instance_id] = []
                self.data_history[block_name]['instance_data'][instance_id].append({'timestamp': timestamp, 'data': instance})
        # Backup and evict if needed
        max_points = st.session_state.streamlit_config.get('data_history', {}).get('max_data_points', 1000)
        if len(self.data_history[block_name]['timestamps']) > max_points or any(len(hist) > max_points for hist in self.data_history[block_name]['instance_data'].values()):
            self.backup_and_evict_data(block_name)
    
    def create_executor_chart(self, block_name: str) -> Optional[go.Figure]:
        """Create chart for executor tasks_processed_total."""
        if (block_name not in self.data_history or 
            not self.data_history[block_name]['executor_data']):
            return None
        history = self.data_history[block_name]
        timestamps = history['timestamps']
        executor_data = history['executor_data']
        # Align lengths to avoid ValueError
        min_len = min(len(timestamps), len(executor_data))
        if min_len == 0:
            return None
        timestamps = timestamps[-min_len:]
        executor_data = executor_data[-min_len:]
        values = [data.get('tasks_processed_total', 0) for data in executor_data]
        df = pd.DataFrame({
            'timestamp': timestamps,
            'tasks_processed_total': values
        })
        
        # Create plotly figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['tasks_processed_total'],
            mode='lines+markers',
            name='Tasks Processed Total',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4),
            hovertemplate="<b>%{fullData.name}</b><br>" +
                          "Time: %{x}<br>" +
                          "Tasks: %{y:,.0f}<br>" +
                          "<extra></extra>"
        ))
        
        fig.update_layout(
            title=dict(
                text=f'Tasks Processed - {block_name}',
                x=0.5,
                xanchor='center',
                font=dict(size=16),
                y=0.95
            ),
            xaxis_title='Time',
            yaxis_title='Tasks Processed Total',
            hovermode='x unified',
            template='plotly_white',
            margin=dict(t=120, b=100, l=60, r=60),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.2)",
                borderwidth=1
            ),
            height=550
        )
        
        return fig
    
    def create_metric_key_chart(self, block_name: str, metric_config: MetricConfig, metric_key: str) -> Optional[go.Figure]:
        """Create a chart for a single metric key across all instances, using per-instance timestamps."""
        if (block_name not in self.data_history or 
            not self.data_history[block_name]['instance_data']):
            return None
        history = self.data_history[block_name]
        instance_data = history['instance_data']
        fig = go.Figure()
        for instance_id, instance_history in instance_data.items():
            if not instance_history:
                continue
            values = []
            valid_timestamps = []
            for entry in instance_history:
                ts = entry['timestamp']
                # ts is already in IST
                instance_snapshot = entry['data']
                value = self.extract_nested_value(instance_snapshot, metric_key)
                if value is not None:
                    values.append(float(value))
                    valid_timestamps.append(ts)
            if values:
                trace_name = f"{instance_id} - {metric_key}"
                trace = go.Scatter(
                    x=valid_timestamps,
                    y=values,
                    mode='lines+markers',
                    name=trace_name,
                    line=dict(width=2),
                    marker=dict(size=4),
                    hovertemplate="<b>%{fullData.name}</b><br>Time: %{x}<br>Value: %{y:,.4f}<br><extra></extra>",
                    legendgroup=metric_key,
                    customdata=[metric_key] * len(values)
                )
                fig.add_trace(trace)
        if fig.data:
            fig.update_layout(
                title=dict(
                    text=f'{metric_config.name} - {metric_key} - {block_name}',
                    x=0.5,
                    xanchor='center',
                    font=dict(size=16),
                    y=0.95
                ),
                xaxis_title='Time',
                yaxis_title='Value',
                hovermode='x unified',
                template='plotly_white',
                margin=dict(t=120, b=100, l=60, r=60),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1
                ),
                height=550,
                hoverlabel=dict(
                    bgcolor="white",
                    bordercolor="black",
                    font_size=12,
                    font_family="Arial"
                )
            )
        return fig if fig.data else None
    
    def add_hover_synchronization(self, fig: go.Figure, metric_config: MetricConfig) -> go.Figure:
        """Add hover synchronization to highlight only the hovered metric key for all instances."""
        if not fig.data:
            return fig
        # Group traces by metric key
        metric_groups = {}
        for trace in fig.data:
            trace_name = trace.name
            # Extract metric key from trace name (format: "instance_id - metric_key")
            if ' - ' in trace_name:
                metric_key = trace_name.split(' - ', 1)[1]
                if metric_key not in metric_groups:
                    metric_groups[metric_key] = []
                metric_groups[metric_key].append(trace)
        # Set up hover effects by assigning same color to same metric keys
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        color_index = 0
        for metric_key, traces in metric_groups.items():
            color = colors[color_index % len(colors)]
            for trace in traces:
                # Only show the metric key and value for this trace (instance)
                instance_id = trace.name.split(' - ', 1)[0]
                trace.update(
                    line=dict(color=color, width=2),
                    marker=dict(color=color, size=4),
                    hovertemplate=f"<b>{instance_id}</b><br>" +
                                  f"{metric_key}: <b>%{{y:,.4f}}</b><br>" +
                                  "Time: %{x}<br>" +
                                  "<extra></extra>",
                    hoverlabel=dict(
                        bgcolor=color,
                        bordercolor="white",
                        font_color="white",
                        font_size=12,
                        font_family="Arial"
                    )
                )
            color_index += 1
        # Update layout to enhance hover experience
        fig.update_layout(
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="black",
                font_size=12,
                font_family="Arial"
            )
        )
        return fig

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Block Metrics Monitor",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📊 Block Metrics Time Series Monitor")
    st.markdown("Real-time monitoring of block performance metrics")
    
    # Initialize monitor and metric states
    if 'monitor' not in st.session_state:
        st.session_state.monitor = BlockMonitor()

    # Initialize metric checkbox states from config (fallback to built-in defaults)
    if 'metric_states' not in st.session_state:
        # Try to read default metrics from the loaded config (streamlit_config.yaml)
        cfg_defaults = None
        try:
            streamlit_config_path = "streamlit_config.yaml"
            if "streamlit_config" not in st.session_state:
                st.session_state.streamlit_config = None
                try:
                    with open(streamlit_config_path, 'r') as file:
                        st.session_state.streamlit_config = yaml.safe_load(file)
                    logger.info(f"Loaded configuration from {streamlit_config_path}")
                except Exception as e:
                    logger.error(f"Error loading {streamlit_config_path}: {e}")
                    st.error(f"Error loading {streamlit_config_path}: {e}")
            # Expecting config to have top-level key 'streamlit'->'default_metrics' or 'default_metrics' at root
            if st.session_state.streamlit_config:
                cfg_defaults = (st.session_state.streamlit_config.get('streamlit') or {}).get('default_metrics') or st.session_state.streamlit_config.get('default_metrics')
        except Exception:
            cfg_defaults = None
        print(f"Config defaults: {cfg_defaults}")

        # Fallback built-in defaults (kept minimal and correct)
        fallback_defaults = [
            {'name': 'Queue Length Metrics', 'keys': ['queue_length.average_15m'], 'enabled': True},
            {'name': 'FPS Metrics', 'keys': ['fps.current'], 'enabled': True},
            {'name': 'Latency Metrics', 'keys': ['latency.current'], 'enabled': True},
            {'name': 'LLM Active Sessions', 'keys': ['llm_active_sessions_rolling.current'], 'enabled': False},
            {'name': 'GPU Utilization', 'keys': ['llm_gpu_utilization_rolling.current'], 'enabled': False},
            {'name': 'CPU Utilization', 'keys': ['llm_cpu_utilization_rolling.current'], 'enabled': False},
        ]

        # Use config defaults if present, otherwise fallback
        raw_defaults = cfg_defaults if cfg_defaults else fallback_defaults

        # Build a dict of metric_states from defaults
        metric_states = {}
        for m in raw_defaults:
            try:
                metric_states[m.get('name')] = bool(m.get('enabled', False))
            except Exception:
                # Skip malformed entries
                continue

        st.session_state.metric_states = metric_states
    
    monitor = st.session_state.monitor
    
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # Refresh interval
    refresh_interval = st.sidebar.slider(
        "Refresh Interval (seconds)",
        min_value=5,
        max_value=300,
        value=30,
        step=5
    )
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
    
    # Manual refresh button
    if st.sidebar.button("Refresh Now"):
        st.rerun()
    
    # Get available blocks
    block_names = monitor.get_block_names()
    
    if not block_names:
        st.error("No blocks found in config.yaml")
        return
    
    # Block selection
    selected_blocks = st.sidebar.multiselect(
        "Select Blocks to Monitor",
        options=block_names,
        default=block_names[:2] if len(block_names) >= 2 else block_names
    )
    
    # Metric configuration
    st.sidebar.header("Metric Configuration")
    
    # Add quick action buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Select All", key="select_all_metrics"):
            for metric_config in default_metrics:
                st.session_state.metric_states[metric_config['name']] = True
            st.rerun()
    
    with col2:
        if st.button("Clear All", key="clear_all_metrics"):
            for metric_config in default_metrics:
                st.session_state.metric_states[metric_config['name']] = False
            st.rerun()
    
    st.sidebar.divider()
    
    # Default metric configurations sourced from config (or fallback)
    if st.session_state.streamlit_config:
        default_metrics = (st.session_state.streamlit_config.get('streamlit') or {}).get('default_metrics') or st.session_state.streamlit_config.get('default_metrics')
    else:
        default_metrics = None

    if not default_metrics:
        # If still not present, use the same fallback as above with reasonable keys
        default_metrics = [
            {
                'name': 'Queue Length Metrics',
                'keys': ['queue_length.average_15m', 'queue_length.average_5m', 'queue_length.average_1m'],
                'enabled': True
            },
            {
                'name': 'FPS Metrics',
                'keys': ['fps.average_15m', 'fps.average_5m', 'fps.average_1m', 'fps.current'],
                'enabled': True
            },
            {
                'name': 'Latency Metrics',
                'keys': ['latency.average_15m', 'latency.average_5m', 'latency.average_1m', 'latency.current'],
                'enabled': True
            },
            {
                'name': 'LLM Active Sessions',
                'keys': ['llm_active_sessions_rolling.average_15m', 'llm_active_sessions_rolling.average_5m', 'llm_active_sessions_rolling.average_1m', 'llm_active_sessions_rolling.current'],
                'enabled': False
            },
            {
                'name': 'GPU Utilization',
                'keys': ['llm_gpu_utilization_rolling.average_15m', 'llm_gpu_utilization_rolling.average_5m', 'llm_gpu_utilization_rolling.average_1m', 'llm_gpu_utilization_rolling.current'],
                'enabled': False
            },
            {
                'name': 'CPU Utilization',
                'keys': ['llm_cpu_utilization_rolling.average_15m', 'llm_cpu_utilization_rolling.average_5m', 'llm_cpu_utilization_rolling.average_1m', 'llm_cpu_utilization_rolling.current'],
                'enabled': False
            },
            {
                'name': 'Empty Response Count',
                'keys': ['llm_inference_empty_token_total'],
                'enabled': True
            },
            {
                'name': 'Error Count',
                'keys': ['llm_inference_errors_total'],
                'enabled': True
            }
        ]
    
    # Allow users to enable/disable metrics
    enabled_metrics = []
    metrics_changed = False
    
    for metric_config in default_metrics:
        metric_name = metric_config['name']
        
        # Use session state value, fallback to default if not set
        current_state = st.session_state.metric_states.get(metric_name, metric_config['enabled'])
        
        # Create checkbox and update session state when changed
        checkbox_state = st.sidebar.checkbox(
            metric_name, 
            value=current_state,
            key=f"metric_{metric_name}"
        )
        
        # Check if state changed
        if st.session_state.metric_states.get(metric_name) != checkbox_state:
            metrics_changed = True
        
        # Update session state
        st.session_state.metric_states[metric_name] = checkbox_state
        
        # Add to enabled metrics if checked
        if checkbox_state:
            enabled_metrics.append(MetricConfig(
                name=metric_config['name'],
                keys=metric_config['keys']
            ))
    
    # Force rerun if metrics changed to immediately update UI
    if metrics_changed:
        st.rerun()
    
    # Custom metric input
    st.sidebar.subheader("Custom Metrics")
    
    # Initialize custom metric states if not exists
    if 'custom_metric_name' not in st.session_state:
        st.session_state.custom_metric_name = ""
    if 'custom_metric_keys' not in st.session_state:
        st.session_state.custom_metric_keys = ""
    
    custom_metric_name = st.sidebar.text_input(
        "Custom Metric Name",
        value=st.session_state.custom_metric_name,
        key="custom_name_input"
    )
    custom_metric_keys = st.sidebar.text_area(
        "Metric Keys (one per line)",
        value=st.session_state.custom_metric_keys,
        placeholder="queue_length.current\nfps.current\nlatency.current",
        key="custom_keys_input"
    )
    
    # Update session state
    st.session_state.custom_metric_name = custom_metric_name
    st.session_state.custom_metric_keys = custom_metric_keys
    
    if custom_metric_name and custom_metric_keys:
        keys = [key.strip() for key in custom_metric_keys.split('\n') if key.strip()]
        if keys:
            # Check if custom metric is enabled
            custom_key = f"custom_{custom_metric_name}"
            if custom_key not in st.session_state.metric_states:
                st.session_state.metric_states[custom_key] = True
            
            custom_enabled = st.sidebar.checkbox(
                f"Enable: {custom_metric_name}",
                value=st.session_state.metric_states[custom_key],
                key=f"custom_enable_{custom_metric_name}"
            )
            
            st.session_state.metric_states[custom_key] = custom_enabled
            
            if custom_enabled:
                enabled_metrics.append(MetricConfig(
                    name=custom_metric_name,
                    keys=keys
                ))
    
    # Main content area
    if not selected_blocks:
        st.warning("Please select at least one block to monitor")
        return
    
    # Create tabs for each selected block
    if len(selected_blocks) > 1:
        tabs = st.tabs([f"📈 {block_name}" for block_name in selected_blocks])
    else:
        tabs = [st.container()]  # Single container if only one block
    
    # Block status sidebar
    with st.sidebar:
        st.header("Block Status")
        status_container = st.container()
    
    # Display each block in its own tab
    for i, block_name in enumerate(selected_blocks):
        with tabs[i]:
            if len(selected_blocks) == 1:
                st.subheader(f"📈 {block_name}")
            
            # Fetch current data
            with st.spinner(f"Fetching data for {block_name}..."):
                block_data = monitor.fetch_block_data(block_name)
            
            if block_data:
                # Update data history
                monitor.update_data_history(block_name, block_data)
                
                # Update status in sidebar
                with status_container:
                    st.success(f"✅ {block_name}")
                    instances = block_data.get('instances', [])
                    st.write(f"Instances: {len(instances)}")
                    st.write(f"Last Update: {datetime.now(monitor.ist_tz).strftime('%H:%M:%S')}")
                    st.divider()
                
                # Create two columns for better layout
                main_col, info_col = st.columns([4, 1])
                
                with main_col:
                    # Use empty containers that can be completely cleared
                    if f"chart_containers_{block_name}" not in st.session_state:
                        st.session_state[f"chart_containers_{block_name}"] = {}
                    # Clear all previous containers
                    for container in st.session_state[f"chart_containers_{block_name}"].values():
                        container.empty()
                    # Create fresh containers
                    st.session_state[f"chart_containers_{block_name}"] = {}
                    # Create executor chart
                    executor_container = st.empty()
                    with executor_container.container():
                        executor_fig = monitor.create_executor_chart(block_name)
                        if executor_fig:
                            st.plotly_chart(
                                executor_fig, 
                                use_container_width=True
                            )
                    # Create metric charts: one chart per metric key, per metric group
                    if enabled_metrics:
                        chart_idx = 0
                        for metric_config in enabled_metrics:
                            for metric_key in metric_config.keys:
                                metric_container = st.empty()
                                st.session_state[f"chart_containers_{block_name}"][f"metric_{chart_idx}"] = metric_container
                                with metric_container.container():
                                    metric_fig = monitor.create_metric_key_chart(block_name, metric_config, metric_key)
                                    if metric_fig:
                                        metric_fig = monitor.add_hover_synchronization(metric_fig, metric_config)
                                        st.plotly_chart(
                                            metric_fig, 
                                            use_container_width=True
                                        )
                                    else:
                                        st.info(f"No data available for {metric_config.name} - {metric_key}")
                                chart_idx += 1
                    else:
                        no_metrics_container = st.empty()
                        with no_metrics_container.container():
                            st.info("No metrics selected. Please enable metrics from the sidebar configuration.")
                
                with info_col:
                    # Display current metrics summary
                    st.subheader("📊 Current Values")
                    instances = block_data.get('instances', [])
                    
                    # Show executor info if available
                    executor_instance = next((inst for inst in instances if inst.get('instanceId') == 'executor'), None)
                    if executor_instance:
                        tasks_total = monitor.extract_nested_value(executor_instance, 'tasks_processed.tasks_processed_total')
                        if tasks_total is not None:
                            st.metric("Tasks Processed", f"{tasks_total:,.0f}")
                    
                    # Show summary stats for non-executor instances
                    non_exec_instances = [inst for inst in instances if inst.get('instanceId') != 'executor']
                    if non_exec_instances and enabled_metrics:
                        st.write("**Instance Summary:**")
                        for instance in non_exec_instances[:3]:  # Show first 3 instances
                            instance_id = instance.get('instanceId', 'Unknown')
                            st.write(f"**{instance_id}**")
                            
                            # Show key metrics for this instance
                            for metric_config in enabled_metrics[:2]:  # Show first 2 metric groups
                                for key in metric_config.keys[:1]:  # Show first key from each group
                                    value = monitor.extract_nested_value(instance, key)
                                    if value is not None:
                                        st.write(f"  {key}: {value:.2f}")
                                break  # Only show first metric group in summary
            
            else:
                # Update status in sidebar
                with status_container:
                    st.error(f"❌ {block_name}")
                    st.write(f"Failed at: {datetime.now(monitor.ist_tz).strftime('%H:%M:%S')}")
                    st.divider()
                
                st.error(f"Failed to fetch data for {block_name}")
                st.info("Please check if the block service is running and accessible.")
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
