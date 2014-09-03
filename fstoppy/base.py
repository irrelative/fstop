import json

import sqlite3
import subprocess
import tempfile


class Model(object):

    @classmethod
    def from_json(cls, json_dict):
        flows = [Flow.from_json(f) for f in json_dict.pop('flows', [])]
        stocks = [Stock.from_json(s) for s in json_dict.pop('stocks', [])]
        m = Model(json_dict.get('steps', 10), json_dict.get('name'))
        m.stocks = stocks
        m.flows = flows
        # Populate the to and from on flows
        stocks_dict = dict([(s.name, s) for s in m.stocks])
        for f in m.flows:
            if isinstance(f.to, basestring):
                f.to = stocks_dict.get(f.to)
            if isinstance(f.from_, basestring):
                f.from_ = stocks_dict.get(f.from_)
        return m

    @classmethod
    def get(cls, db, id_):
        json_dict = json.loads(db.select('models', where='id=$id_',
                                         vars={'id_': id_})[0].model_json)
        return cls.from_json(json_dict)


    def __init__(self, steps, name=None):
        self.steps = steps
        self.name = name
        self.flows = []
        self.stocks = []
        self.conn = sqlite3.connect(":memory:")

    def get_stock(self, stock_name):
        for s in self.stocks:
            if s.name == stock_name:
                return s
        return None

    def to_json(self):
        return {
            'steps': self.steps,
            'name': self.name,
            'flows': [f.to_json() for f in self.flows],
            'stocks': [s.to_json() for s in self.stocks]
        }

    def save(self, db, id_=None):
        json_dict = self.to_json()
        model_json = json.dumps(json_dict)
        name = json_dict['name']
        if id_:
            return db.update('models', model_json=model_json, name=name,
                             where='id=$id_', vars={'id_': id_})
        else:
            return db.insert('models', model_json=model_json, name=name)

    def delete(self, db, id_):
        db.delete('models', where='id=$id_', vars={'id_': id_})

    def run(self):
        self._initdb()
        step = 1
        while step <= self.steps:
            values = {'step': step}
            for flow in self.flows:
                # TODO, calculate value
                values[flow.name] = self.flow_value(flow, step)
            for flow in self.flows:
                if flow.to:
                    flow.to.value += values[flow.name]
                if flow.from_:
                    flow.from_.value -= values[flow.name]
            for stock in self.stocks:
                values[stock.name] = stock.value
            self._insert(values)
            step += 1

        cur = self.conn.execute('select * from results')
        return {
            'headers': [c[0] for c in cur.description],
            'rows': cur.fetchall()        
        }

    def flow_value(self, flow, step):
        prev = step - 1
        sql = 'SELECT %s AS value FROM (SELECT * FROM results WHERE step=%s)'
        return self.conn.execute(sql % (flow.formula, prev)).fetchone()[0]


    def _initdb(self):
        create_sql = 'CREATE TABLE results (step INTEGER PRIMARY KEY,\n'
        for flow in self.flows:
            create_sql += ' %s FLOAT,\n' % flow.name
        initial_values = {'step': 0}
        for stock in self.stocks:
            create_sql += ' %s FLOAT,\n' % stock.name
            initial_values[stock.name] = stock.value
        create_sql = create_sql.strip().rstrip(",")
        create_sql += ')'
        self.conn.execute(create_sql)
        if initial_values:
            self._insert(initial_values)

    def _insert(self, dict_):
        keys = dict_.keys()
        values = [dict_[k] for k in keys]
        sql = 'INSERT INTO results (%s) VALUES (%s)' % \
            (','.join(keys), ','.join('?' for k in keys))
        self.conn.execute(sql, values)

    def gen_svg(self):
        font = 'OpenSans'
        nodes = []
        vertices = []
        for s in self.stocks:
            nodes.append('"%s" [fontname="%s"]' % (s.name, font))
        for f in self.flows:
            nodes.append('"%s" [style=invis fontname="%s"]' % (f.name, font))
            if f.to and f.from_:
                vertices.append('"%s"->"%s" [label="%s" fontname="%s"]' % (f.from_.name, f.to.name, f.name, font))
            elif f.to:
                vertices.append('"%s"->"%s" [label="%s" fontname="%s"]' % (f.name, f.to.name, f.name, font))
            elif f.from_:
                vertices.append('"%s"->"%s" [label="%s" fontname="%s"]' % (f.from_.name, f.name, f.name, font))
        nodes = ';\n'.join(nodes)
        vertices = ';\n'.join(vertices)
        dot_content = '\n'.join(['digraph model {', 'size="6,6";', '%s', '%s', '}']) % (nodes, vertices)
        print dot_content

        with tempfile.NamedTemporaryFile(delete=False) as tf_input, tempfile.NamedTemporaryFile() as tf_output:
            tf_input.write(dot_content)
            tf_input.close()
            p = subprocess.Popen(['dot', '-Tsvg', tf_input.name, '-o', tf_output.name])
            p.wait()
            with open(tf_output.name) as f:
                return f.read()


class Stock(object):

    @classmethod
    def from_json(cls, json_dict):
        return Stock(json_dict.get('name', 'stock'), json_dict.get('initial', 0))

    def __init__(self, name, initial):
        self.name = name
        self.initial = initial
        self.value = initial

    def to_json(self):
        return {'name': self.name, 'initial': self.initial}


class Flow(object):

    @classmethod
    def from_json(cls, json_dict):
        return Flow(
            json_dict.get('name', 'stock'), json_dict.get('formula', '0'),
            to=json_dict.get('to'), from_=json_dict.get('from_'))

    def __init__(self, name, formula, to=None, from_=None):
        self.name = name
        self.formula = formula
        self.to = to
        self.from_ = from_

    def to_json(self):
        return {'name': self.name,
                'formula': self.formula,
                'to': self.to.name if self.to else None,
                'from_': self.from_.name if self.from_ else None}


def main():
    m = Model(96)
    s = Stock('account', 2000)
    m.stocks.append(s)
    f = Flow('deposit', '1000', to=s)
    m.flows.append(f)
    f = Flow('interest', 'account * .008', to=s)
    m.flows.append(f)
    m = Model.from_json(m.to_json())
    print m.run()

if __name__ == '__main__':
    main()
