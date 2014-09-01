import sqlite3

class Model(object):

    def __init__(self, steps):
        self.steps = steps
        self.flows = []
        self.stocks = []
        self.conn = sqlite3.connect(":memory:")

    def run(self):
        self._initdb()
        step = 1
        while step <= self.steps:
            print "step ", step
            values = {'step': step}
            for flow in self.flows:
                # TODO, calculate value
                values[flow.name] = 12
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
    m = Model(10)
    f = Flow('flow1', '10')
    m.flows.append(f)
    s = Stock('stock1', 35)
    m.stocks.append(s)
    m.run()


if __name__ == '__main__':
    main()