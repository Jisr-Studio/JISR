"""Read alpha bounds of FFmpeg's non-interlaced RGBA PNG without dependencies."""
import struct
import zlib


def alpha_bounds(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Expected a PNG subtitle image')
    offset, chunks = 8, []
    while offset < len(data):
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        kind, payload = data[offset + 4:offset + 8], data[offset + 8:offset + 8 + length]
        if kind == b'IHDR':
            width, height, depth, color, _, _, interlace = struct.unpack('>IIBBBBB', payload)
            if depth != 8 or color != 6 or interlace or width * height > 33554432:
                raise ValueError('Unsupported subtitle PNG')
        elif kind == b'IDAT':
            chunks.append(payload)
        elif kind == b'IEND':
            break
        offset += length + 12
    raw = zlib.decompress(b''.join(chunks))
    stride, previous = width * 4, bytearray(width * 4)
    if len(raw) != (stride + 1) * height:
        raise ValueError('Invalid subtitle PNG size')
    top, bottom = None, None
    for y in range(height):
        start = y * (stride + 1)
        method, row = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        if method not in range(5):
            raise ValueError('Invalid PNG filter')
        if method:
            for x in range(stride):
                left = row[x - 4] if x >= 4 else 0
                up = previous[x]
                if method == 1:
                    predictor = left
                elif method == 2:
                    predictor = up
                elif method == 3:
                    predictor = (left + up) // 2
                else:
                    corner = previous[x - 4] if x >= 4 else 0
                    p = left + up - corner
                    dl, du, dc = abs(p - left), abs(p - up), abs(p - corner)
                    predictor = left if dl <= du and dl <= dc else up if du <= dc else corner
                row[x] = (row[x] + predictor) & 255
        if any(row[3::4]):
            if top is None:
                top = y
            bottom = y
        previous = row
    return None if top is None else (top, bottom)
