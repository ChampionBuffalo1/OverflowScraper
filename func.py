import logging
from io import StringIO
from utils import get_img_format
from bs4.element import NavigableString, Tag
from types import MappingProxyType as FrozenDict
# Setting up the logger with a custom format
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

async def extract_paragraph(child: Tag) -> str:
    assert child.name == "p"
    result = ""
    with StringIO() as string_io:
        for c in child:
            if isinstance(c, str) or isinstance(c, NavigableString):
                string_io.write(c.get_text())
            else:
                await get_content(c, string_io)
        result = string_io.getvalue()
    return result

async def extract_list(child: Tag) -> str:
    bullet, result, i = "∙ ", "", 0
    assert child.name == "ol" or child.name == "ul"
    with StringIO() as string_io:
        for c in child:
            if c == "\n": continue
            if child.name == "ol":
                i += 1
            string_io.write(bullet if child.name == "ul" else f"{str(i)}. ")
            await get_content(c, string_io)
            string_io.write("\n")
        result = string_io.getvalue()
    return result
    
async def extract_img(child: Tag) -> str:
    assert child.name == "img" and child['src'] != ""
    return get_img_format(child['src'])

async def extract_code(child: Tag) -> str:
    assert child.name == "pre"
    result = ""
    with StringIO() as string_io:
        string_io.write("<code>\n")
        for c in child:
            if c == '\n': continue
            if isinstance(c, NavigableString):
                string_io.write(c.string)
            else:
                await get_content(c, string_io)
        string_io.write("</code>\n")
        result = string_io.getvalue()
    return result

async def convert_em(child: Tag) -> str:
    assert child.name == "em"
    result = "\\text{{{0}}}"
    return result.format(child.string)

async def get_br(child: Tag):
    assert child.name == "br"
    return "\n"


jump_table = FrozenDict({
    "p": extract_paragraph,
    "ul": extract_list,
    "ol": extract_list,
    "img": extract_img,
    "pre": extract_code,
    # Extra
    "br": get_br,
    "em": convert_em 
})

async def get_content(child: Tag, contentIO: StringIO) -> None:
    # Skipping newlines
    if child == "\n":
        return
    # NavigableString do not have `child.name` property to them
    if isinstance(child, NavigableString):
        contentIO.write(child.string)
    elif child.name in jump_table:
        str_content = await jump_table[child.name](child)
        if len(str_content) == 0: return
        contentIO.write(str_content)
        contentIO.write("\n")
    else:
        logging.warning("Unknown element \"{0}\"".format(child.name))
