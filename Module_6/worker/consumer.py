"""This module listens for messages on a task queue, determines task kind, 
and calls functions for data processing based on the kind."""

import json
import os
import time
import pika
import psycopg
from etl.update_database import ( # pylint: disable=E0401
    find_recent,
    updated_scrape,
    clean_data,
    process_data_with_llm,
    get_db_connection,
)
from etl.query_data import run_queries # pylint: disable=E0401

def update_watermark(source, last_seen):
    """Update watermark table with most recent id."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ingestion_watermarks (source, last_seen)
                    VALUES (%s, %s)
                    ON CONFLICT (source) 
                    DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = now();
                """, (source, last_seen))
    finally:
        if conn:
            conn.close()

def get_last_seen(source):
    """Extract last_seen from watermark table."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT last_seen FROM ingestion_watermarks WHERE source = %s;
                """, (source,))
                result = cur.fetchone()
                return result[0] if result else None
    finally:
        if conn:
            conn.close()

def handle_scrape_new_data(channel, method): # pylint: disable=R0914,R0915
    """Call function for scrape new data task."""
    try:
        conn = get_db_connection()
        data_source = "TheGradCafe"
        last_seen = get_last_seen(data_source)  # Get last seen identifier from the watermark table
        recent_id = find_recent() or 0  # Start from ID 0 if no previous entries exist

        scraped_entries = updated_scrape(last_seen or recent_id)

        if not scraped_entries:
            print("No new data found to scrape.")
            return

        print(f"Found {len(scraped_entries)} new entries. Cleaning the data...")
        cleaned_data = clean_data(scraped_entries)

        if not cleaned_data:
            print("Data cleaning failed - no valid entries found.")
            return

        print(f"Processing {len(cleaned_data)} entries with LLM for standardization...")
        llm_extended_data = process_data_with_llm(cleaned_data)

        if not llm_extended_data:
            print("LLM processing failed - no data to add.")
            return

        last_seen = llm_extended_data[-1]["id"]  # Assuming the last entry has an "id"

        with conn:
            with conn.cursor() as cur:  # pylint: disable=E1101
                for entry in llm_extended_data:
                    # Prepare data for the database insertion (as in your original implementation)
                    program = entry["program"] if entry["program"] else None
                    comments = entry["comments"] if entry["comments"] else None
                    date_added = entry["date_added"] if entry["date_added"] else None
                    url = entry["url"] if entry["url"] else None
                    status = entry["status"] if entry["status"] else None
                    term = entry["term"] if entry["term"] else None
                    us_int = entry["US/International"]
                    us_or_international = us_int if us_int else None
                    gpa = float(entry["GPA"]) if entry["GPA"] else None
                    gre = float(entry["GRE"]) if entry["GRE"] else None
                    gre_v = float(entry["GRE_V"]) if entry["GRE_V"] else None
                    gre_aw = float(entry["GRE_AW"]) if entry["GRE_AW"] else None
                    degree = entry["Degree"] if entry["Degree"] else None
                    llm_prog = entry["llm-generated-program"]
                    llm_generated_program = llm_prog if llm_prog else None
                    llm_uni = entry["llm-generated-university"]
                    llm_generated_university = llm_uni if llm_uni else None

                    # Define variables for table and columns
                    table_name = psycopg.sql.Identifier("applicants")
                    columns = [
                        "program", "comments", "date_added", "url", "status",
                        "term", "us_or_international", "gpa", "gre", "gre_v",
                        "gre_aw", "degree", "llm_generated_program",
                        "llm_generated_university"
                    ]
                    column_identifiers = [psycopg.sql.Identifier(col) for col in columns]

                    # SQL string composition for the insert query
                    query = psycopg.sql.SQL("""
                        INSERT INTO {table} ({fields})
                        VALUES ({placeholders})
                    """).format(
                        table=table_name,
                        fields=psycopg.sql.SQL(', ').join(column_identifiers),
                        placeholders = psycopg.sql.SQL(', ').join(
                            psycopg.sql.Placeholder() for _ in columns
                        )
                    )

                    # Execute the query
                    cur.execute(query, (
                        program, comments, date_added, url, status, term,
                        us_or_international, gpa, gre, gre_v,
                        gre_aw, degree, llm_generated_program,
                        llm_generated_university
                    ))

        # Update the watermark table with the last seen after all data has been processed
        if last_seen is not None:
            update_watermark(data_source, last_seen)

        # Acknowledge the RabbitMQ message after a successful commit
        channel.basic_ack(delivery_tag=method.delivery_tag)
        print("Data scraping and processing completed successfully!")

    # Rollback and nack if not success
    except Exception as e: # pylint: disable=W0718
        conn.rollback()
        # Nack the message with requeue=False in case of failure
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        print(f"Error while scraping and processing new data: {str(e)}")

    finally:
        if conn:
            conn.close()  # Ensure the connection is closed

def handle_recompute_analytics():
    """Call function to rerun queries (recompute analytics) for newly scraped data."""
    try:
        print("Recomputing analytics...")
        results = run_queries()
        print("Analytics recomputed successfully!")
        return results
    except Exception as e: # pylint: disable=W0718
        print(f"Error while recomputing analytics: {str(e)}")
        return e

def callback(channel, method, body):
    """Define RabbitMQ message callback and determine message kind."""
    payload = json.loads(body)
    task_type = payload.get("kind")

    # Route by "kind"
    if task_type == "scrape_new_data":
        handle_scrape_new_data(channel, method)
    elif task_type == "recompute_analytics":
        handle_recompute_analytics()

def main():
    """Start up RabbitMQ connection and consume messages."""
    url = os.environ.get("RABBITMQ_URL", "amqp://rabbituser:rabbitpass@rabbitmq:5672/")
    connected = False
    
    # Logic to connect/wait and retry connection upon error
    while not connected:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(url))
            connected = True
        except pika.exceptions.AMQPConnectionError:
            print("Connection failed, retrying in 5 seconds...")
            time.sleep(5)  # Wait before retrying

    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue='tasks_q', durable=True)

    # Consume messages from the queue
    # Set backpressure, one message at a time
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='tasks_q', on_message_callback=callback)

    print('Waiting for messages. To exit press CTRL+C')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    main()
