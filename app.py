import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import html
from textwrap import dedent

st.set_page_config(
    page_title="Sistema de Compras",
    page_icon="🛒",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
}

hr {
    display: none;
}

div[data-testid="stVerticalBlock"] {
    gap: 1.2rem;
}

.status-bar {
    display: flex;
    gap: 16px;
    margin: 18px 0 28px 0;
}

.status-btn {
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 12px 18px;
    text-align: center;
    background: white;
    font-size: 14px;
}

.status-btn-active {
    border: 2px solid #ef4444;
    font-weight: 700;
}

.total-text {
    margin-top: 10px;
    margin-bottom: 8px;
    font-size: 15px;
}
            
div[role="radiogroup"] {
    gap: 0 !important;
    border-bottom: 1px solid #e5e7eb;
    margin-bottom: 15px;
}

div[role="radiogroup"] label {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 10px 18px !important;
    margin: 0 !important;
    min-height: auto !important;
}

div[role="radiogroup"] label p {
    color: #6b7280 !important;
    font-size: 14px;
    font-weight: 500;
}

div[role="radiogroup"] label:hover p {
    color: #111827 !important;
}

div[role="radiogroup"] label:has(input:checked) {
    background: transparent !important;
    border-bottom: 3px solid #dc2626 !important;
}

div[role="radiogroup"] label:has(input:checked) p {
    color: #111827 !important;
    font-weight: 700;
}

.card-pedido {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}

.card-pedido-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}

.card-pedido-id {
    font-size: 15px;
    font-weight: 800;
    color: #111827;
}

.card-pedido-obra {
    font-size: 13px;
    font-weight: 700;
    color: #374151;
    background: #f3f4f6;
    padding: 5px 10px;
    border-radius: 999px;
}

.card-campo-label {
    font-size: 11px;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 2px;
}

.card-campo-valor {
    font-size: 14px;
    font-weight: 500;
    color: #111827;
    margin-bottom: 10px;
    line-height: 1.35;
}

.card-material {
    font-size: 15px;
    font-weight: 600;
    color: #111827;
    line-height: 1.4;
    margin-bottom: 14px;
}

.card-info-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-top: 12px;
}

.card-info-box {
    background: #f9fafb;
    border-radius: 12px;
    padding: 10px 12px;
}

.card-valor {
    font-size: 15px;
    font-weight: 800;
    color: #166534;
}

.card-fornecedor {
    font-size: 14px;
    font-weight: 700;
    color: #1f2937;
}

.fiador-title {
    font-size: 13px;
    font-weight: 700;
    color: #374151;
    margin-bottom: 8px;
}

div[data-testid="stButton"] button {
    border-radius: 999px;
    border: 1px solid #d1d5db;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 700;
}
                                       
