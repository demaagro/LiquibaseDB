# LiquibaseDB

CLI tool for database migration and version control, inspired by Liquibase. Manage your database schema changes with confidence using declarative changelog files.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 🚀 Features

- 📝 **Declarative Migrations** - Define schema changes in YAML or JSON
- 🔄 **Version Control** - Track all database changes with checksums
- ⏪ **Rollback Support** - Safely revert migrations
- 🏷️ **Tagging** - Tag specific database states
- 📊 **Migration History** - Complete audit trail of all changes
- 🔒 **Checksum Validation** - Detect unauthorized changes
- 🎯 **Multiple Change Types** - Support for tables, columns, indexes, and more
- 🛡️ **Safe Operations** - Confirmation prompts for dangerous actions

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Dependencies

```bash
pip install click tabulate pyyaml
```

### Quick Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/LiquibaseDB.git
cd LiquibaseDB
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Verify installation**
```bash
python liquibase_cli.py --help
```

## 🎯 Quick Start

### 1. Generate a Sample Changelog

```bash
python liquibase_cli.py generate changelog.yaml
```

This creates a sample `changelog.yaml` file with example migrations.

### 2. Apply Migrations

```bash
python liquibase_cli.py update changelog.yaml
```

### 3. Check Status

```bash
python liquibase_cli.py status
```

### 4. View History

```bash
python liquibase_cli.py history
```

## 📘 Usage Guide

### Command Reference

#### Update Database

Execute all pending migrations:
```bash
python liquibase_cli.py update <changelog_file>

# Example
python liquibase_cli.py update changelog.yaml
```

#### Rollback Migrations

Rollback the last N migrations:
```bash
python liquibase_cli.py rollback <count> <changelog_file>

# Rollback last migration
python liquibase_cli.py rollback 1 changelog.yaml

# Rollback last 3 migrations
python liquibase_cli.py rollback 3 changelog.yaml
```

#### Check Status

View executed migrations:
```bash
python liquibase_cli.py status
```

#### View History

See detailed migration history:
```bash
python liquibase_cli.py history
```

#### Tag Database State

Tag the current database version:
```bash
python liquibase_cli.py tag <tag_name>

# Example
python liquibase_cli.py tag v1.0.0
```

#### Generate Sample Changelog

Create a sample changelog file:
```bash
python liquibase_cli.py generate [filename]

# Default: changelog.yaml
python liquibase_cli.py generate

# Custom filename
python liquibase_cli.py generate my-changelog.yaml
```

#### Validate Database

Validate database changelog integrity:
```bash
python liquibase_cli.py validate
```

#### Clear History (Dangerous!)

Clear all migration history:
```bash
python liquibase_cli.py clear
```

### Specify Database File

Use a different database file:
```bash
python liquibase_cli.py --db myapp.db update changelog.yaml
```

## 📝 Changelog Format

### YAML Format (Recommended)

```yaml
databaseChangeLog:
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
      comment: Add index on email
      changes:
        - createIndex:
            indexName: idx_users_email
            tableName: users
            columns:
              - name: email
```

### JSON Format

```json
{
  "databaseChangeLog": [
    {
      "changeSet": {
        "id": "1",
        "author": "john.doe",
        "comment": "Create users table",
        "changes": [
          {
            "createTable": {
              "tableName": "users",
              "columns": [
                {
                  "name": "id",
                  "type": "INTEGER",
                  "constraints": {
                    "primaryKey": true,
                    "autoIncrement": true
                  }
                },
                {
                  "name": "username",
                  "type": "VARCHAR(50)",
                  "constraints": {
                    "nullable": false,
                    "unique": true
                  }
                }
              ]
            }
          }
        ],
        "rollback": [
          {
            "dropTable": {
              "tableName": "users"
            }
          }
        ]
      }
    }
  ]
}
```

## 🔧 Supported Change Types

### Create Table

```yaml
- createTable:
    tableName: products
    columns:
      - name: id
        type: INTEGER
        constraints:
          primaryKey: true
          autoIncrement: true
      - name: name
        type: VARCHAR(100)
        constraints:
          nullable: false
      - name: price
        type: DECIMAL(10,2)
        defaultValue: 0.00
```

### Add Column

```yaml
- addColumn:
    tableName: users
    column:
      name: phone
      type: VARCHAR(20)
      defaultValue: NULL
```

### Drop Column

```yaml
- dropColumn:
    tableName: users
    columnName: phone
```

### Rename Column

```yaml
- renameColumn:
    tableName: users
    oldColumnName: phone
    newColumnName: mobile
```

### Create Index

