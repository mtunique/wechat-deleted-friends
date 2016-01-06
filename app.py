# coding: utf-8
__author__ = 'mtunique'
import tornado
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.options import define, options, parse_command_line


from tornado.web import authenticated, asynchronous

from wdf import Wechat

define('port', default=8000, help="run on the given port", type=int)
define('debug', default=False, help='if debug model')

OBJ_MAP = {}


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)

    def get_login_url(self):
        return "/"

    def get_current_user(self):
        return self.get_secure_cookie('uid')


class GetUUIDHandler(BaseHandler):
    @asynchronous
    def get(self, *args, **kwargs):
        uid = self.get_current_user()
        if not uid or uid not in OBJ_MAP:
            tmp_wechat = Wechat()
            OBJ_MAP[tmp_wechat.uuid] = tmp_wechat
            uid = tmp_wechat.uuid

        tmp_wechat = OBJ_MAP[uid]
        self.set_secure_cookie('uid', tmp_wechat.uuid)
        self.write(tmp_wechat.showQRImage())
        self.finish()

class SubmitHandler(BaseHandler):
    @asynchronous
    @authenticated
    def get(self, *args, **kwargs):
        uid = self.get_current_user()
        OBJ = OBJ_MAP[uid]
        # self.write('dasdas')
        self.write(OBJ.second())
        self.finish()

class HomeHandler(BaseHandler):
    @asynchronous
    def get(self, *args, **kwargs):
        self.render('static/index.html')

def main():
    parse_command_line()

    import conf
    settings = {
        'cookie_secret': conf.COOKIE_SECRET,
        'xsrf_cookies': conf.XSRF_COOKIES,
    }

    app = Application(
            [
                # ('/api/articles/(?P<art_id>[a-zA-Z0-9_]+)?$',
                #   ArticleHandler),
                ('/submit',
                 SubmitHandler),

                ('/uuid',
                 GetUUIDHandler),
                ('/',
                 HomeHandler),
                (r'/(.*)', tornado.web.StaticFileHandler, {'path': './static'}),
             ],
            **settings)

    server = HTTPServer(app, xheaders=True)
    server.listen(options.port)
    IOLoop.instance().start()

if __name__ == "__main__":
    main()