</style>
""", unsafe_allow_html=True)


SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_ID_PEDIDOS = st.secrets["SPREADSHEET_ID_PEDIDOS"]
SHEET_NAME_PEDIDOS = st.secrets["SHEET_NAME_PEDIDOS"]

SPREADSHEET_ID_LISTAS = st.secrets["SPREADSHEET_ID_LISTAS"]
SHEET_NAME_USUARIOS = st.secrets["SHEET_NAME_USUARIOS"]

SHEET_NAME_OBRAS = "Lista de Obras"
SHEET_NAME_FORNECEDORES = "Lista de Fornecedores"

COLUNAS_EDITAVEIS_COMPRADOR = [
    "Obra",
    "Material e quantidade",
    "Data Limite Para Entrega",
    "Prazo de Entrega do Fornecedor",
    "Data Orçamento",
    "Fornecedor",
    "Forma de Pagamento",
    "Observação",
    "Status"
]

COLUNAS_EDITAVEIS_SUPERVISOR = [
    "Status"
]

def usuario_pode_editar_pedido(pedido):
    perfil = st.session_state.get("perfil", "")
    nome_usuario = st.session_state.get("nome", "")

    status_atual = str(pedido.get("Status", "")).strip()

    if perfil == "supervisor":
        return status_atual == "Aguardando autorização"

    if perfil == "comprador":
        comprador_pedido = str(pedido.get("Comprador", "")).strip()
        return comprador_pedido == str(nome_usuario).strip()

    return False


def conectar_google_sheets():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPE
    )
    return gspread.authorize(creds)


@st.cache_data(ttl=60)
def carregar_pedidos():
    client = conectar_google_sheets()

    sheet = client.open_by_key(
        SPREADSHEET_ID_PEDIDOS
    ).worksheet(
        SHEET_NAME_PEDIDOS
    )

    dados = sheet.get_all_records()

    df = pd.DataFrame(dados)

    if "ID Pedido" in df.columns:
        df = df[
            df["ID Pedido"]
            .astype(str)
            .str.strip()
            .ne("")
        ]

    return df


@st.cache_data(ttl=60)
def carregar_usuarios():
    client = conectar_google_sheets()
    sheet = client.open_by_key(SPREADSHEET_ID_LISTAS).worksheet(SHEET_NAME_USUARIOS)
    dados = sheet.get_all_records()
    return pd.DataFrame(dados)

@st.cache_data(ttl=60)
def carregar_obras():
    client = conectar_google_sheets()
    sheet = client.open_by_key(SPREADSHEET_ID_LISTAS).worksheet(SHEET_NAME_OBRAS)
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    if df.empty or "LISTA DE OBRAS" not in df.columns:
        return []

    return sorted(
        df["LISTA DE OBRAS"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda x: x.ne("")]
        .unique()
    )


@st.cache_data(ttl=60)
def carregar_fornecedores():
    client = conectar_google_sheets()
    sheet = client.open_by_key(SPREADSHEET_ID_LISTAS).worksheet(SHEET_NAME_FORNECEDORES)
    dados = sheet.get_all_records()
    df = pd.DataFrame(dados)

    if df.empty or "Fornecedores" not in df.columns:
        return []

    return sorted(
        df["Fornecedores"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda x: x.ne("")]
        .unique()
    )

def salvar_pedido_google_sheets(id_pedido, dados_editados):
    client = conectar_google_sheets()

    sheet = client.open_by_key(
        SPREADSHEET_ID_PEDIDOS
    ).worksheet(
        SHEET_NAME_PEDIDOS
    )

    cabecalhos = sheet.row_values(1)
    coluna_id_pedido = cabecalhos.index("ID Pedido") + 1

    ids_pedidos = sheet.col_values(coluna_id_pedido)

    linha_encontrada = None

    for numero_linha, valor_id in enumerate(ids_pedidos, start=1):
        if str(valor_id).strip() == str(id_pedido).strip():
            linha_encontrada = numero_linha
            break

    if linha_encontrada is None:
        return False, "Pedido não encontrado na planilha."

    atualizacoes = []

    for coluna, valor in dados_editados.items():
        if coluna in cabecalhos:
            numero_coluna = cabecalhos.index(coluna) + 1
            atualizacoes.append({
                "range": gspread.utils.rowcol_to_a1(linha_encontrada, numero_coluna),
                "values": [[valor]]
            })

    if not atualizacoes:
        return False, "Nenhuma coluna editável foi encontrada na planilha."

    sheet.batch_update(atualizacoes)

    st.cache_data.clear()

    return True, "Pedido atualizado com sucesso."

def limpar_texto(valor):
    return str(valor).strip().lower()


def validar_login(usuario, senha):
    df_usuarios = carregar_usuarios()

    colunas_obrigatorias = ["Usuário", "Nome", "Senha", "Perfil", "Ativo"]

    for coluna in colunas_obrigatorias:
        if coluna not in df_usuarios.columns:
            st.error(f"A coluna '{coluna}' não foi encontrada na aba Usuários.")
            return None

    usuario_digitado = limpar_texto(usuario)
    senha_digitada = str(senha).strip()

    df_usuarios["Usuário_temp"] = df_usuarios["Usuário"].apply(limpar_texto)
    df_usuarios["Ativo_temp"] = df_usuarios["Ativo"].apply(limpar_texto)

    usuario_encontrado = df_usuarios[
        (df_usuarios["Usuário_temp"] == usuario_digitado) &
        (df_usuarios["Ativo_temp"].isin(["sim", "s", "ativo", "1", "true"]))
    ]

    if usuario_encontrado.empty:
        return None

    dados_usuario = usuario_encontrado.iloc[0]

    if str(dados_usuario["Senha"]).strip() != senha_digitada:
        return None

    return {
        "usuario": dados_usuario["Usuário"],
        "nome": dados_usuario["Nome"],
        "perfil": limpar_texto(dados_usuario["Perfil"])
    }


def tela_login():
    st.title("🛒 Sistema de Compras")
    st.caption("Acesse com seu usuário e senha.")

    with st.form("form_login"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        dados_usuario = validar_login(usuario, senha)

        if dados_usuario:
            st.session_state["logado"] = True
            st.session_state["usuario"] = dados_usuario["usuario"]
            st.session_state["nome"] = dados_usuario["nome"]
            st.session_state["perfil"] = dados_usuario["perfil"]
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos, ou usuário inativo.")


def logout():
    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.cache_data.clear()
        st.rerun()


def normalizar_dataframe(df):
    df = df.copy()

    for coluna in df.columns:
        df[coluna] = df[coluna].astype(str).replace("nan", "")

    return df


def aplicar_filtros(df, perfil):
    

    if perfil == "comprador":
        colunas_filtro = {
            "Solicitante": "Todos",
            "Obra": "Todas",
            "Status": "Todos",
            "Fiador": "Todos",
        }
    else:
        colunas_filtro = {
            "Comprador": "Todos",
            "Obra": "Todas",
            "Status": "Todos",
            "Fiador": "Todos",
        }

    # Guarda valores escolhidos
    for coluna, padrao in colunas_filtro.items():
        if f"filtro_{coluna}" not in st.session_state:
            st.session_state[f"filtro_{coluna}"] = padrao

    def filtrar_excluindo(coluna_ignorada):
        temp = df.copy()

        for coluna, padrao in colunas_filtro.items():
            if coluna == coluna_ignorada:
                continue

            valor = st.session_state.get(f"filtro_{coluna}", padrao)

            if valor != padrao and coluna in temp.columns:
                temp = temp[
                    temp[coluna].astype(str).str.strip() == valor
                ]

        return temp

    col1, col2, col3 = st.columns([1, 1, 2])

    if perfil == "comprador":
        filtros_render = [
            ("Solicitante", "Solicitante", "Todos", col1),
            ("Obra", "Obra", "Todas", col2),
        ]
    else:
        filtros_render = [
            ("Comprador", "Comprador", "Todos", col1),
            ("Obra", "Obra", "Todas", col2),
        ]

    for chave, coluna, padrao, container in filtros_render:
        with container:
            if coluna in df.columns:
                base_opcoes = filtrar_excluindo(coluna)

                opcoes = (
                    base_opcoes[coluna]
                    .dropna()
                    .astype(str)
                    .str.strip()
                )

                opcoes = sorted([x for x in opcoes.unique() if x != ""])

                lista_opcoes = [padrao] + opcoes

                valor_atual = st.session_state.get(f"filtro_{coluna}", padrao)

                if valor_atual not in lista_opcoes:
                    lista_opcoes.append(valor_atual)

                st.selectbox(
                    chave,
                    lista_opcoes,
                    index=lista_opcoes.index(valor_atual),
                    key=f"filtro_{coluna}"
                )

    df_filtrado = df.copy()

    for coluna, padrao in colunas_filtro.items():
        valor = st.session_state.get(f"filtro_{coluna}", padrao)

        if valor != padrao and coluna in df_filtrado.columns:
            df_filtrado = df_filtrado[
                df_filtrado[coluna].astype(str).str.strip() == valor
            ]

    if "Fiador" in df.columns:
        st.markdown('<div class="fiador-title">Fiador</div>', unsafe_allow_html=True)

        opcoes_fiador = ["Todos", "VG", "MEGA", "GRUPO", "CNPJ's Externos"]

        cols_fiador = st.columns(len(opcoes_fiador))

        for i, opcao in enumerate(opcoes_fiador):
            selecionado = st.session_state.get("filtro_Fiador", "Todos") == opcao

            label = f"✓ {opcao}" if selecionado else opcao

            with cols_fiador[i]:
                if st.button(label, key=f"btn_fiador_{opcao}", use_container_width=True):
                    st.session_state["filtro_Fiador"] = opcao
                    st.rerun()

        valor_fiador = st.session_state.get("filtro_Fiador", "Todos")

        if valor_fiador != "Todos":
            df_filtrado = df_filtrado[
                df_filtrado["Fiador"].astype(str).str.strip() == valor_fiador
            ]

    with col3:
        pesquisa = st.text_input("Pesquisar", key="pesquisa_geral")

        if pesquisa:
            pesquisa = pesquisa.lower().strip()

            df_filtrado = df_filtrado[
                df_filtrado.apply(
                    lambda linha: pesquisa in " ".join(linha.astype(str)).lower(),
                    axis=1
                )
            ]

    return df_filtrado

def obter_opcoes_status_permitidas(status_atual, perfil):
    status_atual = str(status_atual).strip()
    perfil = str(perfil).strip().lower()

    if perfil == "supervisor":
        if status_atual == "Aguardando autorização":
            return ["Aguardando autorização", "Autorizado"]
        return [status_atual]

    if perfil == "comprador":
        if status_atual == "Autorizado":
            return ["Autorizado", "Programado", "Cancelado"]

        if status_atual == "Programado":
            return ["Programado", "Pago", "Cancelado"]

        if status_atual == "Pago":
            return ["Pago", "Entregue", "Cancelado"]

        return [status_atual, "Cancelado"] if status_atual != "Cancelado" else ["Cancelado"]

    return [status_atual]


@st.dialog("Editar pedido")
def abrir_modal_edicao(pedido):
    id_pedido = str(pedido.get("ID Pedido", "")).strip()
    id_origem = str(pedido.get("ID Origem", "")).strip()

    st.markdown(f"### Pedido #{id_origem}")

    dados_editados = {}

    perfil = st.session_state.get("perfil", "")
    status_atual = str(pedido.get("Status", "")).strip()

    if perfil == "comprador":
        obras = carregar_obras()
        obra_atual = str(pedido.get("Obra", "")).strip()

        opcoes_obras = ["Selecione uma obra"] + obras

        index_obra = opcoes_obras.index(obra_atual) if obra_atual in opcoes_obras else 0

        dados_editados["Obra"] = st.selectbox(
            "Obra *",
            opcoes_obras,
            index=index_obra,
            key=f"edit_obra_{id_pedido}"
        )

        dados_editados["Material e quantidade"] = st.text_area(
            "Material e quantidade",
            value=str(pedido.get("Material e quantidade", "")).strip(),
            key=f"edit_material_{id_pedido}",
            height=100
        )

        col1, col2 = st.columns(2)

        with col1:
            dados_editados["Data Limite Para Entrega"] = st.text_input(
                "Data Limite Para Entrega",
                value=str(pedido.get("Data Limite Para Entrega", "")).strip(),
                key=f"edit_data_limite_entrega_{id_pedido}"
            )

        with col2:
            dados_editados["Prazo de Entrega do Fornecedor"] = st.text_input(
                "Prazo de Entrega do Fornecedor",
                value=str(pedido.get("Prazo de Entrega do Fornecedor", "")).strip(),
                key=f"edit_prazo_fornecedor_{id_pedido}"
            )

        col3, col4 = st.columns(2)

        with col3:
            dados_editados["Data Orçamento"] = st.text_input(
                "Data Orçamento",
                value=str(pedido.get("Data Orçamento", "")).strip(),
                key=f"edit_data_orcamento_{id_pedido}"
            )

        with col4:
            fornecedores = carregar_fornecedores()
            fornecedor_atual = str(pedido.get("Fornecedor", "")).strip()

            dados_editados["Fornecedor"] = st.text_input(
                "Fornecedor",
                value=fornecedor_atual,
                key=f"edit_fornecedor_{id_pedido}",
                placeholder="Digite ou copie da lista abaixo"
            )

            if fornecedores:
                fornecedor_sugerido = st.selectbox(
                    "Sugestões de fornecedores",
                    [""] + fornecedores,
                    key=f"edit_fornecedor_sugestao_{id_pedido}"
                )

                if fornecedor_sugerido:
                    dados_editados["Fornecedor"] = fornecedor_sugerido

        dados_editados["Forma de Pagamento"] = st.text_input(
            "Forma de Pagamento",
            value=str(pedido.get("Forma de Pagamento", "")).strip(),
            key=f"edit_forma_pagamento_{id_pedido}"
        )

        dados_editados["Observação"] = st.text_area(
            "Observação",
            value=str(pedido.get("Observação", "")).strip(),
            key=f"edit_observacao_{id_pedido}",
            height=90
        )

    opcoes_status = obter_opcoes_status_permitidas(status_atual, perfil)

    dados_editados["Status"] = st.selectbox(
        "Status",
        opcoes_status,
        index=opcoes_status.index(status_atual) if status_atual in opcoes_status else 0,
        key=f"edit_status_{id_pedido}"
    )

    col_salvar, col_fechar = st.columns(2)

    with col_salvar:
        if st.button("Salvar alterações", type="primary", use_container_width=True):

            if perfil == "comprador" and dados_editados.get("Obra") == "Selecione uma obra":
                st.error("Selecione uma obra antes de salvar.")
                return

            sucesso, mensagem = salvar_pedido_google_sheets(id_pedido, dados_editados)

            if sucesso:
                st.success(mensagem)
                st.session_state["pedido_em_edicao"] = None
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(mensagem)

    with col_fechar:
        if st.button("Cancelar", use_container_width=True):
            st.session_state["pedido_em_edicao"] = None
            st.rerun()


def mostrar_cards_pedidos(df_filtrado, permitir_edicao=False):
    if df_filtrado.empty:
        st.warning("Nenhum pedido encontrado.")
        return

    campos_detalhes = [
        "Carimbo de data/hora",
        "Solicitante",
        "Comprador",
        "Data Orçamento",
        "Observação"
    ]

    for _, pedido in df_filtrado.iterrows():
        id_pedido = str(pedido.get("ID Pedido", "")).strip()
        id_origem = str(pedido.get("ID Origem", "")).strip()
        obra = str(pedido.get("Obra", "")).strip()
        material = str(pedido.get("Material e quantidade", "")).strip()
        data_limite = str(pedido.get("Data Limite Para Compra", "")).strip()
        valor_autorizado = str(pedido.get("Valor Autorizado", "")).strip()
        fornecedor = str(pedido.get("Fornecedor", "")).strip()

        with st.container(border=True):

            col_titulo, col_editar = st.columns([12, 1])

            with col_titulo:
                st.markdown(f"**#{id_origem}** · `{obra}`")

            with col_editar:
                if permitir_edicao and usuario_pode_editar_pedido(pedido):
                    if st.button(
                        "✏️",
                        key=f"editar_{id_pedido}",
                        help="Editar pedido",
                        use_container_width=True
                    ):
                        st.session_state["pedido_em_edicao"] = id_pedido
                        st.rerun()

            st.markdown(
                f"""
                <div style="font-size:14px; line-height:1.25; margin-top:-8px; margin-bottom:6px;">
                    <strong>{material}</strong>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown(
                f"""
                <div style="
                    display:grid;
                    grid-template-columns: 1fr 1fr;
                    gap:6px;
                    font-size:12px;
                    line-height:1.2;
                    margin-bottom:16px;
                ">
                    <div>
                        <span style="color:#6b7280;">Data limite para compra</span><br>
                        <strong>{data_limite}</strong>
                    </div>
                    <div>
                        <span style="color:#6b7280;">Valor</span><br>
                        <strong style="color:#166534;">{valor_autorizado}</strong>
                    </div>
                    <div style="grid-column: 1 / -1;">
                        <span style="color:#6b7280;">Fornecedor</span><br>
                        <strong>{fornecedor}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            with st.expander("Detalhes"):
                st.markdown(
                    """
                    <div style="
                        display:grid;
                        grid-template-columns: 1fr;
                        gap:8px;
                        font-size:12px;
                        line-height:1.25;
                        padding-top:4px;
                    ">
                    """,
                    unsafe_allow_html=True
                )

                for campo in campos_detalhes:
                    valor = str(pedido.get(campo, "")).strip()

                    st.markdown(
                        f"""
                        <div style="
                            background:#f9fafb;
                            border:1px solid #e5e7eb;
                            border-radius:10px;
                            padding:8px 10px;
                        ">
                            <span style="color:#6b7280; font-size:11px; font-weight:700;">{campo}</span><br>
                            <strong style="font-size:12px; color:#111827;">{valor}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)

    pedido_em_edicao = st.session_state.get("pedido_em_edicao")

    if pedido_em_edicao:
        pedido_selecionado = df_filtrado[
            df_filtrado["ID Pedido"].astype(str).str.strip() == str(pedido_em_edicao).strip()
        ]

        if not pedido_selecionado.empty:
            abrir_modal_edicao(pedido_selecionado.iloc[0])                    

