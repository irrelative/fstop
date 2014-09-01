import web

class Index(object):

    def GET(self):
        return "hello"

urls = (
    '/', Index,
)
app = web.application(urls, globals())

if __name__ == '__main__':
    app.run()
