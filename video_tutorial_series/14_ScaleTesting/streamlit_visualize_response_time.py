import os
import yaml
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, time
import plotly.graph_objs as go
import pytz

#st.set_option('server.websocketConnectionTimeout', 600)


# --- Page Setup ---
st.set_page_config(
    page_title="Response Time Analysis", 
    page_icon="🤖",
    layout="wide"  # This makes the layout use full width
)
st.title("🤖 Response Time Analysis")

def get_db_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    tsdb_cfg = config['DMA']['timescaledb']
    host = os.getenv('DMA_TIMESCALEDB_HOST') or tsdb_cfg.get('host', 'localhost')
    port = os.getenv('DMA_TIMESCALEDB_PORT') or tsdb_cfg.get('port', 5432)
    user = os.getenv('DMA_TIMESCALEDB_USERNAME') or tsdb_cfg.get('user', 'tsdbuser')
    db = os.getenv('DMA_TIMESCALEDB_DATABASE') or tsdb_cfg.get('database', 'transactions')
    password = os.getenv('DMA_TIMESCALEDB_PASSWORD') or tsdb_cfg.get('password', '')
    schema = 'public'  # Use public schema for log_entries
    table_name = tsdb_cfg.get('table_name', 'log_entries')
    return dict(host=host, port=port, user=user, db=db, password=password, schema=schema, table_name=table_name)

