import pdfplumber


def curves_to_edges(cs):
    """See https://github.com/jsvine/pdfplumber/issues/127"""
    edges = []
    for c in cs:
        edges += pdfplumber.utils.rect_to_edges(c)
    return edges


def extract_text_from_pdf(pdf_file) -> str:
    table_settings = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}

    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        table_idx = 0

        for page_idx, page in enumerate(pdf.pages, start=1):
            text += f"\n ---PAGE {page_idx}---\n"
            text += page.extract_text(x_tolerance=1)

            # tables = page.extract_tables(table_settings={"text_x_tolerance": 1})
            tables = page.extract_tables(table_settings=table_settings)

            for table in tables:
                table_idx += 1
                text += f"\n ---TABLE {table_idx}---\n"

                row_length = None

                for row in table:
                    if row_length is None:
                        row_length = len(row)
                    elif row_length != len(row):
                        print("ERROR different number of rows in a table")
                        # print(pdf_filepath)

                    row = [str(item) if item is not None else "" for item in row]
                    row = [item.replace("\n", " ") for item in row]
                    text += "\n" + " | ".join(row)
        return text
