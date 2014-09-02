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
        model = base.Model(96)
        s = base.Stock('account', 2000)
        model.stocks.append(s)
        f = base.Flow('deposit', '1000', to=s)
        model.flows.append(f)
        f = base.Flow('interest', 'account * .008', to=s)
        model.flows.append(f)
        svg = model.gen_svg()
        return self.render('index.html', {'svg': svg})


class ViewModel(Handler):

    def GET(self, model_id):
        model = base.Model.get(self.db, model_id)
        svg = model.gen_svg()
        return self.render('index.html',
                           {'svg': svg, 'model': json.dumps(model.to_json(), indent=4)})

    def POST(self, model_id):
        inp = web.input(model=None)
        json_inp = json.loads(inp.model)
        base.Model.from_json(json_inp).save(self.db, model_id)
        return web.seeother('/model/%s' % model_id)


class RunModel(Handler):

    def POST(self):
        inp = web.input(model=None)
        print inp.model
        json_inp = json.loads(inp.model)
        model = base.Model.from_json(json_inp)
        results = model.run()
        return self.render('result_table.html', results)


class About(Handler):

    def GET(self):
        return self.render('about.html', {})


urls = (
    '/', Index,
    '/about', About,
    '/model/(\d+)', ViewModel,
    '/run', RunModel,
)

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
