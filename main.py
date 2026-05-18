from flask import Flask, session, jsonify, render_template, request, send_from_directory, redirect, url_for, flash
import os

#from dotenv import load_dotenv

#load_dotenv()

import requests

import logging
from google.auth import jwt

import pandas as pd
from pandas import Series

import plotly.graph_objs as go
import plotly.express as px

from google.cloud import storage
from google.cloud import firestore
from google.auth import jwt

from datetime import date, datetime, timezone, timedelta

from ropt.normalization import Maximize, Minimize, RatioMaximize, RatioMinimize, LogisticMaximize, LogisticMinimize
from ropt.normalization import SafeRatioMaximize, SafeRatioMinimize
from ropt.normalization import LogisticMaximize, LogisticMinimize

from ropt.normalizer import importance_factors, robust_normalize, normalize, ranking_normalize, outlier_removal

#from composite_indicator.util import BOD_Calculation, Entropy_Calculation, PCA_Calculation
#from composite_indicator.methods import equal_weights, specialist_weights
#from composite_indicator.objectives import MaxCorrel, PCA, MaxEntropy, MinUncertanty
from ropt.means import normal_weighted_arithimetic_mean
from werkzeug.utils import secure_filename

from io import BytesIO

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("No FLASK_SECRET_KEY set in environment variables")

processar_dados_function_url = os.environ.get('PROCESSAR_DADOS_FUNCTION_URL', 'http://localhost:5001/processardados')
UPLOAD_FOLDER = 'files'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSAR_DADOS_FUNCTION_URL'] = processar_dados_function_url
#app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL')

info = {}

fuso_horario = timezone(timedelta(hours=-3))

# Project ID is determined by the GCLOUD_PROJECT environment variable
db = firestore.Client()

# Configure this environment variable via app.yaml
CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET')

ALLOWED_EXTENSIONS = ['csv', 'xlsx', 'xls']

#Progresso = 0

# rotas
@app.route('/index')
def index():
    return redirect('/') #, 304

