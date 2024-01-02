from io import StringIO
from bs4.element import Tag
from func import get_content

# Content -> text, some li elements, img elements, code blocks
async def parse_content(content: Tag) -> str:
    contentIO = StringIO()
    for child in content.children:
        await get_content(child, contentIO)
    value = contentIO.getvalue()
    contentIO.close()
    return value

async def parse_options(list_items: list[str]) -> list[str]:
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
