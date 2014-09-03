# pylint: disable=invalid-name,missing-docstring
import json
import jinja2
import web

import base


class Handler(object):
    template_loader = jinja2.FileSystemLoader(searchpath="templates/")
    template_env = jinja2.Environment(loader=template_loader, autoescape=True)
    db = web.database(dbn='sqlite', db='fstoppy.db')

    def render(self, tname, context):
        return self.template_env.get_template(tname).render(context)


class Index(Handler):

    def GET(self):
        models = self.db.select('models')
        return self.render('index.html', {'models': models})


class ViewModel(Handler):

    def GET(self, model_id):
        model = base.Model.get(self.db, model_id)
        svg = model.gen_svg()
        context = {'svg': svg, 'model_json': json.dumps(model.to_json(), indent=4),
                   'model_id': model_id, 'model': model}
        return self.render('model.html', context)

    def POST(self, model_id):
        inp = web.input(model=None)
        json_inp = json.loads(inp.model)
        base.Model.from_json(json_inp).save(self.db, model_id)
        return web.seeother('/model/%s' % model_id)


class RunModel(Handler):

    def POST(self):
        inp = web.input(model=None)
        json_inp = json.loads(inp.model)
        model = base.Model.from_json(json_inp)
        results = model.run()
        results['json'] = json.dumps(results)
        return self.render('result_table.html', results)


class NewModel(Handler):

    form = web.form.Form(
        web.form.Textarea('name', web.form.notnull,
                          description="Model Name"),
        web.form.Textarea('model_json', web.form.notnull,
                          description="Model JSON"),
        web.form.Button('Create'))

    def GET(self):
        f = self.form()
        f.fill({'model_json': json.dumps(base.Model(100).to_json())})
        return self.render('new_model.html', {'form': f})

    def POST(self):
        f = self.form()
        if not f.validates():
            return self.render('new_model.html', {'form': f})
        id_ = base.Model.from_json(json.loads(f.d.model_json)).save(self.db)
        return web.seeother('/model/%s' % id_)


class Stock(Handler):

    def POST(self, model_id):
        model = base.Model.get(self.db, model_id)
        inp = web.input(name=None, initial=0)
        stock = base.Stock(inp.name, float(inp.initial))
        model.stocks.append(stock)
        model.save(self.db, model_id)
        return web.seeother('/model/%s' % model_id)


class Flow(Handler):

    def POST(self, model_id):
        model = base.Model.get(self.db, model_id)
        inp = web.input(name=None, formula=None, to=None, from_=None)
        to = model.get_stock(inp.to)
        from_ = model.get_stock(inp.from_)
        flow = base.Flow(inp.name, inp.formula, to, from_)

        model.flows.append(flow)
        model.save(self.db, model_id)
        return web.seeother('/model/%s' % model_id)


urls = (
    r'/', Index,
    r'/model/(\d+)', ViewModel,
    r'/model/(\d+)/stock', Stock,
    r'/model/(\d+)/flow', Flow,
    r'/run', RunModel,
    r'/new', NewModel,
)

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
