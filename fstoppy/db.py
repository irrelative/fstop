schema = [
'''
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    model_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''',
'''
CREATE TRIGGER models_updated_at_trigger AFTER UPDATE ON models FOR EACH ROW
  BEGIN
    UPDATE models SET updated_at = CURRENT_TIMESTAMP WHERE id = old.id;
  END;

'''
]

if __name__ == '__main__':
    import ui
    for sql in schema:
        ui.Handler.db.query(sql)
