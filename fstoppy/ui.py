import jinja2
import web


class Handler(object):
    template_loader = jinja2.FileSystemLoader(searchpath="templates/")
    template_env = jinja2.Environment(loader=template_loader)

    def render(self, tname, context):
        return self.template_env.get_template(tname).render(context)


class Index(Handler):

    def GET(self):
        return self.render('index.html', {})


urls = (
    '/', Index,
)

app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
