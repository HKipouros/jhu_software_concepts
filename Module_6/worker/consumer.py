import pika
import json
import os
import psycopg
from etl.update_database import find_recent, updated_scrape, clean_data, process_data_with_llm, get_db_connection
from etl.query_data import run_queries, get_db_connection

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

# Function to handle scraping new data
def handle_scrape_new_data(payload):
    try:
        conn = get_db_connection()
        data_source = "TheGradCafe"  # Define your source name
        last_seen = get_last_seen(data_source)  # Get last seen identifier from the watermark table
        recent_id = find_recent() or 0  # Start from ID 0 if no previous entries exist

        scraped_entries = updated_scrape(last_seen or recent_id)  # Use last_seen or recent_id for scraping

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
                    us_or_international = entry["US/International"] if entry["US/International"] else None
                    gpa = float(entry["GPA"]) if entry["GPA"] else None
                    gre = float(entry["GRE"]) if entry["GRE"] else None
                    gre_v = float(entry["GRE_V"]) if entry["GRE_V"] else None
                    gre_aw = float(entry["GRE_AW"]) if entry["GRE_AW"] else None
                    degree = entry["Degree"] if entry["Degree"] else None
                    llm_generated_program = entry["llm-generated-program"] if entry["llm-generated-program"] else None
                    llm_generated_university = entry["llm-generated-university"] if entry["llm-generated-university"] else None

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
                        placeholders=psycopg.sql.SQL(', ').join(psycopg.sql.Placeholder() for _ in columns)
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
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print("Data scraping and processing completed successfully!")

    # Rollback and nack if not success
    except Exception as e:
        conn.rollback()
        # Nack the message with requeue=False in case of failure
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        print(f"Error while scraping and processing new data: {str(e)}")
    
    finally:
        if conn:
            conn.close()  # Ensure the connection is closed


# Function to handle analysis recomputation
def handle_recompute_analytics(payload):
    try:
        print("Recomputing analytics...")
        results = run_queries()  # Run existing query logic here
        print("Analytics recomputed successfully!")
        # You can further process results or store them as needed
    except Exception as e:
        print(f"Error while recomputing analytics: {str(e)}")

# RabbitMQ message callback
def callback(ch, method, properties, body):
    payload = json.loads(body)
    task_type = payload.get("kind")

    # Route by "kind"
    if task_type == "scrape_new_data":
        handle_scrape_new_data(payload)
    elif task_type == "recompute_analytics":
        handle_recompute_analytics(payload)

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    # Set up the RabbitMQ connection
    url = os.environ.get("RABBITMQ_URL", "amqp://rabbituser:rabbitpass@rabbitmq:5672/")
    print("RabbitMQ URL:", url)
    connection = pika.BlockingConnection(pika.URLParameters(url))
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