```yaml
- createIndex:
    indexName: idx_users_email
    tableName: users
    columns:
      - name: email
```

### Drop Table

```yaml
- dropTable:
    tableName: old_table
```

### Raw SQL

```yaml
- sql:
    sql: "UPDATE users SET status = 'active' WHERE created_at > '2024-01-01'"
```

### Insert Data

```yaml
- insert:
    tableName: users
    columns:
      username: admin
      email: admin@example.com
      role: administrator
```

## 📊 Database Schema

### DATABASECHANGELOG Table

Tracks all executed migrations:

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Unique migration identifier |
| author | TEXT | Migration author |
| filename | TEXT | Source changelog file |
| date_executed | TIMESTAMP | Execution timestamp |
| order_executed | INTEGER | Execution order |
| exec_type | TEXT | Execution type (EXECUTED, ROLLBACK) |
| md5sum | TEXT | Migration checksum |
| description | TEXT | Migration description |
| tag | TEXT | Optional tag name |

### DATABASECHANGELOGLOCK Table

Prevents concurrent migrations:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Always 1 (singleton) |
| locked | BOOLEAN | Lock status |
| lockgranted | TIMESTAMP | Lock timestamp |
| lockedby | TEXT | Lock owner |

## 🏗️ Architecture

### Core Components

```
LiquibaseDB/
├── Migration          # Migration data model
├── DatabaseManager    # Database connection & operations
├── MigrationExecutor  # Execute/rollback migrations
├── ChangelogParser    # Parse YAML/JSON changelogs
└── CLI Commands       # Command-line interface
```

### Migration Lifecycle

1. **Parse** - Read and validate changelog file
2. **Compare** - Check against executed migrations
3. **Execute** - Apply pending changes
4. **Record** - Update DATABASECHANGELOG
5. **Verify** - Validate with checksums

## 📖 Examples

### Example 1: Create a Blog Schema

```yaml
databaseChangeLog:
  - changeSet:
      id: create-blog-schema
      author: developer
      changes:
        - createTable:
            tableName: authors
            columns:
              - name: id
                type: INTEGER
                constraints:
                  primaryKey: true
                  autoIncrement: true
              - name: name
                type: VARCHAR(100)
              - name: bio
                type: TEXT

  - changeSet:
      id: create-posts-table
      author: developer
      changes:
        - createTable:
            tableName: posts
            columns:
              - name: id
                type: INTEGER
                constraints:
                  primaryKey: true
                  autoIncrement: true
              - name: author_id
                type: INTEGER
              - name: title
                type: VARCHAR(200)
              - name: content
                type: TEXT
              - name: published_at
                type: TIMESTAMP
        - createIndex:
            indexName: idx_posts_author
            tableName: posts
            columns:
              - name: author_id
```

### Example 2: Add Authentication

```yaml
databaseChangeLog:
  - changeSet:
      id: add-user-authentication
      author: security-team
      changes:
        - addColumn:
            tableName: users
            column:
              name: password_hash
              type: VARCHAR(255)
        - addColumn:
            tableName: users
            column:
              name: last_login
              type: TIMESTAMP
        - createIndex:
            indexName: idx_users_last_login
            tableName: users
            columns:
              - name: last_login
```

### Example 3: Data Migration

```yaml
databaseChangeLog:
  - changeSet:
      id: seed-initial-data
      author: admin
      changes:
        - insert:
            tableName: roles
            columns:
              name: admin
              description: Administrator
        - insert:
            tableName: roles
            columns:
              name: user
              description: Regular User
        - sql:
            sql: "UPDATE users SET role_id = 1 WHERE email = 'admin@example.com'"
```

## 🔄 Workflow Example

### Complete Development Cycle

```bash
# 1. Create a new migration
cat > migrations/001-init.yaml << EOF
databaseChangeLog:
  - changeSet:
      id: 1
      author: dev
      changes:
        - createTable:
            tableName: products
            columns:
              - name: id
                type: INTEGER
                constraints:
                  primaryKey: true
              - name: name
                type: VARCHAR(100)
EOF

# 2. Apply migration
python liquibase_cli.py update migrations/001-init.yaml

# 3. Check status
python liquibase_cli.py status

# 4. Tag this version
python liquibase_cli.py tag v1.0.0

# 5. Create another migration
cat > migrations/002-add-price.yaml << EOF
databaseChangeLog:
  - changeSet:
      id: 2
      author: dev
      changes:
        - addColumn:
            tableName: products
            column:
              name: price
              type: DECIMAL(10,2)
      rollback:
        - dropColumn:
            tableName: products
            columnName: price
EOF

# 6. Apply new migration
python liquibase_cli.py update migrations/002-add-price.yaml

# 7. Oops! Rollback if needed
python liquibase_cli.py rollback 1 migrations/002-add-price.yaml

# 8. View full history
python liquibase_cli.py history
```

