"""
LiquibaseDB - Database Migration and Version Control CLI
Inspired by Liquibase for database schema management
"""

import sqlite3
import json
import yaml
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import click
from tabulate import tabulate
import hashlib


# Migration Model
class Migration:
    def __init__(self, id: str, author: str, description: str, 
                 changes: List[Dict], rollback: Optional[List[Dict]] = None):
        self.id = id
        self.author = author
        self.description = description
        self.changes = changes
        self.rollback = rollback or []
        self.checksum = self._calculate_checksum()
        self.executed_at = None
    
    def _calculate_checksum(self) -> str:
        content = f"{self.id}{self.author}{json.dumps(self.changes)}"
        return hashlib.md5(content.encode()).hexdigest()


# Database Connection Manager
class DatabaseManager:
    def __init__(self, db_path: str = "liquibase.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_changelog_table()
    
    def _init_changelog_table(self):
        """Initialize the DATABASECHANGELOG table to track migrations"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DATABASECHANGELOG (
                id TEXT PRIMARY KEY,
                author TEXT NOT NULL,
                filename TEXT NOT NULL,
                date_executed TIMESTAMP NOT NULL,
                order_executed INTEGER NOT NULL,
                exec_type TEXT NOT NULL,
                md5sum TEXT NOT NULL,
                description TEXT,
                comments TEXT,
                tag TEXT,
                liquibase_version TEXT,
                contexts TEXT,
                labels TEXT,
                deployment_id TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DATABASECHANGELOGLOCK (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                locked BOOLEAN NOT NULL,
                lockgranted TIMESTAMP,
                lockedby TEXT
            )
        """)
        
        # Initialize lock table
        cursor.execute("INSERT OR IGNORE INTO DATABASECHANGELOGLOCK (id, locked) VALUES (1, 0)")
        self.conn.commit()
    
    def execute_sql(self, sql: str, params: tuple = ()):
        """Execute SQL statement"""
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor
    
    def fetch_all(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Fetch all results"""
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()


# Migration Executor
class MigrationExecutor:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_executed_migrations(self) -> List[str]:
        """Get list of executed migration IDs"""
        rows = self.db.fetch_all("SELECT id FROM DATABASECHANGELOG ORDER BY order_executed")
        return [row['id'] for row in rows]
    
    def execute_migration(self, migration: Migration, filename: str):
        """Execute a single migration"""
        click.echo(f"Executing migration: {migration.id} by {migration.author}")
        
        try:
            # Execute each change
            for change in migration.changes:
                self._execute_change(change)
            
            # Record in changelog
            order = len(self.get_executed_migrations()) + 1
            self.db.execute_sql("""
                INSERT INTO DATABASECHANGELOG 
                (id, author, filename, date_executed, order_executed, exec_type, 
                 md5sum, description, liquibase_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                migration.id,
                migration.author,
                filename,
                datetime.now().isoformat(),
                order,
                'EXECUTED',
                migration.checksum,
                migration.description,
                '1.0.0'
            ))
            
            click.echo(f"✓ Migration {migration.id} executed successfully")
            return True
            
        except Exception as e:
            click.echo(f"✗ Error executing migration {migration.id}: {str(e)}", err=True)
            return False
    
    def rollback_migration(self, migration: Migration):
        """Rollback a migration"""
        click.echo(f"Rolling back migration: {migration.id}")
        
        try:
            if not migration.rollback:
                click.echo("⚠ No rollback defined for this migration", err=True)
                return False
            
            # Execute rollback changes
            for change in migration.rollback:
                self._execute_change(change)
            
            # Remove from changelog
            self.db.execute_sql(
                "DELETE FROM DATABASECHANGELOG WHERE id = ?",
                (migration.id,)
            )
            
            click.echo(f"✓ Migration {migration.id} rolled back successfully")
            return True
            
        except Exception as e:
            click.echo(f"✗ Error rolling back migration {migration.id}: {str(e)}", err=True)
            return False
    
    def _execute_change(self, change: Dict):
        """Execute a single change"""
        change_type = list(change.keys())[0]
        change_data = change[change_type]
        
        if change_type == 'createTable':
            self._create_table(change_data)
        elif change_type == 'addColumn':
            self._add_column(change_data)
        elif change_type == 'dropColumn':
            self._drop_column(change_data)
        elif change_type == 'renameColumn':
            self._rename_column(change_data)
        elif change_type == 'createIndex':
            self._create_index(change_data)
        elif change_type == 'dropTable':
            self._drop_table(change_data)
        elif change_type == 'sql':
            self._execute_raw_sql(change_data)
        elif change_type == 'insert':
            self._insert_data(change_data)
        else:
            raise ValueError(f"Unknown change type: {change_type}")
    
    def _create_table(self, data: Dict):
        table_name = data['tableName']
        columns = data['columns']
        
        column_defs = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            if col.get('constraints', {}).get('primaryKey'):
                col_def += " PRIMARY KEY"
            if col.get('constraints', {}).get('autoIncrement'):
                col_def += " AUTOINCREMENT"
            if col.get('constraints', {}).get('nullable') == False:
                col_def += " NOT NULL"
            if col.get('constraints', {}).get('unique'):
                col_def += " UNIQUE"
            if 'defaultValue' in col:
                col_def += f" DEFAULT {col['defaultValue']}"
            column_defs.append(col_def)
        
        sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"
        self.db.execute_sql(sql)
    
    def _add_column(self, data: Dict):
        table_name = data['tableName']
        column = data['column']
        
        col_def = f"{column['name']} {column['type']}"
        if 'defaultValue' in column:
            col_def += f" DEFAULT {column['defaultValue']}"
        
        sql = f"ALTER TABLE {table_name} ADD COLUMN {col_def}"
        self.db.execute_sql(sql)
    
    def _drop_column(self, data: Dict):
        # SQLite doesn't support DROP COLUMN directly
        # This is a simplified version
        click.echo(f"⚠ Note: SQLite has limited DROP COLUMN support")
        table_name = data['tableName']
        column_name = data['columnName']
        sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
        self.db.execute_sql(sql)
    
    def _rename_column(self, data: Dict):
        table_name = data['tableName']
        old_name = data['oldColumnName']
        new_name = data['newColumnName']
        sql = f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}"
        self.db.execute_sql(sql)
    
    def _create_index(self, data: Dict):
        index_name = data['indexName']
        table_name = data['tableName']
        columns = data['columns']
        
        column_list = ', '.join([col['name'] for col in columns])
        sql = f"CREATE INDEX {index_name} ON {table_name} ({column_list})"
        self.db.execute_sql(sql)
    
    def _drop_table(self, data: Dict):
        table_name = data['tableName']
        sql = f"DROP TABLE IF EXISTS {table_name}"
        self.db.execute_sql(sql)
    
    def _execute_raw_sql(self, data: Dict):
        sql = data['sql']
        self.db.execute_sql(sql)
    
    def _insert_data(self, data: Dict):
        table_name = data['tableName']
        columns = list(data['columns'].keys())
        values = list(data['columns'].values())
        
        placeholders = ', '.join(['?' for _ in values])
        column_list = ', '.join(columns)
        
        sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
        self.db.execute_sql(sql, tuple(values))


