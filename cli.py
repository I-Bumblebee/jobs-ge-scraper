#!/usr/bin/env python3

import sys
from pathlib import Path
import click
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.database import sync_engine, test_connection
from sqlalchemy import text

console = Console()


@click.group()
def cli():
    """Jobs Scraper CLI - Interact with PostgreSQL views"""
    if not test_connection():
        console.print("❌ Database connection failed", style="red")
        sys.exit(1)


@cli.command()
@click.option('--limit',
              '-l',
              default=None,
              type=int,
              help='Limit number of rows')
@click.option('--platform', '-p', default=None, help='Filter by platform')
@click.option('--remote', '-r', is_flag=True, help='Show only remote jobs')
def show(limit, platform, remote):
    """Display jobs_overview as table in console"""

    query = "SELECT * FROM jobs_overview"
    conditions = []

    if platform:
        conditions.append(f"platform = '{platform}'")
    if remote:
        conditions.append("is_remote = true")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY scraped_date DESC"

    if limit:
        query += f" LIMIT {limit}"

    try:
        with sync_engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()

            if not rows:
                console.print("No jobs found", style="yellow")
                return

            # Create rich table
            table = Table(title=f"📊 Jobs Overview ({len(rows)} rows)",
                          box=box.MARKDOWN,
                          show_header=True,
                          header_style="bold blue")

            # Key columns to show (most important first)
            key_columns = [("platform", "Platform", 8),
                           ("title", "Job Title", 25),
                           ("company_name", "Company", 20),
                           ("location_display", "Location", 15),
                           ("salary_range", "Salary", 15),
                           ("days_since_scraped", "Days Ago", 8),
                           ("is_remote", "Remote", 6)]

            # Add columns to table
            for col_name, header, width in key_columns:
                table.add_column(header, max_width=width, overflow="ellipsis")

            # Add rows
            for row in rows:
                row_dict = dict(zip(columns, row))

                # Format values
                title = str(row_dict.get('title', ''))[:25]
                company = str(row_dict.get('company_name', 'N/A'))[:20]
                location = str(row_dict.get('location_display', ''))[:15]
                salary = str(row_dict.get('salary_range',
                                          'Not specified'))[:15]
                platform = str(row_dict.get('platform', ''))
                days_ago = str(int(row_dict.get('days_since_scraped', 0)))
                remote = "✅" if row_dict.get('is_remote') else "❌"

                table.add_row(platform, title, company, location, salary,
                              days_ago, remote)

            console.print(table)

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@cli.command()
@click.option('--format',
              '-f',
              default='csv',
              type=click.Choice(['csv', 'json', 'xlsx']),
              help='Export format')
@click.option('--output', '-o', default=None, help='Output filename')
@click.option('--platform', '-p', default=None, help='Filter by platform')
@click.option('--remote', '-r', is_flag=True, help='Show only remote jobs')
def export(format, output, platform, remote):
    """Export jobs_overview to file"""

    query = "SELECT * FROM jobs_overview"
    conditions = []

    if platform:
        conditions.append(f"platform = '{platform}'")
    if remote:
        conditions.append("is_remote = true")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY scraped_date DESC"

    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = data_dir / f"jobs_export_{timestamp}.{format}"
    else:
        # If user provides output, put it in data folder unless it's an absolute path
        output_path = Path(output)
        if not output_path.is_absolute():
            output = data_dir / output

    try:
        with sync_engine.connect() as conn:
            df = pd.read_sql(query, conn)

            if df.empty:
                console.print("No jobs found to export", style="yellow")
                return

            if format == 'csv':
                df.to_csv(output, index=False)
            elif format == 'json':
                df.to_json(output, orient='records', indent=2)
            elif format == 'xlsx':
                df.to_excel(output, index=False)

            console.print(f"✅ Exported {len(df)} rows to {output}",
                          style="green")

    except Exception as e:
        console.print(f"❌ Export failed: {e}", style="red")


@cli.command()
def stats():
    """Show quick database statistics"""

    queries = {
        "Total Jobs":
        "SELECT COUNT(*) FROM jobs_overview",
        "By Platform":
        "SELECT platform, COUNT(*) as count FROM jobs_overview GROUP BY platform",
        "Remote Jobs":
        "SELECT COUNT(*) FROM jobs_overview WHERE is_remote = true",
        "With Salary":
        "SELECT COUNT(*) FROM jobs_overview WHERE has_salary_info = true"
    }

    try:
        with sync_engine.connect() as conn:
            # Create stats table
            stats_table = Table(title="📊 Database Statistics",
                                box=box.ROUNDED,
                                show_header=True,
                                header_style="bold green")

            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Count", justify="right", style="magenta")

            # Get all stats
            result = conn.execute(text(queries["Total Jobs"]))
            total = result.fetchone()[0]

            result = conn.execute(text(queries["Remote Jobs"]))
            remote = result.fetchone()[0]

            result = conn.execute(text(queries["With Salary"]))
            with_salary = result.fetchone()[0]

            # Add rows to stats table
            stats_table.add_row("Total Jobs", str(total))
            stats_table.add_row("Remote Jobs", str(remote))
            stats_table.add_row("With Salary Info", str(with_salary))

            console.print(stats_table)

            # Platform breakdown table
            platform_table = Table(title="Jobs by Platform",
                                   box=box.SIMPLE,
                                   show_header=True,
                                   header_style="bold yellow")

            platform_table.add_column("Platform", style="cyan")
            platform_table.add_column("Count",
                                      justify="right",
                                      style="magenta")

            result = conn.execute(text(queries["By Platform"]))
            for row in result:
                platform_table.add_row(row[0], str(row[1]))

            console.print(platform_table)

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")


@cli.command()
@click.argument('sql_query')
def query(sql_query):
    """Execute custom SQL query on jobs_overview"""

    try:
        with sync_engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = result.fetchall()
            columns = result.keys()

            if not rows:
                console.print("No results", style="yellow")
                return

            # Create dynamic table for query results
            query_table = Table(title="Query Results",
                                box=box.MARKDOWN,
                                show_header=True,
                                header_style="bold blue")

            # Add columns dynamically
            for col in columns:
                query_table.add_column(str(col),
                                       max_width=20,
                                       overflow="ellipsis")

            # Add rows
            for row in rows:
                query_table.add_row(*[str(val)[:20] for val in row])

            console.print(query_table)

    except Exception as e:
        console.print(f"❌ Query failed: {e}", style="red")


@cli.command()
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
def reinit(force):
    """Reinitialize database by running init.sql script"""

    sql_file = Path("sql/init.sql")

    if not sql_file.exists():
        console.print("❌ init.sql file not found", style="red")
        return

    if not force:
        console.print("⚠️  This will reinitialize the database schema",
                      style="yellow")
        if not click.confirm("Continue?"):
            console.print("Operation cancelled", style="yellow")
            return

    try:
        # Read the SQL file
        with open(sql_file, 'r') as f:
            sql_content = f.read()

        console.print("🔄 Executing init.sql...", style="blue")

        # Execute the SQL as a single script to handle functions with dollar-quoted strings
        with sync_engine.connect() as conn:
            with conn.begin():
                conn.execute(text(sql_content))

        console.print("✅ Database reinitialized successfully!", style="green")
        console.print("📊 All tables, indexes, triggers, and views are ready",
                      style="blue")

    except Exception as e:
        console.print(f"❌ Reinit failed: {e}", style="red")


if __name__ == "__main__":
    cli()
