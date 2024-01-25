from django.shortcuts import render,redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate,logout
import requests  # Corrige la importación de requests
from django.contrib.auth.decorators import login_required
from datetime import datetime,timedelta
import math


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
        'error': "Error de contraseña"
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

    # Payloads para las solicitudes a la API ## RAPTOR ## CAMARA IMPLEMENTACION 1 ##
    payloadA_R = {"pageNo": 1,"pageSize": 2, "cameraIndexCodes": "5", "statisticsType": 1, "startTime": start_time_00, "endTime": end_time}
    payloadB_R = {"pageNo": 1, "pageSize": 2, "cameraIndexCodes": "4", "statisticsType": 1, "startTime": start_time_00, "endTime": end_time}
    payloadHE_R = {"pageNo": 1, "pageSize": 2, "cameraIndexCodes": "4", "statisticsType": 4, "startTime": end_time2, "endTime": end_time}


    # Payloads para las solicitudes a la API ## BLACKHOLE ## CAMARA IMPLEMENTACION 2 ##
    payloadA_B = {"pageNo": 1,"pageSize": 2, "cameraIndexCodes": "6", "statisticsType": 1, "startTime": start_time_00, "endTime": end_time}
    payloadB_B = {"pageNo": 1, "pageSize": 2, "cameraIndexCodes": "2", "statisticsType": 1, "startTime": start_time_00, "endTime": end_time}
    payloadHE_B = {"pageNo": 1, "pageSize": 2, "cameraIndexCodes": "2", "statisticsType": 4, "startTime": end_time2, "endTime": end_time}



    # Encabezados de autenticación
    headers = {"APPkey": "29134892", "APPsecret": "sOC9IlGdXYdrcFEFdT1A", "X-Ca-Key": "29134892"}

    # Realizar las solicitudes a la API ###############RAPTOR###################
    responseA_R = requests.post(api_url, json=payloadA_R, headers=headers, verify=False)
    responseB_R = requests.post(api_url, json=payloadB_R, headers=headers, verify=False)
    responseHE_R = requests.post(api_url, json=payloadHE_R, headers=headers, verify=False)


        
    responseA_B = requests.post(api_url, json=payloadA_B, headers=headers, verify=False)
    responseB_B = requests.post(api_url, json=payloadB_B, headers=headers, verify=False)
    responseHE_B = requests.post(api_url, json=payloadHE_B, headers=headers, verify=False)


    if responseA_R.status_code == 200 and responseB_R.status_code == 200 and responseHE_R.status_code == 200 and \
            responseA_B.status_code == 200 and responseB_B.status_code == 200 and responseHE_B.status_code == 200:
        # Obtener los datos de la respuesta JSON# RAPTOR
        dataA_R = obtener_datos(responseA_R)
        dataB_R = obtener_datos(responseB_R)
        dataHE_R = obtener_datos(responseHE_R)
         # Obtener los datos de la respuesta JSON# BlackHole
        dataA_B = obtener_datos(responseA_B)
        dataB_B = obtener_datos(responseB_B)
        dataHE_B = obtener_datos(responseHE_B)

        # Obtener los datos de la respuesta JSON# RAPTOR
        # dataA_B = 
    

        # Calcular la diferencia entre enterNum y exitNum para cada entrada
        dataA_R = calcular_diferencia(dataA_R, "enterNum", "exitNum")
        dataB_R = calcular_diferencia(dataB_R, "exitNum", "enterNum")
        dataHE_R = calcular_diferencia(dataHE_R, "exitNum", "enterNum")

        dataA_B = calcular_diferencia(dataA_B, "enterNum", "exitNum")
        dataB_B = calcular_diferencia(dataB_B, "exitNum", "enterNum")
        dataHE_B = calcular_diferencia(dataHE_B, "exitNum", "enterNum")



        # Suma acumulativa de media_por_hora_HE
        total_media_por_hora_HE = sum(entry["media_por_hora"] for entry in dataHE_R["data"]["list"])
        total_media_por_hora_HE_B = sum(entry["media_por_hora"] for entry in dataHE_B["data"]["list"])

        # Calcular el totalExH como la suma acumulativa
        totalExH = total_media_por_hora_HE
        totalExH_B = total_media_por_hora_HE_B

        dataR = calcular_data_c(dataA_R, dataB_R, dataHE_R, totalExH)
        dataB = calcular_data_c(dataA_B, dataB_B, dataHE_B, totalExH_B)


        # DATOS UTILIZADOS: Pasa los datos al template
        return render(request, 'dashboard.html', {'dataR': dataR, 'dataB': dataB})
    else:
        # Manejar el error estableciendo valores predeterminados a 0
        dataR = [{"media_por_hora_C": 0, "media_por_hora_A": 0, "media_por_hora_B": 0, "totalExH": 0}]
        dataB = [{"media_por_hora_C": 0, "media_por_hora_A": 0, "media_por_hora_B": 0, "totalExH": 0}]
        return render(request, 'dashboard.html', {'dataR': dataR, 'dataB': dataB})

def obtener_datos(response):
    data = response.json() if "data" in response.json() and "list" in response.json()["data"] else {"data": {"list": []}}
    for entry in data["data"]["list"]:
        entry["media_por_hora"] = entry.get("enterNum", 0) - entry.get("exitNum", 0)
        
    return data

def calcular_diferencia(data, enter_key, exit_key):
    if "data" in data and "list" in data["data"]:
        for entry in data["data"]["list"]:
            entry["media_por_hora"] = entry.get(enter_key, 0) - entry.get(exit_key, 0)
    else:
        # Establecer valores predeterminados si no hay datos
        data = {"data": {"list": []}}
    
    return data




def calcular_data_c(dataA_R, dataB_R, dataHE_R, totalExH):
    dataR = []
    fecha_actual = datetime.now()
    for entryA, entryB, entryHE in zip(dataA_R["data"]["list"], dataB_R["data"]["list"], dataHE_R["data"]["list"]):
        media_por_hora_A = entryA["enterNum"]
        media_por_hora_B = entryB["exitNum"] - entryB["enterNum"]
        media_por_hora_C = max(media_por_hora_A - media_por_hora_B,0)

        # Verificar si totalExH es diferente de cero antes de realizar la división
        if totalExH != 0:
            media_espera = math.ceil((media_por_hora_C / totalExH) * 60)
        else:
            # En este caso, podrías establecer media_espera en un valor predeterminado o manejarlo de alguna otra manera
            media_espera = 0  # O cualquier otro valor que tenga sentido en tu contexto

        dataR.append({
            "media_por_hora_C": media_por_hora_C,
            "media_espera": media_espera,
            "media_por_hora_B": media_por_hora_B,
            "hora_actual": fecha_actual,
            "totalExH": totalExH,
        })
    return dataR