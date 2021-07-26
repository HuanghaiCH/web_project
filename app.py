#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio
from aiohttp import web

logging.basicConfig(level=logging.INFO)


def dealpost(request):
    return web.Response(body=b'<h1>home</h1>', content_type='text/html')


async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', dealpost)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 39000)
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
