from datetime import datetime, timedelta
import logging
import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from airflow.providers.postgres.hooks.postgres import PostgresHook
from googleapiclient.discovery import build

# =============================================================================
# [STEP 1] Data Collection Strategy Configuration
# =============================================================================
REQUIRED_COLUMNS = [
    'channel_id', 'video_id', 'title', 'description', 'thumbnail_url',
    'view_count', 'like_count', 'comment_count', 'published_at', 'collected_at'
]

# =============================================================================
# [STEP 3] Supabase Connection & Table Setup
# =============================================================================
def get_db_connection():
    """
    Establishes a connection to Supabase using Airflow Connection.
    Connection ID: xoosl033110_supabase_conn
    """
    hook = PostgresHook(postgres_conn_id='xoosl033110_supabase_conn')
    return hook.get_conn()

def create_schema_and_table():
    """
    [STEP 3] Implements the Schema and Table creation SQL.
    """
    sql_statements = [
        "CREATE SCHEMA IF NOT EXISTS tlswlgo3;",
        """
        CREATE TABLE IF NOT EXISTS tlswlgo3.youtube_videos (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT,
            channel_title TEXT,
            description TEXT,
            thumbnail_url TEXT,
            view_count BIGINT,
            like_count BIGINT,
            comment_count BIGINT,
            published_at TIMESTAMP,
            collected_at TIMESTAMP
        );
        """
    ]
    
    # Using the hook directly for execution is cleaner but get_conn works with existing structure
    hook = PostgresHook(postgres_conn_id='xoosl033110_supabase_conn')
    try:
        with hook.get_conn() as conn:
            with conn.cursor() as cur:
                for sql in sql_statements:
                    cur.execute(sql)
                    logging.info(f"Executed SQL: {sql[:50]}...")
            conn.commit() # Ensure commits
        logging.info("Schema and Table check/creation completed.")
    except Exception as e:
        logging.error(f"Schema creation failed: {e}")
        raise

# =============================================================================
# [STEP 4] YouTube Data Collection
# =============================================================================
def fetch_youtube_data(**context):
    """
    [STEP 4] Fetches data from YouTube API.
    - Searches for '무한도전'
    - Retrieves statistics
    - Formats data
    """
    # The user should set this variable in Airflow UI > Admin > Variables
    api_key = Variable.get("YOUTUBE_API_KEY", default_var=None)
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY variable is missing in Airflow.")

    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # 1. Search for videos
    logging.info("Searching for '무한도전' videos...")
    search_response = youtube.search().list(
        q="무한도전",
        part="id,snippet",
        maxResults=50,
        order="date",  # Get most recent
        type="video"
    ).execute()
    
    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
    
    if not video_ids:
        logging.info("No videos found.")
        return []
        
    logging.info(f"Found {len(video_ids)} videos. Fetching details...")
    
    # 2. Get details (statistics)
    videos_response = youtube.videos().list(
        part="snippet,statistics",
        id=','.join(video_ids)
    ).execute()
    
    collected_data = []
    current_time = datetime.now()
    
    for item in videos_response.get('items', []):
        try:
            # Safe access with defaults
            stats = item.get('statistics', {})
            snippet = item.get('snippet', {})
            thumbnails = snippet.get('thumbnails', {})
            high_thumb = thumbnails.get('high', {}) or thumbnails.get('medium', {}) or thumbnails.get('default', {})
            
            video_data = {
                'video_id': item['id'],
                'channel_id': snippet.get('channelId'),
                'channel_title': snippet.get('channelTitle'),
                'title': snippet.get('title'),
                'description': snippet.get('description'),
                'thumbnail_url': high_thumb.get('url'),
                'view_count': int(stats.get('viewCount', 0)),
                'like_count': int(stats.get('likeCount', 0)),
                'comment_count': int(stats.get('commentCount', 0)),
                'published_at': snippet.get('publishedAt'),
                'collected_at': current_time
            }
            collected_data.append(video_data)
        except Exception as e:
            logging.error(f"Error parse video item {item.get('id')}: {e}")
            
    logging.info(f"Parsed {len(collected_data)} items.")
    return collected_data

# =============================================================================
# [STEP 5 & 2] Load to Supabase with Deduplication
# =============================================================================
def load_to_supabase(**context):
    """
    [STEP 5] Loads data into Supabase.
    [STEP 2] Uses ON CONFLICT DO NOTHING for deduplication.
    """
    ti = context['ti']
    data = ti.xcom_pull(task_ids='extract_youtube_data')
    
    if not data:
        logging.info("No data to load.")
        return

    # Reminder: Schema does NOT currently have 'title' column roughly based on requirements.
    # We strictly follow the provided schema SQL.
    insert_sql = """
        INSERT INTO tlswlgo3.youtube_videos (
            video_id, channel_id, channel_title, description, 
            thumbnail_url, view_count, like_count, comment_count, 
            published_at, collected_at
        ) VALUES (
            %(video_id)s, %(channel_id)s, %(channel_title)s, %(description)s, 
            %(thumbnail_url)s, %(view_count)s, %(like_count)s, %(comment_count)s, 
            %(published_at)s, %(collected_at)s
        )
        ON CONFLICT (video_id) DO NOTHING;
    """
    
    hook = PostgresHook(postgres_conn_id='xoosl033110_supabase_conn')
    inserted_count = 0
    
    try:
        with hook.get_conn() as conn:
            with conn.cursor() as cur:
                for row in data:
                    cur.execute(insert_sql, row)
                    if cur.rowcount > 0:
                        inserted_count += 1
            conn.commit()
                        
        logging.info(f"Load complete. Inserted {inserted_count} new videos (skipped {len(data) - inserted_count} duplicates).")
            
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        raise

# =============================================================================
# [STEP 6] Airflow DAG Configuration
# =============================================================================
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False, # Can be configured
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'infinite_challenge_archive',
    default_args=default_args,
    description='Collects Infinite Challenge video data every 30 mins',
    schedule='*/30 * * * *',
    start_date=pendulum.datetime(2024, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=['infinite_challenge', 'youtube', 'archive'],
) as dag:

    create_table_task = PythonOperator(
        task_id='create_table_if_not_exists',
        python_callable=create_schema_and_table
    )

    extract_task = PythonOperator(
        task_id='extract_youtube_data',
        python_callable=fetch_youtube_data,
        provide_context=True
    )

    load_task = PythonOperator(
        task_id='load_to_supabase',
        python_callable=load_to_supabase,
        provide_context=True
    )

    create_table_task >> extract_task >> load_task

# =============================================================================
# [STEP 7] Pipeline Summary & Notes (Code Comments)
# =============================================================================
# Pipeline Summary:
# - Triggered every 30 minutes.
# - Checks/Creates DB Schema.
# - Fetches latest 'Infinite Challenge' videos from YouTube.
# - Inserts new videos into Supabase, ignoring duplicates via ON CONFLICT DO NOTHING.
#
# Operational Notes:
# - Ensure Airflow Variables are set: YOUTUBE_API_KEY, SUPABASE_HOST, etc.
# - The Table Schema provided in requirements MISSES 'title' column. Code naturally omits it.
