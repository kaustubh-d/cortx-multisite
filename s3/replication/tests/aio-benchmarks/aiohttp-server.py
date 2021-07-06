#!/usr/bin/env python3

from aiohttp import web
import hashlib

# Route table declaration
routes = web.RouteTableDef()

@routes.put('/{resource_id}')
async def put_api_handler(request):
    resource_id = request.match_info['resource_id']
    print('API: PUT /{}'.format(resource_id))

    data = await request.read()

    return web.json_response({"received_size": len(data)}, status=200)

@routes.get('/{resource_id}')
async def get_api_handler(request):
    resource_id = request.match_info['resource_id']
    print('API: GET /{}'.format(resource_id))

    return web.json_response({"resource": resource_id}, status=200)

if __name__ == '__main__':
    app = web.Application()

    # Setup application routes.
    app.add_routes(routes)

    # Start the REST server.
    web.run_app(app, host="0.0.0.0", port="80")
