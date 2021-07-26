import ocm
from models import User, Blog, Comment
import asyncio


async def run():
    ocm.create_pool(user='test', password='123qwe!', database='test')

    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')

    u.save()


if __name__ == '__main__':
    asyncio.run(run())