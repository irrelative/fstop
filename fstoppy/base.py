import sqlite3
import subprocess
import tempfile


class Model(object):

    @classmethod
    def from_json(cls, json):
        pass

    def __init__(self, steps):
        self.steps = steps
        self.flows = []
        self.stocks = []
        self.conn = sqlite3.connect(":memory:")

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
        for r in self.conn.execute('select * from results').fetchall():
            print r

    def flow_value(self, flow, step):
        prev = step - 1
        sql = 'SELECT %s AS value FROM (SELECT * FROM results WHERE step=%s)'
        return self.conn.execute(sql % (flow.formula, prev)).fetchone()[0]


    def _initdb(self):
        createSql = 'CREATE TABLE results (step INTEGER PRIMARY KEY,\n'
        for flow in self.flows:
            createSql += ' %s FLOAT,\n' % flow.name
        initial_values = {'step': 0}
        for stock in self.stocks:
            createSql += ' %s FLOAT,\n' % stock.name
            initial_values[stock.name] = stock.value
        createSql = createSql.strip().rstrip(",")
        createSql += ')'
        self.conn.execute(createSql)
        if initial_values:
            self._insert(initial_values)

    def _insert(self, dict_):
        keys = dict_.keys()
        values = [dict_[k] for k in keys]
        sql = 'INSERT INTO results (%s) VALUES (%s)' % \
            (','.join(keys), ','.join('?' for k in keys))
        self.conn.execute(sql, values)

    def gen_svg(self):
        nodes = []
        vertices = []
        for s in self.stocks:
            nodes.append(s.name)
        for f in self.flows:
            nodes.append('%s [style=invis]' % f.name)
            if f.to:
                vertices.append((f.name, f.to.name, f.name))
            if f.from_:
                vertices.append((f.from_.name, f.name, f.name))
        nodes = ';\n'.join(nodes)
        vertices = ';\n'.join(['%s->%s [label="%s"]' % v for v in vertices])

        with tempfile.NamedTemporaryFile(delete=False) as tf_input, tempfile.NamedTemporaryFile() as tf_output:
            tf_input.write('''digraph unix {
    size="6,6";
    %s
    %s
    }
            ''' % (nodes, vertices))
            tf_input.close()
            p = subprocess.Popen(['dot', '-Tsvg', tf_input.name, '-o', tf_output.name])
            p.wait()
            with open(tf_output.name) as f:
                return f.read()



class Stock(object):

    def __init__(self, name, initial):
        self.name = name
        self.value = initial


class Flow(object):

    def __init__(self, name, formula, to=None, from_=None):
        self.name = name
        self.formula = formula
        self.to = to
        self.from_ = from_


def main():
    m = Model(96)
    s = Stock('account', 2000)
    m.stocks.append(s)
    f = Flow('deposit', '1000', to=s)
    m.flows.append(f)
    f = Flow('interest', 'account * .008', to=s)
    m.flows.append(f)
    m.run()


if __name__ == '__main__':
    main()
