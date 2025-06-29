#!/usr/bin/env python3
"""
Database utility script for the Jobs Scraper application.
Provides convenient functions for database management and testing.
"""

import os
import sys
import argparse
from datetime import datetime

# Add src to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.config.database import (
        test_connection, 
        create_tables, 
        drop_tables, 
        sync_engine,
        SessionLocal,
        db_config
    )
    from sqlalchemy import text
except ImportError as e:
    print(f"Error importing database modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def print_config():
    """Print current database configuration."""
    print("=== Database Configuration ===")
    print(f"Host: {db_config.host}")
    print(f"Port: {db_config.port}")
    print(f"Database: {db_config.database}")
    print(f"Username: {db_config.username}")
    print(f"URL: {db_config.database_url.replace(db_config.password, '***')}")
    print()


def test_db_connection():
    """Test database connection."""
    print("Testing database connection...")
    if test_connection():
        print("✅ Database connection successful!")
        return True
    else:
        print("❌ Database connection failed!")
        return False


def show_tables():
    """Show all tables in the database."""
    try:
        with sync_engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()
            
            if tables:
                print("=== Database Tables ===")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("No tables found in the database.")
            print()
            return True
    except Exception as e:
        print(f"Error listing tables: {e}")
        return False


def show_table_info(table_name):
    """Show information about a specific table."""
    try:
        with sync_engine.connect() as connection:
            # Get column information
            result = connection.execute(text(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND table_schema = 'public'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            
            if columns:
                print(f"=== Table: {table_name} ===")
                print(f"{'Column':<30} {'Type':<20} {'Nullable':<10} {'Default':<20}")
                print("-" * 80)
                for col in columns:
                    nullable = "YES" if col[2] == "YES" else "NO"
                    default = str(col[3]) if col[3] else ""
                    print(f"{col[0]:<30} {col[1]:<20} {nullable:<10} {default:<20}")
                
                # Get row count
                count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = count_result.fetchone()[0]
                print(f"\nRow count: {row_count}")
            else:
                print(f"Table '{table_name}' not found.")
            print()
            return True
    except Exception as e:
        print(f"Error getting table info: {e}")
        return False


def create_db_tables():
    """Create all database tables."""
    print("Creating database tables...")
    if create_tables():
        print("✅ Tables created successfully!")
        return True
    else:
        print("❌ Failed to create tables!")
        return False


def drop_db_tables():
    """Drop all database tables."""
    confirm = input("⚠️  This will delete all tables and data. Are you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        print("Dropping database tables...")
        if drop_tables():
            print("✅ Tables dropped successfully!")
            return True
        else:
            print("❌ Failed to drop tables!")
            return False
    else:
        print("Operation cancelled.")
        return False


def run_custom_query():
    """Run a custom SQL query."""
    print("Enter your SQL query (type 'quit' to exit):")
    
    while True:
        query = input("SQL> ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            continue
            
        try:
            with sync_engine.connect() as connection:
                result = connection.execute(text(query))
                
                if result.returns_rows:
                    rows = result.fetchall()
                    if rows:
                        # Print column headers
                        if hasattr(result, 'keys'):
                            headers = result.keys()
                            print("\t".join(headers))
                            print("-" * (len("\t".join(headers))))
                        
                        # Print rows
                        for row in rows:
                            print("\t".join(str(val) for val in row))
                    else:
                        print("No rows returned.")
                else:
                    print(f"Query executed. Rows affected: {result.rowcount}")
                    
        except Exception as e:
            print(f"Error executing query: {e}")
        
        print()


def database_status():
    """Show comprehensive database status."""
    print("=== Database Status ===")
    print_config()
    
    if test_db_connection():
        show_tables()
        
        # Show some basic statistics
        try:
            with sync_engine.connect() as connection:
                print("=== Table Statistics ===")
                
                # Common tables to check
                tables_to_check = [
                    'job_listings', 'job_details', 'companies', 
                    'scraping_results', 'job_requirements'
                ]
                
                for table in tables_to_check:
                    try:
                        result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.fetchone()[0]
                        print(f"  {table}: {count} records")
                    except:
                        # Table might not exist
                        pass
                        
        except Exception as e:
            print(f"Error getting statistics: {e}")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description="Database utility for Jobs Scraper")
    parser.add_argument('command', nargs='?', default='status',
                      choices=['test', 'status', 'config', 'tables', 'create', 'drop', 'query', 'info'],
                      help='Command to run')
    parser.add_argument('--table', '-t', help='Table name for info command')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        test_db_connection()
    elif args.command == 'status':
        database_status()
    elif args.command == 'config':
        print_config()
    elif args.command == 'tables':
        show_tables()
    elif args.command == 'create':
        create_db_tables()
    elif args.command == 'drop':
        drop_db_tables()
    elif args.command == 'query':
        run_custom_query()
    elif args.command == 'info':
        if args.table:
            show_table_info(args.table)
        else:
            print("Please specify a table name with --table")


if __name__ == "__main__":
    main() 