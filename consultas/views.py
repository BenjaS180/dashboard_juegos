from django.shortcuts import render,redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate,logout
import requests  # Corrige la importación de requests
from django.contrib.auth.decorators import login_required
from datetime import datetime,timedelta
import math,json
import pyodbc


def signin(request):
    if request.user.is_authenticated:
        # El usuario ya está autenticado, redirige al dashboard
        return redirect('/dashboard')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard')
        else:
            error = 'Username or password is incorrect'
    else:
        error = None

    return render(request, 'signin.html', {
        'form': AuthenticationForm,
    })
        


@login_required
def signout(request):
    logout(request)
    return redirect('signin')



def consultas():
    pass




@login_required
def dashboard(request):
    # Obtener la fecha y hora actual
    fecha_actual = datetime.now()
    fecha_actual_menos_una_hora = fecha_actual - timedelta(hours=1)

    # Crear las fechas de inicio y fin dinámicamente como strings
    end_time = fecha_actual.strftime("%Y-%m-%dT%H:%M:%S%z") + "+08:00"
    start_time_00 = fecha_actual.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S%z") + "+08:00"
    end_time2 = fecha_actual_menos_una_hora.strftime("%Y-%m-%dT%H:%M:%S%z") + "+08:00"

    # URL de la API
    api_url = "https://172.16.2.40/artemis/api/aiapplication/v1/people/statisticsTotalNumByTime"

    # Payloads para las solicitudes a la API ## RAPTOR ## CAMARA IMPLEMENTACION 1   ||| 60 = produccion ||| 61 = demanda ||| ##
    payloadA_RAPTOR = {"pageNo": 1,"pageSize": 2, "cameraIndexCodes": "61", "statisticsType": 1, "startTime": start_time_00, "endTime": end_time}
    payloadB_RAPTOR = {"pageNo": 1, "pageSize": 2, "cameraIndexCodes": "60", "statisticsType": 1, "startTime": start_time_00, "endTime": end_time}
    payloadHE_RAPTOR = {"pageNo": 1, "pageSize": 2, "cameraIndexCodes": "60", "statisticsType": 4, "startTime": end_time2, "endTime": end_time}

    # Payloads para las solicitudes a la API ## BLACKHOLE ## CAMARA IMPLEMENTACION 2 ||| 69 = produccion ||| 63 = demanda |||##
    payloadA_BLACKHOLE = {"pageNo": 1,"pageSize": 2, "cameraIndexCodes": "63", "statisticsType": 1, "startTime": start_time_00, "endTime": end_time}
    payloadB_BLACKHOLE = {"pageNo": 1, "pageSize": 2, "cameraIndexCodes": "69", "statisticsType": 1, "startTime": start_time_00, "endTime": end_time}
    payloadHE_BLACKHOLE = {"pageNo": 1, "pageSize": 2, "cameraIndexCodes": "69", "statisticsType": 4, "startTime": end_time2, "endTime": end_time}

    # Encabezados de autenticación
    headers = {"APPkey": "29134892", "APPsecret": "sOC9IlGdXYdrcFEFdT1A", "X-Ca-Key": "29134892"}

    # Realizar las solicitudes a la API ###############RAPTOR###################
    responseA_RAPTOR = requests.post(api_url, json=payloadA_RAPTOR, headers=headers, verify=False)
    responseB_RAPTOR = requests.post(api_url, json=payloadB_RAPTOR, headers=headers, verify=False)
    responseHE_RAPTOR = requests.post(api_url, json=payloadHE_RAPTOR, headers=headers, verify=False)

    responseA_BLACKHOLE = requests.post(api_url, json=payloadA_BLACKHOLE, headers=headers, verify=False)
    responseB_BLACKHOLE = requests.post(api_url, json=payloadB_BLACKHOLE, headers=headers, verify=False)
    responseHE_BLACKHOLE = requests.post(api_url, json=payloadHE_BLACKHOLE, headers=headers, verify=False)

    if responseA_RAPTOR.status_code == 200 and responseB_RAPTOR.status_code == 200 and responseHE_RAPTOR.status_code == 200 and \
            responseA_BLACKHOLE.status_code == 200 and responseB_BLACKHOLE.status_code == 200 and responseHE_BLACKHOLE.status_code == 200:
        # Obtener los datos de la respuesta JSON# RAPTOR
        dataA_R = obtener_datos(responseA_RAPTOR)
        dataB_R = obtener_datos(responseB_RAPTOR)
        dataHE_R = obtener_datos(responseHE_RAPTOR)
         # Obtener los datos de la respuesta JSON# BlackHole
        dataA_B = obtener_datos(responseA_BLACKHOLE)
        dataB_B = obtener_datos(responseB_BLACKHOLE)
        dataHE_B = obtener_datos(responseHE_BLACKHOLE)

        # Calcular la diferencia entre enterNum y exitNum para cada entrada
        dataA_R = calcular_diferencia(dataA_R, "enterNum", "exitNum")
        dataB_R = calcular_diferencia(dataB_R, "exitNum", "enterNum")
        dataHE_R = calcular_diferencia(dataHE_R, "exitNum", "enterNum")

        dataA_B = calcular_diferencia(dataA_B, "enterNum", "exitNum")
        dataB_B = calcular_diferencia(dataB_B, "exitNum", "enterNum")
        dataHE_B = calcular_diferencia(dataHE_B, "exitNum", "enterNum")

        # Verificar disponibilidad de las cámaras
        availability_api_url = "https://172.16.2.40/artemis/api/resource/v1/cameras/indexCode"
        camera_index_codes = ["61", "60", "63", "69"]

        camera_availability = []
        for code in camera_index_codes:
            payload = {"cameraIndexCode": code}
            response = requests.post(availability_api_url, json=payload, headers=headers, verify=False)
            if response.status_code == 200:
                data = response.json()
                camera_availability.append({
                    "cameraIndexCode": code,
                    "status": data["data"]["status"]
                })
            else:
                camera_availability.append({
                    "cameraIndexCode": code,
                    "status": 2  # Assuming 2 means not available in case of error
                })

        # Suma acumulativa de media_por_hora_HE
        total_media_por_hora_HE = sum(entry["media_por_hora"] for entry in dataHE_R["data"]["list"])
        total_media_por_hora_HE_B = sum(entry["media_por_hora"] for entry in dataHE_B["data"]["list"])

        # Calcular el totalExH como la suma acumulativa
        totalExH = total_media_por_hora_HE
        totalExH_B = total_media_por_hora_HE_B

        dataR = calcular_data_c(dataA_R, dataB_R, dataHE_R, totalExH)
        dataB = calcular_data_c(dataA_B, dataB_B, dataHE_B, totalExH_B)

        # Añadir información de producción y demanda
        for entry in dataR:
            entry["produccion"] = "✔️" if any(cam["cameraIndexCode"] == "60" and cam["status"] == 1 for cam in camera_availability) else "❌"
            entry["demanda"] = "✔️" if any(cam["cameraIndexCode"] == "61" and cam["status"] == 1 for cam in camera_availability) else "❌"

        for entry in dataB:
            entry["produccion"] = "✔️" if any(cam["cameraIndexCode"] == "63" and cam["status"] == 1 for cam in camera_availability) else "❌"
            entry["demanda"] = "✔️" if any(cam["cameraIndexCode"] == "69" and cam["status"] == 1 for cam in camera_availability) else "❌"

        # DATOS UTILIZADOS: Pasa los datos al template
        return render(request, 'dashboard.html', {'dataR': dataR, 'dataB': dataB, 'camera_availability': camera_availability})
    else:
        # Manejar el error estableciendo valores predeterminados a 0
        camera_availability = []
        camera_availability = camera_availability.append({"cameraIndexCode": code,"status": 2  })
        dataR = [{"media_por_hora_C": 0, "media_por_hora_A": 0, "media_por_hora_B": 0, "totalExH": 0}]
        dataB = [{"media_por_hora_C": 0, "media_por_hora_A": 0, "media_por_hora_B": 0, "totalExH": 0}]
        return render(request, 'dashboard.html', {'dataR': dataR, 'dataB': dataB,'camera_availability': camera_availability })


