import gzip
import base64

def encode(html: str) -> str:
    utf8 = html.encode("utf-8")
    gziped = gzip.compress(utf8)
    return base64.b64encode(gziped).decode("utf-8")

def decode(base64_str: str) -> str:
    gziped = base64.b64decode(base64_str.encode("utf-8"))
    utf8 = gzip.decompress(gziped)
    return utf8.decode("utf-8")

num_tags = ["numerical", "fill-in-the-blank"]
def find_numerical(tags: list[str]) -> bool:
    for tag in tags:
        for opt in num_tags:
            if opt.startswith(tag):
                return True
    return False

def get_img_format(src: str) -> str:
    return "#img_{{{0}}}".format(src)