def tela_pedidos(df):
    st.title("Pedidos")

    perfil = st.session_state["perfil"]
    nome_usuario = st.session_state["nome"]

    if perfil == "comprador":
        if "Comprador" in df.columns:
            df = df[
                df["Comprador"]
                .astype(str)
                .str.strip()
                .eq(str(nome_usuario).strip())
            ]
        else:
            df = df.iloc[0:0]

    status_opcoes = [
        "Aguardando autorização",
        "Autorizado",
        "Programado",
        "Pago",
        "Entregue",
        "Cancelado",
        "Todos"
    ]

    if "status_selecionado" not in st.session_state:
        st.session_state["status_selecionado"] = "Todos"

    status_labels = []

    for status_nome in status_opcoes:
        if status_nome == "Todos":
            quantidade = len(df)
        elif "Status" in df.columns:
            quantidade = (
                df["Status"]
                .astype(str)
                .str.strip()
                .eq(status_nome)
                .sum()
            )
        else:
            quantidade = 0

        status_labels.append(f"{status_nome} ({quantidade})")

    status_atual_label = next(
        label for label in status_labels
        if label.startswith(st.session_state["status_selecionado"])
    )

    status_escolhido_label = st.radio(
        "Status",
        status_labels,
        index=status_labels.index(status_atual_label),
        horizontal=True,
        label_visibility="collapsed",
        key="radio_status_pedidos"
    )

    st.session_state["filtro_Status"] = status_escolhido_label.split(" (")[0]

    df_filtrado = aplicar_filtros(df, perfil)

    st.markdown(
        f'<div class="total-text">Total encontrado: <strong>{len(df_filtrado)}</strong> pedido(s)</div>',
        unsafe_allow_html=True
    )

    mostrar_cards_pedidos(
        df_filtrado,
        permitir_edicao=(perfil in ["comprador","supervisor"])
    )

def app_principal():
    st.sidebar.title("Sistema de Compras")
    st.sidebar.write(f"Usuário: **{st.session_state['nome']}**")
    st.sidebar.write(f"Perfil: **{st.session_state['perfil'].capitalize()}**")

    logout()

    if st.sidebar.button("Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

    df = carregar_pedidos()
    df = normalizar_dataframe(df)

    perfil = st.session_state["perfil"]

    if perfil in ["comprador", "supervisor"]:
        tela_pedidos(df)
    else:
        st.error("Perfil de usuário não reconhecido.")

if "pedido_em_edicao" not in st.session_state:
    st.session_state["pedido_em_edicao"] = None

if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    tela_login()
else:
    app_principal()