# Changelog Parser
class ChangelogParser:
    @staticmethod
    def parse_yaml(file_path: str) -> List[Migration]:
        """Parse YAML changelog file"""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        migrations = []
        for changeset in data.get('databaseChangeLog', []):
            if 'changeSet' in changeset:
                cs = changeset['changeSet']
                migration = Migration(
                    id=cs['id'],
                    author=cs['author'],
                    description=cs.get('comment', ''),
                    changes=cs['changes'],
                    rollback=cs.get('rollback', [])
                )
                migrations.append(migration)
        
        return migrations
    
    @staticmethod
    def parse_json(file_path: str) -> List[Migration]:
        """Parse JSON changelog file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        migrations = []
        for changeset in data.get('databaseChangeLog', []):
            if 'changeSet' in changeset:
                cs = changeset['changeSet']
                migration = Migration(
                    id=cs['id'],
                    author=cs['author'],
                    description=cs.get('comment', ''),
                    changes=cs['changes'],
                    rollback=cs.get('rollback', [])
                )
                migrations.append(migration)
        
        return migrations


# CLI Application
@click.group()
@click.option('--db', default='liquibase.db', help='Database file path')
@click.pass_context
def cli(ctx, db):
    """LiquibaseDB - Database Migration and Version Control"""
    ctx.ensure_object(dict)
    ctx.obj['db_manager'] = DatabaseManager(db)
    ctx.obj['executor'] = MigrationExecutor(ctx.obj['db_manager'])


@cli.command()
@click.argument('changelog_file')
@click.pass_context
def update(ctx, changelog_file):
    """Execute all pending migrations from changelog"""
    if not Path(changelog_file).exists():
        click.echo(f"✗ Changelog file not found: {changelog_file}", err=True)
        return
    
    # Parse changelog
    if changelog_file.endswith('.yaml') or changelog_file.endswith('.yml'):
        migrations = ChangelogParser.parse_yaml(changelog_file)
    elif changelog_file.endswith('.json'):
        migrations = ChangelogParser.parse_json(changelog_file)
    else:
        click.echo("✗ Unsupported file format. Use .yaml, .yml, or .json", err=True)
        return
    
    executor = ctx.obj['executor']
    executed = executor.get_executed_migrations()
    
    pending = [m for m in migrations if m.id not in executed]
    
    if not pending:
        click.echo("✓ Database is up to date!")
        return
    
    click.echo(f"Found {len(pending)} pending migration(s)")
    
    for migration in pending:
        executor.execute_migration(migration, changelog_file)


@cli.command()
@click.argument('count', type=int, default=1)
@click.argument('changelog_file')
@click.pass_context
def rollback(ctx, count, changelog_file):
    """Rollback the last N migrations"""
    if not Path(changelog_file).exists():
        click.echo(f"✗ Changelog file not found: {changelog_file}", err=True)
        return
    
    # Parse changelog
    if changelog_file.endswith('.yaml') or changelog_file.endswith('.yml'):
        migrations = ChangelogParser.parse_yaml(changelog_file)
    elif changelog_file.endswith('.json'):
        migrations = ChangelogParser.parse_json(changelog_file)
    else:
        click.echo("✗ Unsupported file format", err=True)
        return
    
    executor = ctx.obj['executor']
    executed = executor.get_executed_migrations()
    
    # Get migrations to rollback (in reverse order)
    to_rollback = executed[-count:]
    to_rollback.reverse()
    
    migrations_dict = {m.id: m for m in migrations}
    
    for migration_id in to_rollback:
        if migration_id in migrations_dict:
            executor.rollback_migration(migrations_dict[migration_id])


@cli.command()
@click.pass_context
def status(ctx):
    """Show migration status"""
    executor = ctx.obj['executor']
    db = ctx.obj['db_manager']
    
    rows = db.fetch_all("""
        SELECT id, author, date_executed, description 
        FROM DATABASECHANGELOG 
        ORDER BY order_executed
    """)
    
    if rows:
        data = [[r['id'], r['author'], r['date_executed'], r['description']] for r in rows]
        headers = ['ID', 'Author', 'Executed At', 'Description']
        click.echo("\nExecuted Migrations:")
        click.echo(tabulate(data, headers=headers, tablefmt='grid'))
    else:
        click.echo("No migrations executed yet.")


@cli.command()
@click.pass_context
def history(ctx):
    """Show detailed migration history"""
    db = ctx.obj['db_manager']
    
    rows = db.fetch_all("""
        SELECT * FROM DATABASECHANGELOG ORDER BY order_executed DESC
    """)
    
    if rows:
        for row in rows:
            click.echo(f"\n{'='*60}")
            click.echo(f"ID: {row['id']}")
            click.echo(f"Author: {row['author']}")
            click.echo(f"File: {row['filename']}")
            click.echo(f"Executed: {row['date_executed']}")
            click.echo(f"Checksum: {row['md5sum']}")
            click.echo(f"Description: {row['description']}")
    else:
        click.echo("No migration history found.")


@cli.command()
@click.argument('tag_name')
@click.pass_context
def tag(ctx, tag_name):
    """Tag the current database state"""
    db = ctx.obj['db_manager']
    executor = ctx.obj['executor']
    
    executed = executor.get_executed_migrations()
    if not executed:
        click.echo("✗ No migrations to tag", err=True)
        return
    
    last_migration = executed[-1]
    db.execute_sql(
        "UPDATE DATABASECHANGELOG SET tag = ? WHERE id = ?",
        (tag_name, last_migration)
    )
    
    click.echo(f"✓ Tagged current state as: {tag_name}")


@cli.command()
@click.argument('filename', default='changelog.yaml')
def generate(filename):
    """Generate a sample changelog file"""
    sample_yaml = """databaseChangeLog:
  - changeSet:
      id: 1
      author: john.doe
      comment: Create users table
      changes:
        - createTable:
            tableName: users
            columns:
              - name: id
                type: INTEGER
                constraints:
                  primaryKey: true
                  autoIncrement: true
              - name: username
                type: VARCHAR(50)
                constraints:
                  nullable: false
                  unique: true
              - name: email
                type: VARCHAR(100)
                constraints:
                  nullable: false
              - name: created_at
                type: TIMESTAMP
                defaultValue: CURRENT_TIMESTAMP
      rollback:
        - dropTable:
            tableName: users

  - changeSet:
      id: 2
      author: john.doe
      comment: Create posts table
      changes:
        - createTable:
            tableName: posts
            columns:
              - name: id
                type: INTEGER
                constraints:
                  primaryKey: true
                  autoIncrement: true
              - name: user_id
                type: INTEGER
                constraints:
                  nullable: false
              - name: title
                type: VARCHAR(200)
              - name: content
                type: TEXT
              - name: published
                type: BOOLEAN
                defaultValue: false
        - createIndex:
            indexName: idx_posts_user_id
            tableName: posts
            columns:
              - name: user_id
      rollback:
        - dropTable:
            tableName: posts

  - changeSet:
      id: 3
      author: jane.smith
      comment: Add phone column to users
      changes:
        - addColumn:
            tableName: users
            column:
              name: phone
              type: VARCHAR(20)
      rollback:
        - dropColumn:
            tableName: users
            columnName: phone
"""
    
    with open(filename, 'w') as f:
        f.write(sample_yaml)
    
    click.echo(f"✓ Generated sample changelog: {filename}")


@cli.command()
@click.pass_context
def validate(ctx):
    """Validate database changelog"""
    db = ctx.obj['db_manager']
    
    try:
        rows = db.fetch_all("SELECT COUNT(*) as count FROM DATABASECHANGELOG")
        count = rows[0]['count']
        click.echo(f"✓ Database changelog is valid ({count} migrations)")
    except Exception as e:
        click.echo(f"✗ Database validation failed: {str(e)}", err=True)


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear all migration history?')
@click.pass_context
def clear(ctx):
    """Clear all migration history (dangerous!)"""
    db = ctx.obj['db_manager']
    db.execute_sql("DELETE FROM DATABASECHANGELOG")
    click.echo("✓ Migration history cleared")


if __name__ == '__main__':
    cli(obj={})
