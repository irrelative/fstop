import subprocess
import tempfile

import jinja2
import web

import base


def gen_svg(model):
    nodes = []
    vertices = []
    for s in model.stocks:
        nodes.append(s.name)
    for f in model.flows:
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
        svg = gen_svg(model)
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