def fetch_log_entries(db_cfg, start_epoch, end_epoch, test_id=None):
    connection_string = f"postgresql://{db_cfg['user']}:{db_cfg['password']}@{db_cfg['host']}:{db_cfg['port']}/{db_cfg['db']}"
    # Create engine with connection pooling
    engine = create_engine(
        connection_string,
        pool_size=db_cfg.get('connection_pool_size', 5),
        max_overflow=db_cfg.get('max_overflow', 10),
        echo=False  # Set to True for SQL debugging
    )
    
    # Initialize metadata and tables
    metadata = MetaData()
    table_name = f"{db_cfg['schema']}.{db_cfg['table_name']}"
    # Define table structure (columns must match your DB schema)
    log_entries = Table(
        db_cfg['table_name'], metadata,
        Column('block_id', String),
        Column('session_id', String),
        Column('seq_no', Integer),
        Column('type', String),
        Column('response_time', Float),
        Column('raw', Text),
        Column('test_id', String),
        Column('user_id', String),
        Column('starttime', Float),
        Column('endtime', Float),
        Column('starttimeObj', String),
        Column('endtimeObj', String),
        autoload_with=engine
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        sql = f"""
            SELECT block_id, session_id, seq_no, type, response_time, raw, test_id, user_id, starttime, endtime, starttimeObj, endtimeObj
            FROM {table_name}
            WHERE endtime >= :start_epoch AND endtime <= :end_epoch
        """
        params = {'start_epoch': start_epoch, 'end_epoch': end_epoch}
        if test_id:
            sql += " AND test_id = :test_id"
            params['test_id'] = test_id
        result = session.execute(text(sql), params)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    except SQLAlchemyError as e:
        st.error(f"Database error: {e}")
        df = pd.DataFrame()
    finally:
        session.close()
        engine.dispose()
    return df

@st.cache_data(show_spinner=True)
def fetch_log_entries_cached(db_cfg, start_epoch, end_epoch, test_id=None):
    return fetch_log_entries(db_cfg, start_epoch, end_epoch, test_id)

def main():
    # timezone_str = self.config.get('logging', {}).get('timezone', 'Asia/Kolkata')
    ist_tz = pytz.timezone('Asia/Kolkata')
    st.title('Response Time Timeseries Visualization')
    db_cfg = get_db_config()
    st.sidebar.header('Time Filter')
    now = datetime.now(ist_tz)
    # Use session_state to retain values
    if 'start_date' not in st.session_state:
        st.session_state['start_date'] = now.date()
    if 'start_time' not in st.session_state:
        st.session_state['start_time'] = now.replace(hour=0, minute=0, second=0, microsecond=0).time()
    if 'end_date' not in st.session_state:
        st.session_state['end_date'] = now.date()
    if 'end_time' not in st.session_state:
        st.session_state['end_time'] = now.time()
    start_date = st.sidebar.date_input('Start Date', value=st.session_state['start_date'], key='start_date')
    start_time_val = st.sidebar.time_input('Start Time', value=st.session_state['start_time'], key='start_time')
    end_date = st.sidebar.date_input('End Date', value=st.session_state['end_date'], key='end_date')
    end_time_val = st.sidebar.time_input('End Time', value=st.session_state['end_time'], key='end_time')
    # Add slider for averaging window
    avg_window = st.sidebar.slider('Averaging Window (seconds)', min_value=1, max_value=1000, value=60, step=1)
    test_id = st.sidebar.text_input('Test ID (optional)', value='', key='test_id')
    submit = st.sidebar.button('Submit')
    if submit:
        # Always get the latest values from widgets
        start_date = st.session_state['start_date']
        start_time_val = st.session_state['start_time']
        end_date = st.session_state['end_date']
        end_time_val = st.session_state['end_time']
        start_dt = datetime.combine(start_date, start_time_val)
        start_dt = ist_tz.localize(start_dt)
        end_dt = datetime.combine(end_date, end_time_val)
        end_dt = ist_tz.localize(end_dt)
        start_epoch = start_dt.timestamp()
        end_epoch = end_dt.timestamp()
        st.sidebar.write(f"Epoch range: {start_epoch} - {end_epoch}")
        df = fetch_log_entries_cached(db_cfg, start_epoch, end_epoch, test_id)
        if df.empty:
            st.warning('No data found for selected time range.')
            return
        # Plot per session_id
        # fig = go.Figure()
        # for session_id, group in df.groupby('session_id'):
        #     x = [datetime.fromtimestamp(e) for e in group['endtime']]
        #     y = group['response_time']
        #     fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=str(session_id)))
        # fig.update_layout(
        #     title='Response Time per Session',
        #     xaxis_title='End Time',
        #     yaxis_title='Response Time (s)',
        #     hovermode='x unified',
        #     height=700,
        #     font=dict(size=16),
        #     legend=dict(font=dict(size=14)),
        #     margin=dict(l=60, r=60, t=80, b=80)
        # )
        # st.plotly_chart(fig, use_container_width=True, height=700)
        # --- Averaged response_time graph ---
        # Bin by avg_window seconds
        df_sorted = df.sort_values('endtime')
        min_time = df_sorted['endtime'].min()
        max_time = df_sorted['endtime'].max()
        bins = list(range(int(min_time), int(max_time)+avg_window, avg_window))
        df_sorted['bin'] = pd.cut(df_sorted['endtime'], bins=bins, labels=bins[:-1], include_lowest=True)
        avg_df = df_sorted.groupby('bin').agg({'response_time':'mean'}).reset_index()
        avg_df['bin_dt'] = avg_df['bin'].astype(float).apply(lambda x: datetime.fromtimestamp(x, ist_tz))
        fig_avg = go.Figure()
        fig_avg.add_trace(go.Scatter(x=avg_df['bin_dt'], y=avg_df['response_time'], mode='lines+markers', name=f'Avg Response Time ({avg_window}s window)'))
        fig_avg.update_layout(
            title=f'Average Response Time (Window: {avg_window} seconds)',
            xaxis_title='Time (window start)',
            yaxis_title='Avg Response Time (s)',
            hovermode='x unified',
            height=500,
            font=dict(size=16),
            margin=dict(l=60, r=60, t=60, b=60)
        )
        st.plotly_chart(fig_avg, use_container_width=True)
        # --- Request Counts over time ---
        count_df = df_sorted.groupby('bin').size().reset_index(name='count')
        count_df['bin_dt'] = count_df['bin'].astype(float).apply(lambda x: datetime.fromtimestamp(x, ist_tz))
        count_df['cumulative_count'] = count_df['count'].cumsum()
        fig_count = go.Figure()
        fig_count.add_trace(go.Scatter(
            x=count_df['bin_dt'],
            y=count_df['cumulative_count'],
            mode='lines+markers',
            name='Cumulative Request Count'
        ))
        fig_count.update_layout(
            title='Request Counts over time',
            xaxis_title='Time (window start)',
            yaxis_title='Cumulative Request Count',
            hovermode='x unified',
            height=400,
            font=dict(size=16),
            margin=dict(l=60, r=60, t=60, b=60)
        )
        st.plotly_chart(fig_count, use_container_width=True)
        # --- Request Counts Failed Over Time ---
        failed_df = df_sorted[df_sorted['type'].str.lower().isin(['failed', 'failure'])]
        count_failed_df = failed_df.groupby('bin').size().reset_index(name='count')
        count_failed_df['bin_dt'] = count_failed_df['bin'].astype(float).apply(lambda x: datetime.fromtimestamp(x, ist_tz))
        count_failed_df['cumulative_count'] = count_failed_df['count'].cumsum()
        fig_failed = go.Figure()
        fig_failed.add_trace(go.Scatter(
            x=count_failed_df['bin_dt'],
            y=count_failed_df['cumulative_count'],
            mode='lines+markers',
            name='Cumulative Failed Request Count'
        ))
        fig_failed.update_layout(
            title='Request Counts Failed Over Time',
            xaxis_title='Time (window start)',
            yaxis_title='Cumulative Failed Request Count',
            hovermode='x unified',
            height=400,
            font=dict(size=16),
            margin=dict(l=60, r=60, t=60, b=60)
        )
        st.plotly_chart(fig_failed, use_container_width=True)
        st.dataframe(df, use_container_width=True, height=500)
    else:
        st.info('Set your time range and press Submit to view results.')

if __name__ == '__main__':
    main()
