import dash
from dash import dcc, html, Input, Output, State, dash_table, callback
import pandas as pd
import requests
from io import StringIO
import os

# Инициализация приложения Dash
app = dash.Dash(__name__)
app.title = "CRM для управления заказами"

# Путь к локальному файлу для сохранения изменений
LOCAL_TSV = "chipotle_local.tsv"


def load_data():
    # Если локальный файл существует — грузим из него
    if os.path.exists(LOCAL_TSV):
        return pd.read_csv(LOCAL_TSV, sep='\t')

    # Если локального файла нет — грузим из удаленного источника и сохраняем в локальный файл
    url = "https://raw.githubusercontent.com/justmarkham/DAT8/refs/heads/master/data/chipotle.tsv"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверяем, что запрос успешен
        df = pd.read_csv(StringIO(response.text), sep='\t')

        # Убедимся, что данные имеют правильную структуру
        if 'order_id' not in df.columns:
            df['order_id'] = range(1, len(df) + 1)  # Добавляем order_id, если его нет

        # Сохраняем данные в локальный файл
        df.to_csv(LOCAL_TSV, sep='\t', index=False)
        return df
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return pd.DataFrame()  # Возвращаем пустой DataFrame в случае ошибки

def save_data(df):
    # Всегда сохраняем в ЛОКАЛЬНЫЙ файл
    df.to_csv(LOCAL_TSV, sep='\t', index=False)


# Загрузка данных (из локального файла или удаленного источника)
df = load_data()

app.layout = html.Div([
    html.H1("CRM для управления заказами Chipotle", style={'textAlign': 'center'}),

    dash_table.DataTable(
        id='orders-table',
        columns=[
            {"name": "Order ID", "id": "order_id"},
            {"name": "Quantity", "id": "quantity"},
            {"name": "Item Name", "id": "item_name"},
            {"name": "Choice Description", "id": "choice_description"},
            {"name": "Item Price", "id": "item_price"},
        ],
        data=df.to_dict('records'),
        editable=True,
        filter_action="native",
        sort_action="native",
        row_deletable=True,
        page_action="native",
        page_size=10,
        style_table={'margin': '20px'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
    ),

    html.Hr(style={'margin': '20px'}),

    html.H2("Добавить заказ", style={'textAlign': 'left', 'margin': '20px'}),

    html.Div([
        dcc.Input(id="item-name", placeholder="Название товара", style={'margin': '10px', 'width': '95%'}),
        dcc.Input(id="quantity", type="number", placeholder="Количество", style={'margin': '10px', 'width': '95%'}),
        dcc.Input(id="item-price", placeholder="Цена", style={'margin': '10px', 'width': '95%'}),
        html.Button("Добавить", id="add-button", style={'margin': '20px', 'width': '95%'})
    ], style={'width': '50%', 'margin': 'auto'}),

    html.Div(id='output-message', style={'color': 'green', 'margin': '20px'})
])


@callback(
    [Output('orders-table', 'data'),
     Output('output-message', 'children')],
    [Input('add-button', 'n_clicks'),
     Input('orders-table', 'data_timestamp')],
    [State('orders-table', 'data'),
     State('item-name', 'value'),
     State('quantity', 'value'),
     State('item-price', 'value')]
)
def update_table(add_clicks, edit_timestamp, current_data, item_name, quantity, item_price):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'add-button':
        if not all([item_name, quantity, item_price]):
            return dash.no_update, "Заполните все поля!"

        # Создаем новый заказ
        new_order = {
            'order_id': max([x['order_id'] for x in current_data]) + 1,
            'item_name': item_name,
            'quantity': quantity,
            'item_price': item_price,
            'choice_description': ''
        }

        # Обновляем данные
        updated_data = current_data + [new_order]
        save_data(pd.DataFrame(updated_data))  # Сохраняем в ЛОКАЛЬНЫЙ файл
        return updated_data, "Заказ добавлен!"

    elif triggered_id == 'orders-table':
        # Сохраняем изменения при редактировании таблицы
        save_data(pd.DataFrame(current_data))
        return dash.no_update, "Изменения сохранены!"

    return dash.no_update, dash.no_update


if __name__ == '__main__':
    app.run_server(debug=True)