import base64
import io
import dash
from dash import dcc, html, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_table
import dash_html_components as html_comp
from PyPDF2 import PdfReader
import spacy
from fpdf import FPDF
import os
import flask

nlp = spacy.load("en_core_web_md")

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("PDF Resume Entity Extractor"),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select PDF Resumes')
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
        multiple=True
    ),
    html.Div(id='output-data-upload'),
    html.Div(id='dummy-div')
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

        table_data = [{"Entity": ent[0], "Label": ent[1]} for ent in entities]

        return html.Div([
            html.H5(filename),
            dash_table.DataTable(
                id={
                    'type': 'datatable',
                    'index': filename
                },
                columns=[
                    {"name": "Entity", "id": "Entity"},
                    {"name": "Label", "id": "Label"}
                ],
                data=table_data,
            ),
            html.Button("Download as PDF", id={'type': 'pdf-download', 'index': filename})
        ])
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])


def generate_pdf(filename, table_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for row in table_data:
        for item in row:
            pdf.cell(40, 10, txt=item, ln=True)
    
    pdf_filename = filename.split('.')[0] + '_extracted_entities.pdf'
    print(pdf_filename)
    pdf.output(pdf_filename)
    
    return pdf_filename


@app.callback([Output('output-data-upload', 'children'),
               Output('output-data-upload', 'style')],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')])
def update_output(list_of_contents, list_of_filenames):
    if list_of_contents is None or list_of_filenames is None:
        raise PreventUpdate

    outputs = []
    for content, filename in zip(list_of_contents, list_of_filenames):
        outputs.append(parse_contents(content, filename))

    return outputs, {'overflowY': 'scroll', 'height': '500px'}


@app.callback(
    Output('dummy-div', 'children'),
    [Input({'type': 'pdf-download'}, 'n_clicks')],
    [State({'type': 'datatable'}, 'data'),
     State({'type': 'datatable'}, 'columns'),
     State({'type': 'datatable'}, 'id')]
)
def download_pdf(n_clicks, data, columns, table_id):
    if n_clicks:
        table_data = [columns]
        for row in data:
            table_data.append([row[col['id']] for col in columns])
        pdf_filename = generate_pdf(table_id['index'], table_data)
        return html_comp.A(html_comp.Button('Download PDF'), href='/download/' + pdf_filename)


@app.server.route('/download/<path:path>')
def serve_static(path):
    root_dir = os.getcwd()
    return flask.send_from_directory(root_dir, path)


if __name__ == '__main__':
    app.run_server(debug=True)