def obtener_datos(response):
    try:
        data = response.json()
        if "data" in data and "list" in data["data"]:
            for entry in data["data"]["list"]:
                entry["media_por_hora"] = entry.get("enterNum", 0) - entry.get("exitNum", 0)
        else:
            data = {"data": {"list": []}}
    except json.JSONDecodeError:
        data = {"data": {"list": []}}
    return data


def calcular_diferencia(data, enter_key, exit_key):
    if "data" in data and "list" in data["data"]:
        for entry in data["data"]["list"]:
            entry["media_por_hora"] = entry.get(enter_key, 0) - entry.get(exit_key, 0)
    else:
        # Establecer valores predeterminados si no hay datos
        data = {"data": {"list": []}}
    
    return data




def obtener_cantidad_gente():
    # Establecer la conexión con la base de datos
    server = '172.20.8.252\\SQLEXPRESS'
    database = 'informatica'
    username = 'sa'
    password = 'Superman8'
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password)

    # Ejecutar la consulta SQL para obtener la cantidad de gente en el parque
    cursor = conn.cursor()
    cursor.execute("SELECT PeopleCount FROM Pregoner_Status")
    row = cursor.fetchone()
    cantidad_gente = row[0] if row else 0

    # Cerrar la conexión
    conn.close()

    return cantidad_gente

