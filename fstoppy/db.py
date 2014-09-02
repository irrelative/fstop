schema = '''
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_json TEXT
)
'''

if __name__ == '__main__':
    import ui
    ui.Handler.db.query(schema)
