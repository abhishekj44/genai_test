# TODO: this should be replaced with standard library at some point when that is deployed internally

import logging
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from typing import Iterator, List, Union
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl


logger = logging.getLogger(__name__)

from typing import List


def _make_header_md(header_cell_content: List[str]) -> str:
    header_row = "| " + " | ".join(header_cell_content) + " |"
    separator_row = "| " + " | ".join("---" for _ in header_cell_content) + " |"
    return header_row + "\n" + separator_row + "\n"


def __make_body_row_md(row_cell_content: List[str]) -> str:
    return "| " + " | ".join(row_cell_content) + " |"


def _make_body_md(rows_cell_contents: List[List[str]]) -> str:
    body_content = ""
    for row in rows_cell_contents:
        body_content += __make_body_row_md(row) + "\n"
    return body_content


def make_markdown_table(cell_contents: List[List[str]]) -> str:
    if len(cell_contents) == 1:
        return _make_body_md([cell_contents[0]])
    else:
        header_row = cell_contents[0]
        body_rows = cell_contents[1:]
        header_md = _make_header_md(header_row)
        body_md = _make_body_md(body_rows)
        return header_md + body_md


def _t_docx_to_string(table: Table) -> str:
    contents: List[List[str]] = []
    for row in table.rows:
        row_contents = []
        for cell in row.cells:
            row_contents.append(cell.text)
        contents.append(row_contents)

    return make_markdown_table(contents)


def _p_docx_to_string(block: Paragraph) -> str:
    block_text = block.text
    return block_text


UNKNOWN_BLOCK_TYPE_WARNING = "{block} has an unknown type.  Not of Paragraph or Table"


def _block_to_string(block: Union[Paragraph, Table]) -> str:
    if isinstance(block, Paragraph):
        return _p_docx_to_string(block)
    elif isinstance(block, Table):
        return _t_docx_to_string(block)
    else:
        logging.warning(UNKNOWN_BLOCK_TYPE_WARNING.format(block=block))
        return ""


def _iter_block_items(parent: Document) -> Iterator[Union[Paragraph, Table]]:
    """
    Yield each paragraph and table in order of occurrence in a document, represented by a `parent` element.

    :param parent: The parent element representing the document.
    :type parent: Element
    :returns: Iterator over paragraphs and tables.
    :rtype: Iterator

    """

    for child in parent.element.body:
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def docx_to_string(doc: Document) -> str:
    """
    Convert a DOCX document to a string representation.

    :param doc: The input DOCX document.
    :type doc: Document
    :returns: A string representing the document content.
    :rtype: str
    """
    full_text = ""
    for block in _iter_block_items(doc):
        full_text += "\n" + _block_to_string(block)
    return full_text