def estado_parque():
    server = '172.20.8.252\\SQLEXPRESS'
    database = 'informatica'
    username = 'sa'
    password = 'Superman8'
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password)

    cursor = conn.cursor()
    cursor.execute("SELECT Park_Open FROM Pregoner_Status")
    row = cursor.fetchone()
    park_open = row[0] if row else 0

    conn.close()
    
    return park_open

def calcular_data_c(dataA_R, dataB_R, dataHE_R, totalExH):
    dataR = []
    fecha_actual = datetime.now()
    optimo_raptor = 550
    optimo_blackhole = 250
    cantidad_gente = obtener_cantidad_gente()
    cantidad_gente_formateada = '{:,}'.format(cantidad_gente)
    park_open = estado_parque()

    if park_open == 1:
        park_open = "✔️"
    else:
        park_open = "❌"

    # Verificar si totalExH es igual a cero
    if totalExH == 0:
        # Establecer todos los datos en cero y mostrar el mensaje de parque cerrado
        dataR.append({
            "media_por_hora_C": 0,
            "media_espera": 0,
            "media_por_hora_B": 0,
            "hora_actual": fecha_actual,
            "totalExH": 0,
            "optimo_raptor": optimo_raptor,
            "optimo_blackhole": optimo_blackhole,
            "diferencia_raptor": 0,
            "diferencia_blackhole": 0,
            "cantidadgente": 0,
            "dispoparque": park_open
        })
    else:
        # Procesar datos normalmente
        for entryA, entryB, entryHE in zip(dataA_R["data"]["list"], dataB_R["data"]["list"], dataHE_R["data"]["list"]):
            media_por_hora_A = entryA["enterNum"] - entryA["exitNum"]
            media_por_hora_B = entryB["exitNum"] - entryB["enterNum"]
            media_por_hora_C = media_por_hora_A - media_por_hora_B

            # Calcular media_espera
            media_espera = math.ceil((media_por_hora_C / totalExH) * 60)

            # Calcular las diferencias entre totalExH y los valores óptimos
            diferencia_raptor = totalExH - optimo_raptor
            diferencia_blackhole = totalExH - optimo_blackhole

            dataR.append({
                "media_por_hora_C": media_por_hora_C,
                "media_espera": media_espera,
                "media_por_hora_B": media_por_hora_B,
                "hora_actual": fecha_actual,
                "totalExH": totalExH,
                "optimo_raptor": optimo_raptor,
                "optimo_blackhole": optimo_blackhole,
                "diferencia_raptor": diferencia_raptor,
                "diferencia_blackhole": diferencia_blackhole,
                "cantidadgente": cantidad_gente_formateada,
                "dispoparque": park_open
            })

    return dataR
