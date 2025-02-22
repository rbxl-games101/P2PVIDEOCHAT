import aiohttp
import asyncio
import hashlib
import subprocess
import zlib
from aiohttp import web

# Video compression using zlib
def compress_video(data):
    return zlib.compress(data)

def decompress_video(data):
    return zlib.decompress(data)

# Hashing function for file integrity
def hash_file(data):
    return hashlib.sha256(data).hexdigest()

# P2P sharing logic (basic torrent-like mechanism)
async def p2p_share(file_path, peers):
    with open(file_path, 'rb') as f:
        data = f.read()
    compressed_data = compress_video(data)
    file_hash = hash_file(compressed_data)
    
    tasks = [send_to_peer(peer, compressed_data, file_hash) for peer in peers]
    await asyncio.gather(*tasks)

async def send_to_peer(peer, data, file_hash):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'http://{peer}/receive', data=data, headers={'File-Hash': file_hash}) as resp:
            return await resp.text()

# Web server to receive files
async def receive_file(request):
    file_hash = request.headers.get('File-Hash')
    data = await request.read()
    if hash_file(data) != file_hash:
        return web.Response(text='Hash mismatch!', status=400)
    with open('received_video', 'wb') as f:
        f.write(decompress_video(data))
    return web.Response(text='Received Successfully')

# Web UI for uploading and streaming videos
async def upload_video(request):
    reader = await request.multipart()
    field = await reader.next()
    filename = field.filename
    with open(f'uploads/{filename}', 'wb') as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            f.write(chunk)
    return web.Response(text='Upload Successful')

async def stream_video(request):
    filename = request.match_info.get('filename', "")
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'video/mp4'
    await response.prepare(request)
    
    with open(f'uploads/{filename}', 'rb') as f:
        while chunk := f.read(8192):
            await response.write(chunk)
    
    await response.write_eof()
    return response

app = web.Application()
app.router.add_post('/receive', receive_file)
app.router.add_post('/upload', upload_video)
app.router.add_get('/stream/{filename}', stream_video)

if __name__ == "__main__":
    web.run_app(app, port=5000)
