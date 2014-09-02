import jinja2
import web

import base



class Handler(object):
    template_loader = jinja2.FileSystemLoader(searchpath="templates/")
    template_env = jinja2.Environment(loader=template_loader)

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


class About(Handler):

    def GET(self):
        return self.render('about.html', {})


urls = (
    '/', Index,
    '/about', About,
)

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
