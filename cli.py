#!/usr/bin/env python3

import sys
from pathlib import Path
import click
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
from typing import Optional
import base64
import io
from jinja2 import Template

sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.database import sync_engine, test_connection
from sqlalchemy import text

console = Console()

# Set matplotlib style for better looking charts
plt.style.use('default')
sns.set_palette("husl")


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


@cli.command()
@click.option('--type', '-t', 
              type=click.Choice(['platform', 'location', 'remote', 'timeline', 'salary', 'category', 'companies', 'all']),
              default='all',
              help='Type of chart to generate')
@click.option('--save-path', '-s', default=None, help='Directory to save charts (default: charts/)')
@click.option('--show', is_flag=True, help='Display charts interactively')
@click.option('--platform', '-p', default=None, help='Filter by platform')
@click.option('--days', '-d', default=30, type=int, help='Days back for timeline charts (default: 30)')
def charts(type, save_path, show, platform, days):
    """Generate various charts and visualizations"""
    
    # Ensure charts directory exists
    if save_path is None:
        save_path = Path("charts")
    else:
        save_path = Path(save_path)
    
    save_path.mkdir(exist_ok=True)
    
    # Configure matplotlib for non-interactive backend if not showing
    if not show:
        plt.ioff()
        # Use Agg backend for non-interactive plotting
        import matplotlib
        matplotlib.use('Agg')
    
    try:
        with sync_engine.connect() as conn:
            # Base query with optional platform filter
            base_query = "SELECT * FROM jobs_overview"
            if platform:
                base_query += f" WHERE platform = '{platform}'"
            
            df = pd.read_sql(base_query, conn)
            
            if df.empty:
                console.print("No jobs found for charting", style="yellow")
                return
            
            console.print(f"📊 Generating charts from {len(df)} jobs...", style="blue")
            
            # Generate charts based on type
            if type == 'platform' or type == 'all':
                _create_platform_chart(df, save_path, show)
            
            if type == 'location' or type == 'all':
                _create_location_chart(df, save_path, show)
            
            if type == 'remote' or type == 'all':
                _create_remote_chart(df, save_path, show)
            
            if type == 'timeline' or type == 'all':
                _create_timeline_chart(df, save_path, show, days)
            
            if type == 'salary' or type == 'all':
                _create_salary_chart(df, save_path, show)
            
            if type == 'category' or type == 'all':
                _create_category_chart(df, save_path, show)
            
            if type == 'companies' or type == 'all':
                _create_companies_chart(df, save_path, show)
            
            console.print(f"✅ Charts saved to {save_path}/", style="green")
            
            if show:
                console.print("📈 Displaying charts interactively...", style="blue")
                plt.show()
    
    except Exception as e:
        console.print(f"❌ Chart generation failed: {e}", style="red")


def _create_platform_chart(df: pd.DataFrame, save_path: Path, show: bool):
    """Create jobs by platform chart"""
    plt.figure(figsize=(10, 6))
    
    platform_counts = df['platform'].value_counts()
    
    ax = sns.barplot(x=platform_counts.index, y=platform_counts.values, hue=platform_counts.index, palette="viridis", legend=False)
    plt.title('Job Listings by Platform', fontsize=16, fontweight='bold')
    plt.xlabel('Platform', fontsize=12)
    plt.ylabel('Number of Jobs', fontsize=12)
    
    # Add value labels on bars
    for i, v in enumerate(platform_counts.values):
        ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if not show:
        plt.savefig(save_path / 'jobs_by_platform.png', dpi=300, bbox_inches='tight')
        plt.close()


