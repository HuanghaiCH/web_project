#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging;

from aiohttp.web_middlewares import middleware

from www.models import User

logging.basicConfig(level=logging.INFO)

import asyncio, os, json, time
from datetime import datetime
from coreweb import get

from aiohttp import web
from jinja2 import Environment, FileSystemLoader

import ocm
from coreweb import add_routes, add_static


"""
init_jinja2(app, filters=dict(datetime=datetime_filter))
jinja2模块中有一个名为Enviroment的类，这个类的实例用于存储配置和全局对象，然后从文件系统或其他位置中加载模板。
Environment支持两种加载方式：PackageLoader：包加载器 / FileSystemLoader：文件系统加载器
"""
def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            # logging.info("name:%s, f:%s" % (name, f))
            env.filters[name] = f
    app['__templating__'] = env


"""
中间件工厂，创建与传递参数的中间件功能
例如，这是一个简单的中间件工厂：
def middleware_factory(text):
    @middleware
    async def sample_middleware(request, handler):
        resp = await handler(request)
        resp.text = resp.text + text
        return resp
    return sample_middleware
请记住，与常规中间件相反，您需要中间件工厂的结果而不是函数本身。因此，当将中间件工厂传递给应用程序时，您实际上需要调用它：

logger_factory 作用:输出request.method，request.path
"""


async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        response = await handler(request)
        return response

    return logger

"""
data_factory 作用：
1、如果request.method == POST，则继续判断
2、判断媒体格式类型，如果是JSON数据格式，转化成json数据；如果是application/x-www-form-urlencoded 表格格式，初始化post
"""

async def data_factory(app, handler):
    async def parse_data(request):
        if request.method == 'POST':
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()
                logging.info('request json: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()
                logging.info('request form: %s' % str(request.__data__))
        response = await handler(request)
        return response

    return parse_data


async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                resp = web.Response(
                    body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r, int) and r >= 100 and r < 600:
            return web.Response(r)
        if isinstance(r, tuple) and len(r) == 2:
            t, m = r
            if isinstance(t, int) and t >= 100 and t < 600:
                return web.Response(t, str(m))
        # default:
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
        return resp

    return response


def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)


# 老式的写法 @asyncio.coroutine
#           def init(loop):
async def init(loop):
    await ocm.create_pool(loop=loop, host='127.0.0.1', port=33339, user='test', password='123qwe!', db='test')

    # aiohttp 提供了中间件，通过中间件，可以定制请求处理程序
    # 中间件必须有2个接收参数，一个是request请求实例，一个是处理程序，返回一个相应或者异常报错。
    # 中间件的一个常见用途是实现自定义错误页面。以下示例将使用 JSON 响应呈现 404 错误，这可能适用于 JSON REST 服务：
    '''
        @web.middleware
        async def error_middleware(request, handler):
            try:
                response = await handler(request)
                if response.status != 404:
                    return response
                message = response.message
            except web.HTTPException as ex:
                if ex.status != 404:
                    raise
                message = ex.reason
            return web.json_response({'error': message})
        
        app = web.Application(middlewares=[error_middleware])
    '''
    app = web.Application(loop=loop, middlewares=[
        logger_factory, response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 19000)
    logging.info('server started at http://127.0.0.1:19000...')
    return srv

if __name__ == '__main__':
    # 获取当前事件循环。
    # 如果当前 OS 线程没有设置当前事件循环，该 OS 线程为主线程，并且 set_event_loop() 还没有被调用，则 asyncio 将创建一个新的事件循环并将其设为当前事件循环。
    # 由于此函数具有相当复杂的行为（特别是在使用了自定义事件循环策略的时候），更推荐在协程和回调中使用 get_running_loop() 函数而非 get_event_loop()。
    # 应该考虑使用 asyncio.run() 函数而非使用低层级函数来手动创建和关闭事件循环。
    loop = asyncio.get_event_loop()

    # 运行直到 future ( Future 的实例 ) 被完成
    # 如果参数是 coroutine object ，将被隐式调度为 asyncio.Task 来运行。
    # 返回 Future 的结果 或者引发相关异常。
    loop.run_until_complete(init(loop))

    # 运行事件循环直到 stop() 被调用。
    # 如果 stop() 在调用 run_forever() 之前被调用，循环将轮询一次 I/O 选择器并设置超时为零，再运行所有已加入计划任务的回调来响应 I/O 事件（以及已加入计划任务的事件）
    # ，然后退出。
    # 如果 stop() 在 run_forever() 运行期间被调用，循环将运行当前批次的回调然后退出。 请注意在此情况下由回调加入计划任务的新回调将不会运行；
    # 它们将会在下次 run_forever() 或 run_until_complete() 被调用时运行。
    loop.run_forever()
