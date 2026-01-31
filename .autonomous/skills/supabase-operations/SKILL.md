---
id: supabase-operations
name: Supabase Operations
version: 1.0.0
category: database
description: Database operations, DDL, RLS policies, and migrations for Supabase
trigger: When working with Supabase, database operations, migrations
inputs:
  - name: operation
    type: string
    required: true
    description: "Operation type"
  - name: target
    type: string
    required: true
    description: "Table, policy, or migration name"
  - name: definition
    type: object
    required: false
    description: "Schema or policy definition"
outputs:
  - name: operation_result
    type: object
    description: Result of operation
  - name: sql_executed
    type: string
    description: SQL that was run
commands:
  - execute
  - create-table
  - alter-table
  - create-policy
  - apply-migration
  - verify-rls
---

# Supabase Operations

## Purpose

Safely perform database operations on Supabase with proper DDL, RLS, and migration handling.

## When to Use

- Creating or modifying tables
- Setting up RLS policies
- Applying migrations
- Querying data

---

## Command: execute

### Input
- `operation`: Type of operation
- `target`: What to operate on
- `definition`: Schema/policy details

### Process

1. **Validate operation**
   - Check permissions
   - Verify target exists (or doesn't)
   - Validate definition

2. **Generate SQL**
   - Create safe, valid SQL
   - Add comments
   - Include rollback

3. **Execute via MCP**
   - Use supabase MCP
   - Handle errors
   - Log operations

4. **Verify result**
   - Check success
   - Validate changes
   - Update documentation

### Output

```yaml
operation_result:
  operation: "create_table"
  target: "users"
  status: "success"

  sql_executed: |
    CREATE TABLE users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email VARCHAR(255) UNIQUE NOT NULL,
      created_at TIMESTAMP DEFAULT NOW()
    );

    COMMENT ON TABLE users IS 'User accounts';

  verification:
    table_exists: true
    columns_match: true
    indexes_created: ["users_email_idx"]

  migration_recorded: true
  migration_file: "migrations/20260130_create_users.sql"
```

---

## Common Operations

### Create Table
```sql
CREATE TABLE table_name (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Create RLS Policy
```sql
CREATE POLICY "Users can read own data"
  ON users
  FOR SELECT
  USING (auth.uid() = id);
```

### Apply Migration
- Generate migration file
- Execute SQL
- Record in migration log
- Verify success

---

## Safety Rules

1. **Always use transactions** where possible
2. **Test on dev first** before production
3. **Generate rollback** for every change
4. **Verify after execution**
5. **Document in migrations**

---

## Examples

### Example: Create Users Table

```markdown
**Operation:** create_table
**Target:** users
**Definition:**
  - id: UUID PK
  - email: VARCHAR UNIQUE
  - name: VARCHAR

**Result:**
✓ Table created
✓ Indexes created
✓ Migration recorded
✓ RLS enabled (no policies yet)
```

### Example: Add RLS Policy

```markdown
**Operation:** create_policy
**Target:** users
**Definition:**
  - Name: "Users read own"
  - Action: SELECT
  - Using: auth.uid() = id

**Result:**
✓ Policy created
✓ Verified with test query
✓ Security test passing
```