def _create_location_chart(df: pd.DataFrame, save_path: Path, show: bool):
    """Create jobs by location chart"""
    plt.figure(figsize=(12, 8))
    
    # Get top 15 cities
    location_counts = df[df['city'].notna()]['city'].value_counts().head(15)
    
    if location_counts.empty:
        plt.text(0.5, 0.5, 'No location data available', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title('Top Cities by Job Count', fontsize=16, fontweight='bold')
    else:
        ax = sns.barplot(y=location_counts.index, x=location_counts.values, hue=location_counts.index, palette="plasma", legend=False)
        plt.title('Top 15 Cities by Job Count', fontsize=16, fontweight='bold')
        plt.xlabel('Number of Jobs', fontsize=12)
        plt.ylabel('City', fontsize=12)
        
        # Add value labels on bars
        for i, v in enumerate(location_counts.values):
            ax.text(v + 0.1, i, str(v), ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    
    if not show:
        plt.savefig(save_path / 'jobs_by_location.png', dpi=300, bbox_inches='tight')
        plt.close()


def _create_remote_chart(df: pd.DataFrame, save_path: Path, show: bool):
    """Create remote vs non-remote jobs pie chart"""
    plt.figure(figsize=(8, 8))
    
    remote_counts = df['is_remote'].value_counts()
    labels = ['Non-Remote', 'Remote']
    colors = ['#ff9999', '#66b3ff']
    
    # Map boolean values to labels
    values = [remote_counts.get(False, 0), remote_counts.get(True, 0)]
    
    plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('Remote vs Non-Remote Job Distribution', fontsize=16, fontweight='bold')
    plt.axis('equal')
    
    if not show:
        plt.savefig(save_path / 'remote_jobs_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()


def _create_timeline_chart(df: pd.DataFrame, save_path: Path, show: bool, days: int):
    """Create jobs over time timeline chart"""
    plt.figure(figsize=(12, 6))
    
    # Convert scraped_date to datetime if it's not already
    df_copy = df.copy()
    df_copy['scraped_date'] = pd.to_datetime(df_copy['scraped_date'])
    
    # Filter last N days
    cutoff_date = pd.Timestamp.now().tz_localize(None) - pd.Timedelta(days=days)
    # Make sure both sides of comparison are timezone-naive
    df_copy['scraped_date'] = df_copy['scraped_date'].dt.tz_localize(None)
    recent_df = df_copy[df_copy['scraped_date'] >= cutoff_date]
    
    if recent_df.empty:
        plt.text(0.5, 0.5, f'No jobs found in last {days} days', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title(f'Jobs Scraped Over Last {days} Days', fontsize=16, fontweight='bold')
    else:
        # Group by date and count
        daily_counts = recent_df.groupby(recent_df['scraped_date'].dt.date).size()
        
        plt.plot(daily_counts.index, daily_counts.values, marker='o', linewidth=2, markersize=6)
        plt.title(f'Jobs Scraped Over Last {days} Days', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Jobs Scraped', fontsize=12)
        plt.xticks(rotation=45)
        
        # Format x-axis dates
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
    
    plt.tight_layout()
    
    if not show:
        plt.savefig(save_path / f'jobs_timeline_{days}days.png', dpi=300, bbox_inches='tight')
        plt.close()


def _create_salary_chart(df: pd.DataFrame, save_path: Path, show: bool):
    """Create salary distribution chart"""
    plt.figure(figsize=(12, 6))
    
    # Filter jobs with salary information
    salary_df = df[df['has_salary_info'] == True].copy()
    
    if salary_df.empty or salary_df['salary_min'].isna().all():
        plt.text(0.5, 0.5, 'No salary data available', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title('Salary Distribution', fontsize=16, fontweight='bold')
    else:
        # Use salary_min for distribution (could also use average of min/max)
        salary_data = salary_df['salary_min'].dropna()
        
        plt.subplot(1, 2, 1)
        sns.histplot(salary_data, bins=20, kde=True, color='skyblue')
        plt.title('Salary Distribution (Minimum)', fontsize=14, fontweight='bold')
        plt.xlabel('Salary (Min)', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        
        plt.subplot(1, 2, 2)
        # Box plot by platform
        if len(salary_df['platform'].unique()) > 1:
            sns.boxplot(data=salary_df, x='platform', y='salary_min', palette="Set2")
            plt.title('Salary Distribution by Platform', fontsize=14, fontweight='bold')
            plt.xlabel('Platform', fontsize=12)
            plt.ylabel('Salary (Min)', fontsize=12)
            plt.xticks(rotation=45)
        else:
            plt.text(0.5, 0.5, 'Single platform data', ha='center', va='center', 
                    transform=plt.gca().transAxes, fontsize=12)
    
    plt.tight_layout()
    
    if not show:
        plt.savefig(save_path / 'salary_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()


def _create_category_chart(df: pd.DataFrame, save_path: Path, show: bool):
    """Create jobs by category chart"""
    plt.figure(figsize=(12, 8))
    
    # Filter out null categories and get top 15
    category_counts = df[df['category'].notna()]['category'].value_counts().head(15)
    
    if category_counts.empty:
        plt.text(0.5, 0.5, 'No category data available', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title('Top Job Categories', fontsize=16, fontweight='bold')
    else:
        ax = sns.barplot(y=category_counts.index, x=category_counts.values, hue=category_counts.index, palette="Set3", legend=False)
        plt.title('Top 15 Job Categories', fontsize=16, fontweight='bold')
        plt.xlabel('Number of Jobs', fontsize=12)
        plt.ylabel('Category', fontsize=12)
        
        # Add value labels on bars
        for i, v in enumerate(category_counts.values):
            ax.text(v + 0.1, i, str(v), ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    
    if not show:
        plt.savefig(save_path / 'jobs_by_category.png', dpi=300, bbox_inches='tight')
        plt.close()


def _create_companies_chart(df: pd.DataFrame, save_path: Path, show: bool):
    """Create top companies by job count chart"""
    plt.figure(figsize=(12, 8))
    
    # Get top 15 companies
    company_counts = df[df['company_name'].notna()]['company_name'].value_counts().head(15)
    
    if company_counts.empty:
        plt.text(0.5, 0.5, 'No company data available', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title('Top Companies by Job Count', fontsize=16, fontweight='bold')
    else:
        ax = sns.barplot(y=company_counts.index, x=company_counts.values, hue=company_counts.index, palette="coolwarm", legend=False)
        plt.title('Top 15 Companies by Job Count', fontsize=16, fontweight='bold')
        plt.xlabel('Number of Jobs', fontsize=12)
        plt.ylabel('Company', fontsize=12)
        
        # Add value labels on bars
        for i, v in enumerate(company_counts.values):
            ax.text(v + 0.1, i, str(v), ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    
    if not show:
        plt.savefig(save_path / 'top_companies.png', dpi=300, bbox_inches='tight')
        plt.close()


@cli.command()
@click.option('--output', '-o', default=None, help='Output HTML filename (default: reports/job_analysis_report.html)')
@click.option('--platform', '-p', default=None, help='Filter by platform')
@click.option('--days', '-d', default=30, type=int, help='Days back for timeline analysis (default: 30)')
@click.option('--title', '-t', default='Job Market Analysis Report', help='Report title')
def html_report(output, platform, days, title):
    """Generate comprehensive HTML report with embedded charts and data analysis"""
    
    # Ensure reports directory exists
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        output = reports_dir / f"job_analysis_report_{timestamp}.html"
    else:
        output_path = Path(output)
        if not output_path.is_absolute():
            output = Path("reports") / output_path
            output.parent.mkdir(exist_ok=True)
    
    # Configure matplotlib for non-interactive backend
    plt.ioff()
    import matplotlib
    matplotlib.use('Agg')
    
    try:
        with sync_engine.connect() as conn:
            # Base query with optional platform filter
            base_query = "SELECT * FROM jobs_overview"
            if platform:
                base_query += f" WHERE platform = '{platform}'"
            
            df = pd.read_sql(base_query, conn)
            
            if df.empty:
                console.print("No jobs found for report generation", style="yellow")
                return
            
            console.print(f"📊 Generating HTML report from {len(df)} jobs...", style="blue")
            
            # Generate all charts as base64 images
            charts_data = {}
            charts_data['platform'] = _generate_chart_base64(df, _create_platform_chart_for_html)
            charts_data['location'] = _generate_chart_base64(df, _create_location_chart_for_html)
            charts_data['remote'] = _generate_chart_base64(df, _create_remote_chart_for_html)
            charts_data['companies'] = _generate_chart_base64(df, _create_companies_chart_for_html)
            
            # Generate summary statistics
            stats = _generate_summary_stats(df)
            
            # Generate data tables
            tables = _generate_data_tables(df)
            
            # Create HTML report
            html_content = _create_html_report(title, stats, charts_data, tables, platform, days)
            
            # Write HTML file
            with open(output, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            console.print(f"✅ HTML report generated: {output}", style="green")
            console.print(f"📝 Report contains {len(df)} jobs with interactive charts and analysis", style="blue")
    
    except Exception as e:
        console.print(f"❌ HTML report generation failed: {e}", style="red")


def _generate_chart_base64(df: pd.DataFrame, chart_function) -> str:
    """Generate a chart and return it as base64 encoded string"""
    try:
        chart_function(df)
        
        # Save plot to memory buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buffer.seek(0)
        
        # Encode to base64
        chart_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{chart_base64}"
    except Exception as e:
        console.print(f"Warning: Chart generation failed: {e}", style="yellow")
        return ""


def _create_platform_chart_for_html(df: pd.DataFrame):
    """Create platform chart optimized for HTML reports"""
    plt.figure(figsize=(10, 6))
    platform_counts = df['platform'].value_counts()
    ax = sns.barplot(x=platform_counts.index, y=platform_counts.values, hue=platform_counts.index, palette="viridis", legend=False)
    plt.title('Job Listings by Platform', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Platform', fontsize=12)
    plt.ylabel('Number of Jobs', fontsize=12)
    
    for i, v in enumerate(platform_counts.values):
        ax.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
    
    plt.xticks(rotation=45)
    plt.tight_layout()


def _create_location_chart_for_html(df: pd.DataFrame):
    """Create location chart optimized for HTML reports"""
    plt.figure(figsize=(12, 8))
    location_counts = df[df['city'].notna()]['city'].value_counts().head(15)
    
    if location_counts.empty:
        plt.text(0.5, 0.5, 'No location data available', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title('Top Cities by Job Count', fontsize=16, fontweight='bold')
    else:
        ax = sns.barplot(y=location_counts.index, x=location_counts.values, hue=location_counts.index, palette="plasma", legend=False)
        plt.title('Top 15 Cities by Job Count', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Number of Jobs', fontsize=12)
        plt.ylabel('City', fontsize=12)
        
        for i, v in enumerate(location_counts.values):
            ax.text(v + 0.1, i, str(v), ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()


def _create_remote_chart_for_html(df: pd.DataFrame):
    """Create remote jobs chart optimized for HTML reports"""
    plt.figure(figsize=(8, 8))
    remote_counts = df['is_remote'].value_counts()
    labels = ['Non-Remote', 'Remote']
    colors = ['#ff9999', '#66b3ff']
    values = [remote_counts.get(False, 0), remote_counts.get(True, 0)]
    
    plt.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    plt.title('Remote vs Non-Remote Job Distribution', fontsize=16, fontweight='bold', pad=20)
    plt.axis('equal')


def _create_timeline_chart_for_html(df: pd.DataFrame, days: int):
    """Create timeline chart optimized for HTML reports"""
    plt.figure(figsize=(12, 6))
    
    df_copy = df.copy()
    df_copy['scraped_date'] = pd.to_datetime(df_copy['scraped_date'])
    cutoff_date = pd.Timestamp.now().tz_localize(None) - pd.Timedelta(days=days)
    df_copy['scraped_date'] = df_copy['scraped_date'].dt.tz_localize(None)
    recent_df = df_copy[df_copy['scraped_date'] >= cutoff_date]
    
    if recent_df.empty:
        plt.text(0.5, 0.5, f'No jobs found in last {days} days', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title(f'Jobs Scraped Over Last {days} Days', fontsize=16, fontweight='bold')
    else:
        daily_counts = recent_df.groupby(recent_df['scraped_date'].dt.date).size()
        plt.plot(daily_counts.index, daily_counts.values, marker='o', linewidth=2, markersize=6)
        plt.title(f'Jobs Scraped Over Last {days} Days', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Number of Jobs Scraped', fontsize=12)
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days//10)))
    
    plt.tight_layout()


def _create_salary_chart_for_html(df: pd.DataFrame):
    """Create salary chart optimized for HTML reports"""
    plt.figure(figsize=(12, 6))
    salary_df = df[df['has_salary_info'] == True].copy()
    
    if salary_df.empty or salary_df['salary_min'].isna().all():
        plt.text(0.5, 0.5, 'No salary data available', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title('Salary Distribution', fontsize=16, fontweight='bold')
    else:
        salary_data = salary_df['salary_min'].dropna()
        
        plt.subplot(1, 2, 1)
        sns.histplot(salary_data, bins=20, kde=True, color='skyblue')
        plt.title('Salary Distribution (Minimum)', fontsize=14, fontweight='bold')
        plt.xlabel('Salary (Min)', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        
        plt.subplot(1, 2, 2)
        if len(salary_df['platform'].unique()) > 1:
            sns.boxplot(data=salary_df, x='platform', y='salary_min', palette="Set2")
            plt.title('Salary Distribution by Platform', fontsize=14, fontweight='bold')
            plt.xlabel('Platform', fontsize=12)
            plt.ylabel('Salary (Min)', fontsize=12)
            plt.xticks(rotation=45)
        else:
            plt.text(0.5, 0.5, 'Single platform data', ha='center', va='center', 
                    transform=plt.gca().transAxes, fontsize=12)
    
    plt.tight_layout()


def _create_category_chart_for_html(df: pd.DataFrame):
    """Create category chart optimized for HTML reports"""
    plt.figure(figsize=(12, 8))
    category_counts = df[df['category'].notna()]['category'].value_counts().head(15)
    
    if category_counts.empty:
        plt.text(0.5, 0.5, 'No category data available', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title('Top Job Categories', fontsize=16, fontweight='bold')
    else:
        ax = sns.barplot(y=category_counts.index, x=category_counts.values, hue=category_counts.index, palette="Set3", legend=False)
        plt.title('Top 15 Job Categories', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Number of Jobs', fontsize=12)
        plt.ylabel('Category', fontsize=12)
        
        for i, v in enumerate(category_counts.values):
            ax.text(v + 0.1, i, str(v), ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()


def _create_companies_chart_for_html(df: pd.DataFrame):
    """Create companies chart optimized for HTML reports"""
    plt.figure(figsize=(12, 8))
    company_counts = df[df['company_name'].notna()]['company_name'].value_counts().head(15)
    
    if company_counts.empty:
        plt.text(0.5, 0.5, 'No company data available', ha='center', va='center', 
                transform=plt.gca().transAxes, fontsize=14)
        plt.title('Top Companies by Job Count', fontsize=16, fontweight='bold')
    else:
        ax = sns.barplot(y=company_counts.index, x=company_counts.values, hue=company_counts.index, palette="coolwarm", legend=False)
        plt.title('Top 15 Companies by Job Count', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Number of Jobs', fontsize=12)
        plt.ylabel('Company', fontsize=12)
        
        for i, v in enumerate(company_counts.values):
            ax.text(v + 0.1, i, str(v), ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()


def _generate_summary_stats(df: pd.DataFrame) -> dict:
    """Generate summary statistics for the report"""
    stats = {
        'total_jobs': len(df),
        'platforms': df['platform'].nunique(),
        'platform_breakdown': df['platform'].value_counts().to_dict(),
        'remote_jobs': len(df[df['is_remote'] == True]),
        'jobs_with_salary': len(df[df['has_salary_info'] == True]),
        'unique_companies': df['company_name'].nunique(),
        'unique_cities': df['city'].nunique(),
        'date_range': {
            'earliest': df['scraped_date'].min(),
            'latest': df['scraped_date'].max()
        }
    }
    
    # Add top categories if available
    if df['category'].notna().any():
        stats['top_categories'] = df[df['category'].notna()]['category'].value_counts().head(5).to_dict()
    
    # Add average salary if available
    if df['salary_min'].notna().any():
        stats['avg_min_salary'] = df['salary_min'].mean()
        stats['median_min_salary'] = df['salary_min'].median()
    
    return stats


def _generate_data_tables(df: pd.DataFrame) -> dict:
    """Generate data tables for the report"""
    tables = {}
    
    # Recent jobs table (last 10)
    tables['recent_jobs'] = df.head(10)[['platform', 'title', 'company_name', 'location_display', 'salary_range', 'days_since_scraped']].to_html(
        classes='table', 
        table_id='recent-jobs-table',
        escape=False,
        index=False
    )
    
    # Platform statistics table
    platform_stats = []
    for platform in df['platform'].unique():
        platform_df = df[df['platform'] == platform]
        platform_stats.append({
            'Platform': platform,
            'Total Jobs': len(platform_df),
            'Remote Jobs': len(platform_df[platform_df['is_remote'] == True]),
            'With Salary': len(platform_df[platform_df['has_salary_info'] == True]),
            'Unique Companies': platform_df['company_name'].nunique()
        })
    
    platform_stats_df = pd.DataFrame(platform_stats)
    tables['platform_stats'] = platform_stats_df.to_html(
        classes='table',
        table_id='platform-stats-table',
        escape=False,
        index=False
    )
    
    return tables


def _create_html_report(title: str, stats: dict, charts: dict, tables: dict, platform_filter: str, days: int) -> str:
    """Create the complete HTML report"""
    
    html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.5;
            color: #1a1a1a;
            margin: 0;
            padding: 0;
            background: #ffffff;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
        }
        header {
            text-align: center;
            margin-bottom: 50px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e5e5e5;
        }
        h1 {
            color: #1a1a1a;
            font-size: 2.2rem;
            font-weight: 600;
            margin: 0 0 10px 0;
            letter-spacing: -0.5px;
        }
        .subtitle {
            color: #666;
            font-size: 0.95rem;
            margin: 0;
        }
        h2 {
            color: #1a1a1a;
            font-size: 1.4rem;
            font-weight: 600;
            margin: 40px 0 20px 0;
            letter-spacing: -0.3px;
        }
        h3 {
            color: #333;
            font-size: 1.1rem;
            font-weight: 500;
            margin: 30px 0 15px 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 30px 0;
        }
        .stat-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 20px;
            text-align: center;
            border-radius: 6px;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0 0 5px 0;
        }
        .stat-label {
            font-size: 0.85rem;
            color: #666;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .chart-section {
            margin: 40px 0;
        }
        .chart-container {
            margin: 20px 0;
            text-align: center;
            padding: 15px;
            background: #fafbfc;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }
        .table-container {
            margin: 30px 0;
            overflow-x: auto;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            background: white;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            overflow: hidden;
        }
        .table th {
            background: #f6f8fa;
            color: #24292e;
            font-weight: 600;
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid #e1e4e8;
            font-size: 0.85rem;
        }
        .table td {
            padding: 12px 16px;
            border-bottom: 1px solid #e1e4e8;
            font-size: 0.9rem;
        }
        .table tbody tr:last-child td {
            border-bottom: none;
        }
        .table tbody tr:hover {
            background-color: #f6f8fa;
        }
        .filter-info {
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            padding: 16px;
            border-radius: 6px;
            margin: 20px 0;
            font-size: 0.9rem;
        }
        .filter-info strong {
            color: #1565c0;
        }
        .metadata {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 16px;
            border-radius: 6px;
            margin: 40px 0 0 0;
            font-size: 0.85rem;
            color: #6a737d;
        }
        .metadata strong {
            color: #24292e;
        }
        @media (max-width: 768px) {
            .container {
                padding: 20px 15px;
            }
            h1 {
                font-size: 1.8rem;
            }
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }
            .stat-card {
                padding: 15px;
            }
            .stat-value {
                font-size: 1.5rem;
            }
            .chart-container {
                padding: 10px;
            }
            .table th, .table td {
                padding: 8px 12px;
                font-size: 0.8rem;
            }
        }
        @media (max-width: 480px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ title }}</h1>
            <p class="subtitle">Generated on {{ generation_time }}</p>
        </header>
        
        {% if platform_filter %}
        <div class="filter-info">
            <strong>Filtered Report:</strong> Showing data for platform <strong>{{ platform_filter }}</strong>
        </div>
        {% endif %}

        <section>
            <h2>Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{{ stats.total_jobs }}</div>
                    <div class="stat-label">Total Jobs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ stats.platforms }}</div>
                    <div class="stat-label">Platforms</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ stats.remote_jobs }}</div>
                    <div class="stat-label">Remote Jobs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ stats.unique_companies }}</div>
                    <div class="stat-label">Companies</div>
                </div>
            </div>
        </section>

        <section class="chart-section">
            <h2>Charts & Analysis</h2>
            
            <h3>Platform Distribution</h3>
            <div class="chart-container">
                <img src="{{ charts.platform }}" alt="Jobs by Platform">
            </div>

            <h3>Geographic Distribution</h3>
            <div class="chart-container">
                <img src="{{ charts.location }}" alt="Jobs by Location">
            </div>

            <h3>Remote Work Distribution</h3>
            <div class="chart-container">
                <img src="{{ charts.remote }}" alt="Remote vs Non-Remote Jobs">
            </div>



            <h3>Top Companies</h3>
            <div class="chart-container">
                <img src="{{ charts.companies }}" alt="Top Companies">
            </div>
        </section>

        <section>
            <h2>Data Tables</h2>
            
            <h3>Platform Statistics</h3>
            <div class="table-container">
                {{ tables.platform_stats | safe }}
            </div>

            <h3>Recent Job Listings</h3>
            <div class="table-container">
                {{ tables.recent_jobs | safe }}
            </div>
        </section>

        <div class="metadata">
            <strong>Data Range:</strong> {{ stats.date_range.earliest }} to {{ stats.date_range.latest }}
        </div>
    </div>
</body>
</html>
    """
    
    template = Template(html_template)
    return template.render(
        title=title,
        stats=stats,
        charts=charts,
        tables=tables,
        platform_filter=platform_filter,
        days=days,
        generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


if __name__ == "__main__":
    cli()