@app.route("/")
def homepage():
#    if not 'picture' in session:
#        session['picture'] = "../static/img/undraw_profile.svg"
#    if 'tipousuario' not in session or session['tipousuario'] == 0:
#        return redirect('/acessonegado.html') #, 304

    #global Progresso
    #session.clear()
    if __name__ == '__main__':
        info = {'iss': 'https://accounts.google.com', 
                'nbf': 1625489864, 
                'aud': 'your-google-client-id.apps.googleusercontent.com', 
                'sub': 'user-unique-id', 
                'email': 'user@example.com', 
                'email_verified': True, 
                'azp': 'your-google-client-id.apps.googleusercontent.com', 
                'name': 'Generic User', 
                'picture': '', 
                'given_name': 'Generic', 
                'iat': 1625490164, 
                'exp': 1625493764, 
                'jti': '9fd4824823f292e8f6fde204d39cb77b214b4940'}

        session['email'] = info['email']
        session['name'] = info['name']
        session['given_name'] = info['given_name']
        session['picture'] = info['picture']
        session['hoje'] = datetime.now().strftime("%d/%m/%Y")
        session['tipousuario'] = 1 # 1-Usuario 2-Administrador
    if not 'picture' in session:
        session['picture'] = "../static/img/undraw_profile.svg"
    session['tipousuario'] = 0 # 0-Não Logado
    if 'email' in session:
        refUsuario = db.collection(u'Usuarios').document(session['email'])
        Usuario = refUsuario.get()
        if Usuario.exists:
             dictUsuario = Usuario.to_dict()
             if dictUsuario['Tipo'] == 'Usuario':
                 session['tipousuario'] = 1
             elif dictUsuario['Tipo'] == 'Administrador':
                 session['tipousuario'] = 2
             else:
                 session['tipousuario'] = 0
    
    session['Progresso'] = 0

    print("__name__: " + __name__)
    print("tipousuario ", session['tipousuario'])

    return render_template("index.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/novaotimizacao.html')
def novaotimizacao():
    #if session['tipousuario'] == 0:
    #    return redirect('/acessonegado.html') #, 304
    dados = ""

    return render_template("novaotimizacao.html", Dados = dados)

@app.route('/carregardados', methods=['POST'])
def carregardados():
    if session['tipousuario'] == 0:
        email = os.environ.get('GUEST_EMAIL', 'guest@example.com')
        #return redirect('/acessonegado.html') #, 304
    else:
        email = session['email']
    dados = ""
    todascolunas = ""
    # Create a Cloud Storage client.
    gcs = storage.Client()
    # Get the bucket that the file will be uploaded to.
    bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)

    if 'inputFile' in request.files:  
        inputFile = request.files.get('inputFile')
        if inputFile.filename != '':
            if inputFile and allowed_file(inputFile.filename):
                filename = secure_filename(inputFile.filename)
                nome_arquivo = email + '/' + filename

                # Create a new blob and upload the file's content.
                blob = bucket.blob(nome_arquivo)
                
                blob.upload_from_string(
                    inputFile.read(),
                    content_type=inputFile.content_type
                )
                session['filename'] = filename
            else:
                return redirect(request.url)
        elif 'filename' not in session:
            flash('No file part')
            return redirect(request.url)
    elif 'filename' not in session:
        flash('No file part')
        return redirect(request.url)

    filename = session['filename']
    
    firstfilename, fileextension = os.path.splitext(filename)
    print(fileextension)
    if 'separador' in request.form:
        separador = request.form['separador']
        decimal = request.form['decimal']
    else:
        separador = ";"
        decimal = ","
    #if separador == ",":
    #    decimal = "."
    print(separador)
    print(decimal)
    print(firstfilename)
    fileextension = fileextension.lower()
    blob = bucket.get_blob(email + '/' + filename)
    contents = BytesIO(blob.download_as_bytes())
    if fileextension == ".csv":
        raw_data = pd.read_csv(contents, sep=separador, decimal=decimal)
    if fileextension == ".xlsx" or fileextension == ".xls":
        raw_data = pd.read_excel(contents)
    session['fileextension'] = fileextension
    session['separador'] = separador
    session['decimal'] = decimal

    #raw_data = raw_data[raw_data.columns[1:-3]]
    dados = raw_data.values.tolist()
    todascolunas = raw_data.columns.values.tolist()
    colunascoefs = todascolunas.copy() #list(range(len(colunas)))
    print("colunascoefs")
    print(colunascoefs)
    importances = {c: 1 for c in todascolunas}
    #session['dados'] = dados
    session['todascolunas'] = todascolunas
    tipotodascolunas = raw_data.dtypes
    selecionaveiscolunas = [c for c in todascolunas if tipotodascolunas.get(c) in ['int', 'int64', 'float64']]
    selecionadascolunas = [c for c in todascolunas if tipotodascolunas.get(c) in ['int', 'int64', 'float64']]
    session['selecionaveiscolunas'] = selecionaveiscolunas;
    print(selecionaveiscolunas)
    print(session)

    return render_template("novaotimizacao.html", Separador = separador, Decimal = decimal, FileExtension = fileextension, ColunasCoefs = colunascoefs, Result = "", Importances = importances, Technique = "", Method = "", Reference = "", Dados = dados, SelecionadasColunas = selecionadascolunas, SelecionaveisColunas = selecionaveiscolunas, TodasColunas = todascolunas)

@app.route('/criarotimizacao', methods=['POST'])
def criarotimizacao():
    if session['tipousuario'] == 0:
        email = os.environ.get('GUEST_EMAIL', 'guest@example.com')
        #return redirect('/acessonegado.html') #, 304
    else:
        email = session['email']
    dados = ""
    if request.method == "POST":
        if 'filename' in session:
            filename = session['filename']
            processar_colunas = request.form.getlist('selected_coluna[]')
            todascolunas = session['todascolunas']
            referencia = todascolunas[int(request.form['reference'])]
            separador = session['separador']
            decimal = session['decimal']
            colunas = list()
            for c in processar_colunas:
                colunas.append(todascolunas[int(c)])
            d = {'Data': firestore.SERVER_TIMESTAMP, 
                'Arquivo': filename, 
                'Usuario': email, 
                'Status': 'Cadastrada',
                'Referencia': referencia,
                'Separador' : separador,
                'Decimal' : decimal,
                'Colunas' : colunas
                }
            update_time, refDado = db.collection(u'Dados').add(d)
            iddado = refDado.id

            # Trigger the processing automatically after creating the optimization task.
            try:
                # This is the same logic from the 'processardadosfirestore' route
                response = requests.get(
                    app.config['PROCESSAR_DADOS_FUNCTION_URL'],
                    params={'name': iddado},
                    timeout=5
                )
                
                if response.status_code == 200:
                    flash(f'Optimization {iddado} created and processing started successfully.', 'success')
                else:
                    flash(f'Optimization {iddado} created, but failed to start processing. The service returned status {response.status_code}.', 'warning')

            except requests.exceptions.Timeout:
                # This is expected for a "fire-and-forget" call
                flash(f'Optimization {iddado} created and processing started successfully.', 'success')
            except requests.exceptions.RequestException as e:
                flash(f'Optimization {iddado} created, but an error occurred connecting to the processing service: {e}', 'danger')

            return redirect(url_for('listaotimizacoes'))

    return redirect(url_for('novaotimizacao'))

@app.route('/listaotimizacoes.html')
def listaotimizacoes():
    if session['tipousuario'] == 0:
        emailConvidado = os.environ.get('GUEST_EMAIL', 'guest@example.com')
        streamDados = db.collection(u'Dados').where(u'Usuario', u'==', emailConvidado).stream()
        #return redirect('/acessonegado.html') #, 304
    elif session['tipousuario'] == 1:
        streamDados = db.collection(u'Dados').where(u'Usuario', u'==', session['email']).stream()
    elif session['tipousuario'] == 2:
        streamDados = db.collection(u'Dados').stream()
    else:
        return render_template("listaotimizacoes.html", Dados = [])
    Dados = []
    for Dado in streamDados:
        dictDado = Dado.to_dict()
        Data = dictDado['Data'].astimezone(fuso_horario)
        a = {'IdDado': Dado.id,
             'Data': Data.strftime('%d/%m/%Y %H:%M'),
             'DataUniversal': Data.strftime('%Y/%m/%d %H:%M'),
             'Arquivo': dictDado['Arquivo'],
             'Usuario': dictDado['Usuario'],
             'Status': dictDado['Status']
        }
        Dados.append(a) 

    sorted_Dados = sorted(Dados, key=lambda k: k['DataUniversal'], reverse=True) 

    return render_template("listaotimizacoes.html", Dados = sorted_Dados)

@app.route('/viewgraficos.html', methods=['POST'])
def viewgraficos():
    #if 'tipousuario' not in session or session['tipousuario'] == 0:
    #    return redirect('/acessonegado.html') #, 304
    IdDado = request.form['textIdDado']
    print("IdDados ", IdDado)
    refDados = db.collection(u'Dados').document(IdDado)
    Dados = refDados.get()
    if Dados.exists:
        # Create a Cloud Storage client.
        gcs = storage.Client()
        # Get the bucket that the file will be uploaded to.
        bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)
        dictDados = Dados.to_dict()
        Usuario = dictDados['Usuario']
        if 'Resultado' not in dictDados:
            return redirect('/listaotimizacoes.html') #, 304

        filename = dictDados['Resultado']
        nome_arquivo = Usuario + '/' + os.path.basename(filename)
        print(nome_arquivo)

        blob = bucket.get_blob(nome_arquivo)
        if blob is None:
            print("Erro blob")
        
        if blob is None:
            print("Erro blob")
        
        contents = BytesIO(blob.download_as_bytes())
        if contents is None:
            print("Erro contents")

        firstfilename, fileextension = os.path.splitext(filename)
        #fileextension = fileextension.lower()
        if 'Referencia' not in dictDados:
            refDados.update({u'Status': 'Sem referencia'})
        #if 'Separador' in dictDados:
        #    separador = dictDados['Separador']
        #    decimal = dictDados['Decimal']
        #else:
        #    separador = ";"
        #    decimal = ","
        #if fileextension == ".csv":
        #    raw_data = pd.read_csv(contents, sep=separador, decimal=decimal)
        #if fileextension == ".xlsx" or fileextension == ".xls":
        raw_data = pd.read_excel(contents)
        raw_ic = pd.read_excel(contents, sheet_name='Importance Coeficients')
        raw_qci = pd.read_excel(contents, sheet_name='Composite Indicator Quality')
        raw_iq = pd.read_excel(contents, sheet_name='Comparison with other methods')

        dados = raw_data.values.tolist()
        if(not (dados is None or dados == "")):
            todascolunas = raw_data.columns.values.tolist()
            print("todas as colunas ", todascolunas)
            reference = dictDados['Referencia'] # transformar em ordinal
            colunasescolhidas = dictDados['Colunas']

            # streamColunas = db.collection(u'Dados').document(IdDado).collection(u'Colunas').stream()
            # colunasescolhidas = []
            # for sC in streamColunas:
            #     sC_dict = sC.to_dict()
            #     colunasescolhidas.append(sC_dict['Campo'])

            if reference in colunasescolhidas:
                colunasescolhidas.remove(reference)

            print("colunasescolhidas ", colunasescolhidas)

            dadosescolhidos = raw_ic[colunasescolhidas].values.tolist()
            colunascoef = colunasescolhidas.copy()
            coef = ['%.3f'%v for v in dadosescolhidos[-1]]

            #coef = dadosescolhidos[-1]
            #referencedata = raw_data[raw_data.columns[-1]]
            # TODO: Processar os dados
            #raw_data = pd.DataFrame(dadosescolhidos, columns=colunasescolhidas)

            #qci = ["Correlation", "Varience", "Entropy", "Uncertainty"]
            qci = ["Explanatory power", "Informational power", "Discriminating power", "Uncertainty"]
            dadosqci = raw_qci.iloc[:, 1:].values.tolist()
            print(dadosqci)
            dadosqci = [['%.3f'%v for v in d] for d in dadosqci]

            #if(not (dados_qci is None or dados_qci == "")):

            iq = ['Quality-based', 'BoD', 'Entropy', 'PCA', 'Equal Weights']
            dadosiq = raw_iq[iq].values.tolist()
            dadosiq = [['%.3f'%v for v in d] for d in dadosiq]

            indicadores = ['Quality-based', 'BoD', 'Entropy', 'PCA', 'Equal Weights']

            dadosindicadores = raw_data[indicadores].values.tolist()
            dadosindicadores = [['%.3f'%v for v in d] for d in dadosindicadores]

            print(iq)
            print(dadosiq)
            #data = pd.DataFrame({
            #    'mes': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
            #    'valor': [10, 20, 15, 25, 30, 20]
            #})
            #fig = go.Figure([go.Bar(x=data['mes'], y=data['valor'])])
            #fig = go.Figure([go.Histogram(x=dadosindicadores[0])])
            fig = px.histogram(data_frame=raw_data, x=indicadores)

            figDispersao = px.scatter(data_frame=raw_data, x = dictDados['Referencia'], y=indicadores, trendline='ols')

            colunasescolhidas.append(reference)
            colunasescolhidas.append('Quality-based')
            dadosescolhidos = raw_data[colunasescolhidas]

            correlation = dadosescolhidos.corr()
            dadoscorrelation = correlation['Quality-based'] ** 2
            dadoscorrelation = dadoscorrelation.drop(['Quality-based'])
            print(dadoscorrelation)

            #figCorrelation = px.density_heatmap(correlation)
            figCorrelation = px.bar(dadoscorrelation)

            vmedia = dadoscorrelation[1].mean()
            print(vmedia)

            colunasescolhidas.remove(reference)

            medias = [vmedia for c in colunasescolhidas]

            #dadoscorrelation['medias'] = medias

            print(dadoscorrelation)

            linha = px.line(dadoscorrelation, y=medias).update_traces(line_color="red")

            figCorrelation.add_traces(linha.data)

            dfiq = raw_data[iq]

            ddfiq = pd.DataFrame()

            for i in indicadores:
                ddfiq[i] = dfiq[i].rank(method='min', ascending=False)

#            ddfiq = ddfiq.T / 10
            ddfiq = ddfiq / (len(ddfiq) / 10)
            ddfiq = ddfiq.astype(int)
            ddfiq = ddfiq.sort_values(["Quality-based", "BoD", 'Entropy', 'PCA', 'Equal Weights'], ascending=[False, False, False, False, False])
            print(ddfiq)
            
#            figIncertezas = px.line(ddfiq)
            figIncertezas = px.parallel_categories(ddfiq, color="Quality-based", color_continuous_scale=px.colors.sequential.Inferno,
                            dimensions=['Quality-based', 'BoD', 'Entropy', 'PCA', 'Equal Weights'])
    

            #figSemaforo1 = px.colors.diverging.swatches_continuous(px.colors.diverging.RdYlGn)
            #figSemaforo1 = px.choropleth(raw_iq, locations="Quality-based", color_continuous_scale=px.colors.diverging.RdYlGn, color_continuous_midpoint=0.5 )
            
            #figSemaforo1 = px.bar(raw_iq["Quality-based"], color="Quality-based", color_continuous_scale=px.colors.diverging.RdYlGn, color_continuous_midpoint=0.5)
            #figSemaforo1 = px.bar(raw_iq["Quality-based"], color="Quality-based", color_continuous_scale=px.colors.diverging.RdYlGn)
            #figSemaforo1 = px.colors.diverging._swatches(px.colors.diverging.RdYlGn)

            ##ri =     df = pd.DataFrame(dadosiq, columns=iq)
            ##ri["Labels"] = qci
            raw_iq["Labels"] = qci
            print(raw_iq)
            ##print(ri)
            raw_iq_t = raw_iq[["Labels", "Quality-based"]]
            for indice, r in enumerate(raw_iq_t["Quality-based"]):
                if indice == 1: # Informational power
#                    raw_iq_t["Quality-based"][indice] = round((r / .6), 3)
                    if r < .3:
                        raw_iq_t["Quality-based"][indice] = round(((r * .5) / .3), 3)
                    elif r > .3:
                        raw_iq_t["Quality-based"][indice] = round(((r * .7143) + .2857), 3)
                    else:
                        raw_iq_t["Quality-based"][indice] = .5
                elif indice == 3: # Uncertainty
                    if r < .2:
                        raw_iq_t["Quality-based"][indice] = round(1-((r * .5) / .2), 3)
                    elif r > .2:
                        raw_iq_t["Quality-based"][indice] = round(1-((r * .625) + .375), 3)
                    else:
                        raw_iq_t["Quality-based"][indice] = .5
                else: # Others
                    raw_iq_t["Quality-based"][indice] = round(r, 3)

            print(raw_iq_t)
            figSemaforo1 = px.parallel_categories(raw_iq_t, color = "Quality-based", color_continuous_scale=px.colors.diverging.RdYlGn, color_continuous_midpoint=0.5, range_color=[0, 1])

#['lowess', 'rolling', 'ewm', 'expanding', 'ols']

            return render_template("viewgraficos.html", plotSemaforo1 = figSemaforo1.to_html(), plotincertezas = figIncertezas.to_html(), plotcorrecao = figCorrelation.to_html(), plotdispersao=figDispersao.to_html(), plot=fig.to_html(), Iq = iq, DadosIq = dadosiq, Indicadores = indicadores, DadosIndicadores = dadosindicadores, DadosQci = dadosqci, Qci = qci, ColunasCoefs = colunascoef, Coef = coef, iddado = IdDado)

    return redirect('/listaotimizacoes.html') #, 304


@app.route('/resultadosdownload', methods=['POST'])
def resultadosdownload():
    #if 'tipousuario' not in session or session['tipousuario'] == 0:
    #    return redirect('/acessonegado.html') #, 304
    IdDados = request.form['textIdDado']
    print("IdDados ", IdDados)
    refDados = db.collection(u'Dados').document(IdDados)
    Dados = refDados.get()
    if Dados.exists:
        # Create a Cloud Storage client.
        gcs = storage.Client()
        # Get the bucket that the file will be uploaded to.
        bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)
        dictDados = Dados.to_dict()
        Usuario = dictDados['Usuario']
        filename = dictDados['Resultado']
        nome_arquivo = Usuario + '/' + os.path.basename(filename)
        print(nome_arquivo)

        blob = bucket.get_blob(nome_arquivo)
        if blob is None:
            print("Erro blob")
        
        #contents = BytesIO(blob.download_as_bytes())
        #if contents is None:
        #    print("Erro contents")
        
        blob.download_to_filename(os.path.basename(filename))
        

        return send_from_directory('.', os.path.basename(filename), as_attachment=True)
    return redirect('/listaotimizacoes.html') #, 304

@app.route('/processardadosfirestore', methods=['POST'])
def processardadosfirestore():
    #if 'tipousuario' not in session or session['tipousuario'] == 0:
    #    return redirect('/acessonegado.html') # Access Denied
    
    iddado = request.form.get('textIdDado')
    if not iddado:
        flash('Optimization ID not found.', 'danger')
        return redirect(url_for('listaotimizacoes'))

    try:
        # Chama a Cloud Function de forma assíncrona.
        # A chamada é "fire-and-forget", por isso o timeout baixo para não prender o servidor.
        response = requests.get(
            app.config['PROCESSAR_DADOS_FUNCTION_URL'],
            params={'name': iddado},
            timeout=5
        )
        
        if response.status_code == 200:
            flash(f'Processing for optimization {iddado} has started successfully. Please refresh the page in a few moments to see the result.', 'success')
        else:
            flash(f'Failed to start processing. The service returned status {response.status_code}.', 'warning')

    except requests.exceptions.Timeout:
        # O timeout é esperado em uma chamada "fire-and-forget".
        # A requisição foi enviada, mas não esperamos a resposta completa.
        flash(f'Processing for optimization {iddado} has started successfully. Please refresh the page in a few moments to see the result.', 'success')
    except requests.exceptions.RequestException as e:
        # Captura outras exceções de conexão (DNS, falha de conexão, etc.)
        flash(f'Error connecting to the processing service: {e}', 'danger')

    return redirect(url_for('listaotimizacoes'))

@app.route('/get_optimization_status/<iddado>', methods=['GET'])
def get_optimization_status(iddado):
    #if 'tipousuario' not in session or session['tipousuario'] == 0:
    #    return jsonify({'error': 'Access denied'}), 403

    try:
        ref_dado = db.collection(u'Dados').document(iddado).get()
        if ref_dado.exists:
            status = ref_dado.to_dict().get('Status', 'Unknown')
            return jsonify({'status': status})
        else:
            return jsonify({'error': 'Optimization not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/404.html')
def h404():
    return render_template("404.html")

@app.route('/acessonegado.html')
def acessonegado():
    return render_template("acessonegado.html")
    
@app.route('/contact', methods=['POST'])
def contact():
    """Handles the contact form submission."""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        if not all([name, email, phone, message]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('homepage', _anchor='contact'))

        contact_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'message': message,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        db.collection(u'Contatos').add(contact_data)

        flash('Thank you for your message. We will get back to you shortly.', 'success')
    except Exception as e:
        flash(f'An error occurred while sending your message: {e}', 'danger')
        app.logger.error(f"Error saving contact form data: {e}")

    return redirect(url_for('homepage', _anchor='contact'))

@app.route('/blank.html')
def blank():
    return render_template("blank.html")

@app.route('/teste', methods=('GET', 'POST'))
def teste():
    print("Aqui")
    print(__name__)
    #if request.method == 'POST':
    Credential = request.json
    print("Credential", Credential)
    session['email'] = "usu"
    return render_template("resultado.html", dados = Credential)

@app.route('/auth/info/googlejwt', methods=['GET'])
def auth_info_google_jwt():
    """Auth info with Google signed JWT."""
    info = auth_info()
    #dados = json.loads(info.text)
    #dados = json.loads(info)
    #session['username'] = info ['email']
    session['email'] = info['email']
    session['name'] = info['name']
    session['given_name'] = info['given_name']
    session['picture'] = info['picture']

    return jsonify(info)

@app.route('/logoff', methods=('GET', 'POST'))
def logoff():
    session.clear()
    return redirect('/') #, 304

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)

# [START endpoints_auth_info_backend]
def auth_info():
    """Retrieves the authenication information from Google Cloud Endpoints."""
    encoded_info = request.headers.get('X-Endpoint-API-UserInfo', None)
    claims = ""
    info_json = ""
    if encoded_info:
        #claims = _base64_decode(encoded_info)
        info_json = jwt.decode(encoded_info, verify=False) #, certs=public_certs)
        user_info = info_json #json.loads(info_json)
    else:
        user_info = {'email': 'anonymous'}

    return user_info #jsonify(user_info)
# [END endpoints_auth_info_backend]