## 🛡️ Best Practices

### 1. Migration IDs
- Use sequential numbers or timestamps
- Make them unique and descriptive
- Example: `001-create-users`, `20240101-add-indexes`

### 2. Always Include Rollbacks
```yaml
changes:
  - createTable:
      tableName: users
rollback:
  - dropTable:
      tableName: users
```

### 3. One Logical Change Per ChangeSet
❌ Bad:
```yaml
- changeSet:
    id: multiple-changes
    changes:
      - createTable: users
      - createTable: posts
      - addColumn: products
```

✅ Good:
```yaml
- changeSet:
    id: create-users
    changes:
      - createTable: users

- changeSet:
    id: create-posts
    changes:
      - createTable: posts
```

### 4. Test Migrations Before Production
```bash
# Test on development database
python liquibase_cli.py --db dev.db update changelog.yaml

# Test rollback
python liquibase_cli.py --db dev.db rollback 1 changelog.yaml

# Verify
python liquibase_cli.py --db dev.db validate
```

### 5. Use Version Control
```bash
git add migrations/
git commit -m "Add user authentication migration"
```

## 🔍 Troubleshooting

### Migration Already Executed

**Problem**: Migration appears as "already executed"

**Solution**: 
- Check `python liquibase_cli.py status`
- Verify migration ID is unique
- Use a new ID for the new change

### Checksum Mismatch

**Problem**: Checksum validation fails

**Solution**:
- Never modify executed migrations
- Create a new migration instead
- Or clear history (development only)

### Rollback Not Defined

**Problem**: Cannot rollback migration

**Solution**: Add rollback section to changeset:
```yaml
rollback:
  - dropTable:
      tableName: table_name
```

### SQLite Limitations

**Problem**: Some operations not supported

**Solution**: 
- SQLite has limited ALTER TABLE support
- Consider recreating tables for complex changes
- Use raw SQL for advanced operations

## 🚀 Advanced Usage

### Multiple Environments

```bash
# Development
python liquibase_cli.py --db dev.db update changelog.yaml

# Staging
python liquibase_cli.py --db staging.db update changelog.yaml

# Production
python liquibase_cli.py --db production.db update changelog.yaml
```

### Conditional Migrations

Use tags to manage different versions:
```bash
python liquibase_cli.py update changelog.yaml
python liquibase_cli.py tag v1.0.0

# Later, rollback to tag
python liquibase_cli.py rollback-to-tag v1.0.0
```

### Integration with CI/CD

```yaml
# .github/workflows/migrations.yml
name: Database Migrations

on: [push]

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run migrations
        run: python liquibase_cli.py update changelog.yaml
      - name: Validate
        run: python liquibase_cli.py validate
```

## 📚 Additional Resources

### Requirements File

Create `requirements.txt`:
```
click>=8.0.0
tabulate>=0.9.0
PyYAML>=6.0
```

### Sample Project Structure

```
my-project/
├── liquibase_cli.py
├── requirements.txt
├── README.md
├── migrations/
│   ├── 001-initial-schema.yaml
│   ├── 002-add-users.yaml
│   └── 003-add-indexes.yaml
└── databases/
    ├── dev.db
    ├── staging.db
    └── production.db
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Roadmap

- [ ] Support for PostgreSQL and MySQL
- [ ] Migration validation before execution
- [ ] Diff tool to compare databases
- [ ] Generate migrations from database
- [ ] Web UI for migration management
- [ ] Multiple database support in single run
- [ ] Preconditions for migrations
- [ ] Context-based migrations

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by [Liquibase](https://www.liquibase.org/)
- Built with [Click](https://click.palletsprojects.com/)
- Uses [PyYAML](https://pyyaml.org/) for YAML parsing
- Table formatting by [Tabulate](https://github.com/astanin/python-tabulate)

## 📞 Support

- 📧 Email: support@liquibasedb.example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/LiquibaseDB/issues)
- 📖 Documentation: [Wiki](https://github.com/yourusername/LiquibaseDB/wiki)

## ⚠️ Important Notes

- Always backup your database before running migrations in production
- Test migrations thoroughly in development environment
- Never modify executed migrations - create new ones instead
- Keep your changelog files in version control
- Review migration checksums regularly

---

**Made with ❤️ for database version control**

**Happy Migrating! 🚀**
