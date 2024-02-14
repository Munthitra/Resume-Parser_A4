import base64
import io
import dash
from dash import dcc, html, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_table
from PyPDF2 import PdfReader
import spacy

nlp = spacy.load("en_core_web_md")

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("PDF Resume Entity Extractor"),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select PDF Resume')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),
    html.Div(id='output-data-upload'),
])


def extract_entities_from_text(text):
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append((ent.text, ent.label_))
    return entities


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        reader = PdfReader(io.BytesIO(decoded))
        page = reader.pages[0]
        text = page.extract_text()
        entities = extract_entities_from_text(text)

        return html.Div([
            html.H5(filename),
            dash_table.DataTable(
                id='datatable',
                columns=[
                    {"name": "Entity", "id": "Entity"},
                    {"name": "Label", "id": "Label"}
                ],
                data=[{"Entity": ent[0], "Label": ent[1]} for ent in entities],
            ),
        ])
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])


@app.callback(Output('output-data-upload', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(contents, filename):
    if contents is None:
        raise PreventUpdate

    return parse_contents(contents, filename)


if __name__ == '__main__':
    app.run_server(debug=True)
