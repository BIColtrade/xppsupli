import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xppcoltrade.settings')
django.setup()

from django.db import connection
from collections import defaultdict

def get_table_schema():
    with connection.cursor() as cursor:
        # Obtener todas las tablas
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        schema = {}
        for table in tables:
            cursor.execute(f"""
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, [table])

            columns = []
            for row in cursor.fetchall():
                col_name, data_type, is_nullable, col_default = row
                columns.append({
                    'name': col_name,
                    'type': data_type,
                    'nullable': is_nullable == 'YES',
                    'default': col_default
                })

            schema[table] = columns

        return schema

def get_table_fks():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name
        """)

        fks = defaultdict(list)
        for row in cursor.fetchall():
            table, col, fk_table, fk_col = row
            fks[table].append({
                'column': col,
                'references': f"{fk_table}.{fk_col}"
            })

        return fks

schema = get_table_schema()
fks = get_table_fks()

for table in sorted(schema.keys()):
    print(f"\n{'='*80}")
    print(f"TABLE: {table}")
    print(f"{'='*80}")

    for col in schema[table]:
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        print(f"  {col['name']:<40} {col['type']:<15} {nullable}{default}")

    if table in fks:
        print(f"\n  Foreign Keys:")
        for fk in fks[table]:
            print(f"    {fk['column']:<40} → {fk['references']}")
