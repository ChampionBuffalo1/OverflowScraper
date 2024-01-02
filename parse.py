import logging
from io import StringIO
from utils import get_img_format
from bs4.element import NavigableString, Tag
from types import MappingProxyType as FreezeDict
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
                string_io.write(await get_content(c))
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
            string_io.write(await get_content(c))
            string_io.write("\n")
        result = string_io.getvalue()
    return result
    
async def extract_img(child: Tag) -> str:
    assert child.name == "img" and child['src'] != ""
    return get_img_format(child['src'])

async def extract_code(child: Tag) -> str:
    return ""

jump_table = FreezeDict({
    "p": extract_paragraph,
    "ul": extract_list,
    "ol": extract_list,
    "img": extract_img,
    "pre": extract_code
})

# Content -> text, some li elements, img elements, code blocks
async def get_content(content: Tag) -> str:
    contentIO = StringIO()
    for child in content.children:
        # Skipping newlines
        if child == "\n": continue
        # NavigableString do not have `child.name` property to them
        elif isinstance(child, NavigableString):
            contentIO.write(child.string)
        elif child.name in jump_table:
            str_content = await jump_table[child.name](child)
            if len(str_content) == 0: continue
            contentIO.write(str_content)
            contentIO.write("\n")
        else:
            logging.warning("Unknown element \"{0}\"".format(child.name))
            # contentIO.write(child.get_text())
    value = contentIO.getvalue()
    contentIO.close()
    return value

async def get_options(list_items: list[str]) -> list[str]:
    opts = []
    # Options can either be text or images
    for li in list_items:
        if li == "\n": continue
        for child in li.contents:
            if child.name == "img":
                opts.append(child["src"])
            else:
                opts.append(child.get_text())
    return opts
