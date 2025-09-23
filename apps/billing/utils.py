from django.db import connections


AI_COLUMNS_SQLITE = {
    'ai_generated': "BOOLEAN NOT NULL DEFAULT 0",
    'ai_confidence_score': "REAL",
    'ai_pricing_optimization': "TEXT",
    'ai_payment_prediction': "TEXT",
    'ai_revenue_insights': "TEXT",
    'insurance_verification_status': "VARCHAR(20) NOT NULL DEFAULT 'PENDING'",
    'insurance_ai_analysis': "TEXT",
    'predicted_payment_date': "DATE",
    'payment_risk_score': "REAL",
    'notes': "TEXT",
    'internal_notes': "TEXT",
    'ai_notes': "TEXT",
    'last_payment_date': "DATETIME",
}


def ensure_invoice_ai_columns(db_alias: str) -> bool:
    """Ensure billing_invoice has AI-related columns on the given DB alias.

    Only applies to SQLite; returns True if any change was made.
    Safe to call repeatedly; it is idempotent.
    """
    conn = connections[db_alias]
    if conn.vendor != 'sqlite':
        return False

    changed = False
    with conn.cursor() as cursor:
        try:
            cursor.execute("PRAGMA table_info('billing_invoice')")
            cols = {row[1] for row in cursor.fetchall()}
        except Exception:
            return False

        for col, sql_type in AI_COLUMNS_SQLITE.items():
            if col not in cols:
                try:
                    cursor.execute(f"ALTER TABLE billing_invoice ADD COLUMN {col} {sql_type}")
                    changed = True
                except Exception:
                    # Keep going; best-effort
                    pass
    return changed
