#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import functools
import aiohttp

async def handle_url_requests(request):
    url_param = request.match_info['key']


def get(path):
    """
    Define decorator @get('/path')
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

def get(path):
    """
    Define decorator @post('/path')
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator


