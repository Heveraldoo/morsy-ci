from flask import Flask, request, jsonify
import os
import pandas as pd

from google.cloud import firestore
from google.cloud import storage

from datetime import date, datetime, timezone, timedelta

from io import BytesIO

from ropt.normalization import Maximize, Minimize, RatioMaximize, RatioMinimize, LogisticMaximize, LogisticMinimize
from ropt.normalization import SafeRatioMaximize, SafeRatioMinimize
from ropt.normalization import LogisticMaximize, LogisticMinimize

from ropt.normalizer import importance_factors, robust_normalize, normalize, ranking_normalize, outlier_removal

from ropt.util import BOD_Calculation, Entropy_Calculation, PCA_Calculation
from ropt.multi_objective import multi_objective_optimization
from ropt.methods import equal_weights, specialist_weights
from ropt.objectives import MaxCorrel, PCA, MaxEntropy, MinUncertanty
from ropt.means import normal_weighted_arithimetic_mean

from multiprocessing import Process, Manager

db = firestore.Client()

CLOUD_STORAGE_BUCKET = os.environ.get('CLOUD_STORAGE_BUCKET', 'seu-bucket-padrao')

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def hello_http():
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'name' in request_json:
        name = request_json['name']
    elif request_args and 'name' in request_args:
        name = request_args['name']
    else:
        return jsonify({'error': 'Nenhum ID de otimização fornecido'}), 400
    
    IdDados = name
    print(IdDados)

    refDados = db.collection(u'Dados').document(IdDados)
    Dados = refDados.get()
    if Dados.exists:
        refDados.update({u'Status': 'Em Processamento'})

        gcs = storage.Client()
        if gcs is None:
            print("Erro gcs")
        bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)
        if bucket is None:
            print("Erro bucket")

        dictDados = Dados.to_dict()
        Usuario = dictDados['Usuario']
        filename = dictDados['Arquivo']
        nome_arquivo = Usuario + '/' + os.path.basename(filename)
        print(nome_arquivo)

        blob = bucket.get_blob(nome_arquivo)
        if blob is None:
            print("Erro blob")
        
        contents = BytesIO(blob.download_as_bytes())
        if contents is None:
            print("Erro contents")

        firstfilename, fileextension = os.path.splitext(filename)
        fileextension = fileextension.lower()
        if 'Referencia' not in dictDados:
            refDados.update({u'Status': 'Sem referencia'})
        if 'Separador' in dictDados:
            separador = dictDados['Separador']
            decimal = dictDados['Decimal']
        else:
            separador = ";"
            decimal = ","
        if fileextension == ".csv":
            raw_data = pd.read_csv(contents, sep=separador, decimal=decimal)
        if fileextension == ".xlsx" or fileextension == ".xls":
            raw_data = pd.read_excel(contents)


        dados = raw_data.values.tolist()
        if(not (dados is None or dados == "")):
            todascolunas = raw_data.columns.values.tolist()
            reference = dictDados['Referencia'] # transformar em ordinal

            method = 'Robust'
            technique = 'Min Max'
            factors = [1 for c in todascolunas]

            colunasescolhidas = dictDados['Colunas']

            # streamColunas = db.collection(u'Dados').document(IdDados).collection(u'Colunas').stream()
            # colunasescolhidas = []
            # for sC in streamColunas:
            #     sC_dict = sC.to_dict()
            #     colunasescolhidas.append(sC_dict['Campo'])

            if reference in colunasescolhidas:
                colunasescolhidas.remove(reference)
            
            colunasescolhidas.append(reference)
            print("colunasescolhidas ", colunasescolhidas)

            dadosescolhidos = raw_data[colunasescolhidas].values.tolist()

            print("Normalizing data")
            raw_data = pd.DataFrame(dadosescolhidos, columns=colunasescolhidas)
            MethodsFunctions = {'Robust': robust_normalize, 'Normal': normalize, 'Ranking': ranking_normalize}
            NormalFunctions = {'Min Max': (Maximize, Minimize), 'Ratio': (RatioMaximize, RatioMinimize), 'Logistic': (LogisticMaximize, LogisticMinimize)}
            raw_data = MethodsFunctions[method](outlier_removal(raw_data), 
                                max_function=NormalFunctions[technique][0],
                                min_function=NormalFunctions[technique][1])

            print("Calculating indicators")

            indata = raw_data[raw_data.columns[:-1]]
            referencedata = raw_data[raw_data.columns[-1]]

            indicator1 = Manager().list()
            indicator2 = Manager().list()
            indicator3 = Manager().list()
            indicator4 = Manager().list()

            p1 = Process(target=CalcularBOD, args=(indata, indicator1))
            p2 = Process(target=CalcularEntropy, args=(indata, indicator2))  
            p3 = Process(target=CalcularPCA, args=(indata, indicator3))
            p4 = Process(target=Calcularequal_weights, args=(indata, indicator4))

            p1.start()
            p2.start()
            p3.start()
            p4.start()

            p1.join()
            p2.join()
            p3.join()
            p4.join()

            uncertanty_indicators = [
                        pd.Series([r.ci for r in indicator1]),
                        pd.Series([r.ci for r in indicator2]),
                        pd.Series([r.ci for r in indicator3]),
                        pd.Series([r for r in indicator4])
                    ]

            objectfunctions = [
                    MaxCorrel(referencedata),
                    PCA(indata),
                    MaxEntropy(),
                    MinUncertanty(uncertanty_indicators)
                ]

            print("Optimizing Data")

            o_max = []
            o_min=[]
            coef = multi_objective_optimization(indata,
                objectfunctions,
                thresholds=[1 for _ in indata.columns],
                out_max=o_max, out_min=o_min, importance_factors = factors
            )

            coeff = ['%15.3f'%v for v in coef]

            ci = indata.apply(lambda x: normal_weighted_arithimetic_mean(coef, x), axis=1)
            cif = ['%15.3f'%v for v in ci]

            qualities = [quality(ci) for quality in objectfunctions]
            #qualities = [quality(ci, indata) for quality in objectfunctions]

            valoresobjetivos = list()
            for mi, val, ma in zip(o_min,qualities,o_max):
                print(['%15.3f'%v for v in (mi, val, ma, (val-mi)/(ma-mi))])
                v = ['%15.3f'%v for v in (mi, val, ma, (val-mi)/(ma-mi))]
                valoresobjetivos.append(v);

            print("Saving results")

            file_name = firstfilename + '__res'

            public_url = send_to_excel(raw_data, ci, coef, referencedata, uncertanty_indicators, o_min, o_max, Usuario, file_name)

            data_e_hora_atuais = datetime.now()

            refDados.update({u'Status': 'Processado', 
                             u'Resultado': public_url,
                             u'HoraResultado': data_e_hora_atuais})

    return 'Hello {}!'.format(filename)

def CalcularBOD(indata, indicator):
    for v in BOD_Calculation(indata).run():
        indicator.append(v)

def CalcularEntropy(indata, indicator):
    for v in Entropy_Calculation(indata).run():
        indicator.append(v)

def CalcularPCA(indata, indicator):
    for v in PCA_Calculation(indata).run():
        indicator.append(v)

def Calcularequal_weights(indata, indicator):
    for v in equal_weights(indata).values.tolist():
        indicator.append(v)

def send_to_excel(raw_data, ci, coef, reference, uncertanty_indicators, o_min, o_max, usuario, file_name='export_dados'):

    gcs = storage.Client()
    bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)
    file_name = file_name +'.xlsx'
    nome_arquivo = usuario + "/" + file_name
    #nome_arquivo = file_name
    # Create a new blob and upload the file's content.
    blob = bucket.blob(nome_arquivo)

    data = raw_data[raw_data.columns[:-1]]

    raw_data['Quality-based'] = ci
    raw_data['BoD'] = uncertanty_indicators[0]
    raw_data['Entropy'] = uncertanty_indicators[1]
    raw_data['PCA'] = uncertanty_indicators[2]
    raw_data['Equal Weights'] = uncertanty_indicators[3]
    indic = coef + [0,0,0,0,0,0]
    #raw_data.loc[-1] = indic
    raw_data.to_excel(file_name, sheet_name='Data')
    
    df = pd.DataFrame(columns=data.columns.tolist())
    df.loc[-1] = coef
    #df.index = ["Explanatory power", "Informational power", "Discriminating power", "Uncertainty"]
    with pd.ExcelWriter(file_name, engine="openpyxl", mode="a") as writer:
        df.to_excel(writer,sheet_name='Importance Coeficients') # Máximo de 30 caracteres

    ci = data.apply(lambda col: normal_weighted_arithimetic_mean(coef, col), axis=1)
    qualities = [
        MaxCorrel(reference)(ci),
        PCA(data)(ci),
        MaxEntropy()(ci),
        MinUncertanty(uncertanty_indicators)(ci)
        #MaxCorrel(reference)(ci, data),
        #PCA()(ci, data),
        #MaxEntropy()(ci, data),
        #MinUncertanty(uncertanty_indicators)(ci, data)
    ]
    #df = pd.DataFrame(zip(o_min,qualities,o_max), columns=['Worst', 'Found', 'Better'])
    Matriz = [[abs(v) for v in (mi, val, ma, (val-mi)/(ma-mi))] for mi, val, ma in zip(o_min,qualities,o_max)]
    df = pd.DataFrame(Matriz, columns=['Worst', 'Found', 'Better', '%'])
    #df.index = ['Correlation', 'Variance', 'Entropy', 'Uncertanty']
    df.index = ["Explanatory power", "Informational power", "Discriminating power", "Uncertainty"]
    with pd.ExcelWriter(file_name, engine="openpyxl", mode="a") as writer:
        df.to_excel(writer,sheet_name='Composite Indicator Quality') # Máximo de 30 caracteres
    print("para o excel")
    for mi, val, ma in zip(o_min,qualities,o_max):
        print([abs(v) for v in (mi, val, ma, (val-mi)/(ma-mi))])

    qualities = [qualities] + [[
         MaxCorrel(reference)(uncertanty_indicators[i]),
         PCA(data)(uncertanty_indicators[i]),
         MaxEntropy()(uncertanty_indicators[i]),
         MinUncertanty(uncertanty_indicators)(uncertanty_indicators[i])
    ] for i in range(len(uncertanty_indicators))]

    Matriz = [[abs(v) for v in d] for d in qualities]
    #df = pd.DataFrame(Matriz, columns=['Correlation', 'Variance', 'Entropy', 'Uncertanty'])
    df = pd.DataFrame(Matriz, columns=["Explanatory power", "Informational power", "Discriminating power", "Uncertainty"])
    df.index = ['Quality-based', 'BoD', 'Entropy', 'PCA', 'Equal Weights']
    df = df.transpose()
    with pd.ExcelWriter(file_name, engine="openpyxl", mode="a") as writer:
        df.to_excel(writer,sheet_name='Comparison with other methods')
    
    blob.upload_from_filename(file_name)

    return blob.public_url

if __name__ == "__main__":
    app.run(host='127.0.0.2', port=5300, debug=False)