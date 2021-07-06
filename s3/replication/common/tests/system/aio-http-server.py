#!/usr/bin/env python3

from aiohttp import web
import hashlib

# Route table declaration
routes = web.RouteTableDef()


# PUT API.
@routes.put('/{resource1_id}/{resource2_id}')  # noqa: E302
async def put_object(request):
    """Put API handler"""

    resource1_id = request.match_info['resource1_id']
    resource2_id = request.match_info['resource2_id']
    print('API: PUT /{}/{}'.format(resource1_id, resource2_id))

    data = await request.read()
    # Send back same data.

    hash = hashlib.md5()
    hash.update(data)
    md5 = hash.hexdigest()

    print("API: PUT /{}/{} - md5 = {}".format(resource1_id, resource2_id, md5))

    headers = {"ETag": "\"" +  md5 + "\""}

    return web.json_response(status=200, headers=headers)



if __name__ == '__main__':
    app = web.Application()

    # Setup application routes.
    app.add_routes(routes)

    # Start the REST server.
    web.run_app(app, host="0.0.0.0", port="80")
