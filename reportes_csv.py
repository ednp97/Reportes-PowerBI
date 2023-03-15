import time
import pandas as pd
import schedule 
import cx_Oracle
cx_Oracle.init_oracle_client(lib_dir=r"C:\ReportesPowerBI\oracle") 
import queries 
from datetime import date, timedelta
from datetime import datetime

def connection():
    connection = cx_Oracle.connect(
                user='',
                password='',
                dsn= '',
                encoding = 'UTF-8'
                            )
    return connection

def lista_fechas():
    hoy = date.today()
    fecha_ini = date(2022, 11, 1)
    lista = []
    dias = (hoy - fecha_ini)
    for i in range(dias.days+1):
        lista.append((fecha_ini + timedelta(i)).strftime("%d/%m/%Y"))
    return lista

def shortname_area(nombre):
    if nombre is not None:
        if ('CACE' in nombre):
           ss = 'CACE'+","+str(nombre.index("CACE"))
        elif ('CACR' in nombre):
           ss = 'CACR'+","+str(nombre.index("CACR"))
        elif ('SEDE' in nombre):
           ss = 'SEDE'+","+str(nombre.index("SEDE"))
        else:
            ss = 'NA'

        if ss != 'NA':
            if int(ss.split(",")[1])== 0 :
                sn = nombre[len(ss.split(",")[0])+1:]
                pb = sn.index(' ')
                sn = sn[pb+1:]
            else:
                sn = nombre[0:int(ss.split(",")[1])-1]
            return sn.strip()
        else:
            return nombre
    else:
        pass

def format_date():
    año, mes, dia, hora, minuto = map(str, time.strftime("%Y %m %d %H %M").split())
    f_fecha = "'" + str(dia) + "/" + str(mes)+ "/" + str(año) + " " + str(hora) + ":" + str(minuto) + "'"
    return f_fecha

def write_log(script_name):
    script_name = script_name
    fecha = format_date()
    log = open(r'C:\ReportesPowerBI\files\log.txt','a')
    log.write(f"Se ejecuto {script_name} a las {fecha} \n")
    log.close()

def csv_estancias(): 

    fechas = lista_fechas()
    datos = []
    for fecha in fechas:
        connection = connection()
        cursor = connection.cursor()
        query_nov = f"""
            select 
            substr(ACANOMBRE, instr(ACANOMBRE,'-')-LENGTH(ACANOMBRE)+1) AS SEDE,
            HGRNOMBRE tipo,
            hsunombre piso, 
            '{fecha}' fecha,
            CASE WHEN ADNINGRES IS NULL THEN 'Desocupada' else 'Ocupada' END ESTADO, 
            count(*) as camas
            FROM HPNDEFCAM
            --INNER JOIN HPNESTANC  ON HPNDEFCAM.OID = HPNESTANC.HPNDEFCAM
            inner join hpngrupos on hpngrupos.oid = hpndefcam.hpngrupos
            inner join hpnsubgru on hpnsubgru.oid = hpndefcam.hpnsubgru
            inner join adncenate on adncenate.oid = hpndefcam.adncenate
            left join (
            select HPNDEFCAM CAMAOID, hesfecing FECHAING, nvl(hesfecsal, sysdate) FECHAEGR, ADNINGRES from HPNESTANC) OCUPACION ON CAMAOID = HPNDEFCAM.OID AND (TO_DATE('{fecha} 07:00:00','DD/MM/YYYY hh24:mi:ss') between FECHAING and FECHAEGR)
            group by substr(ACANOMBRE, instr(ACANOMBRE,'-')-LENGTH(ACANOMBRE)+1), HGRNOMBRE, hsunombre, {fecha}, CASE WHEN ADNINGRES IS NULL THEN 'Desocupada' else 'Ocupada' end
            order by 1,2,3,4
            """
        
        cursor.execute(query_nov)
        tit_no_facturados = [row[0] for row in cursor.description]
        for row in cursor:
            datos.append(row)
        connection.close()
    datos.insert(0,tit_no_facturados)
    d =pd.DataFrame(datos) 
    d.to_csv(r'C:\ReportesPowerBI\files\estancias.csv', encoding="utf-8-sig", header=False,index=False, mode="w")
    print("listo")
    write_log("estancias_nov")

def csv_estancias_anexar(): 

    fecha = format_date()

    connection = connection()
    cursor = connection.cursor()
    query_estancias = queries.estancia_sql(fecha)
    cursor.execute(query_estancias)
    datos = []
    for row in cursor:
        datos.append(row)
    connection.close()
    d =pd.DataFrame(datos) 
    d.to_csv(r'C:\ReportesPowerBI\files\estancias.csv', encoding="utf-8-sig", header=False,index=False, mode="a")
    print("listo")
    write_log("estancias")

def csv_seguimiento():
    connection = connection()
    cursor = connection.cursor()
    q_seguimiento = queries.seguimiento_sql()
    cursor.execute(q_seguimiento)
    tit_no_facturados = [row[0] for row in cursor.description]
    datos = []
    for row in cursor:
        datos.append(row)
    datos.insert(0,tit_no_facturados)
    connection.close()
    d =pd.DataFrame(datos) 
    d.to_csv(r'C:\ReportesPowerBI\files\seguimiento_censo.csv', encoding="utf-8-sig", header=False,index=False)
    print("listo")
    write_log("seguimiento")

def csv_ocupacion():
    fechas = lista_fechas()
    datos = []
    for fecha in fechas:
        connection = connection()
        cursor = connection.cursor()
        print (connection)
        q_ocupacion = f"""
        select 
        TO_CHAR'{fecha}'< AS FECHA_CONSULTA,
        substr(ACANOMBRE, <instr(ACANOMBRE,'-')-LENGTH(ACANOMBRE)+1) AS SEDE,
        hsunombre PISO, TOTAL_CAMAS, NVL(TOTAL_OCUPADAS,0) OCUPADAS, 
        TOTAL_CAMAS-NVL(TOTAL_OCUPADAS,0) DISPONIBLE, 
        NVL(SUMADIAS,0) DIAS_CAMA_OCUP,
        TRUNC(100*NVL(TOTAL_OCUPADAS,0)/TOTAL_CAMAS,2) AS PORC_OCUP
        from HPNSUBGRU piso
        inner join (select ADNCENATE, HPNSUBGRU, COUNT(*) TOTAL_CAMAS FROM HPNDEFCAM GROUP BY adncenate, HPNSUBGRU) Camas on Camas.hpnsubgru = piso.oid 
        inner join ADNCENATE sedes on camas.ADNCENATE = sedes.oid
        left join (select HPNSUBGRU, COUNT(HPNDEFCAM.OID) TOTAL_OCUPADAS, SUM(trunc(nvl(HESFECSAL,TO_DATE('{fecha} 23:59:59','DD/MM/YYYY hh24:mi:ss'))-HESFECING)) SUMADIAS
        from hpnestanc INNER JOIN HPNDEFCAM ON HPNDEFCAM.OID = HPNESTANC.HPNDEFCAM
        where (TO_DATE('{fecha} 23:59:59','DD/MM/YYYY hh24:mi:ss') between hesfecing and nvl(HESFECSAL,TO_DATE('{fecha} 23:59:59','DD/MM/YYYY hh24:mi:ss')))
        GROUP BY HPNSUBGRU) OCUPADAS ON OCUPADAS.HPNSUBGRU = PISO.OID
        """
        cursor.execute(q_ocupacion)
        tit_no_facturados = [row[0] for row in cursor.description]
        for row in cursor:
            datos.append(row)
        connection.close()
    datos.insert(0,tit_no_facturados)
    d =pd.DataFrame(datos) 
    d.to_csv(r'C:\ReportesPowerBI\files\ocupacion.csv', encoding="utf-8-sig", header=False,index=False, mode="w")
    print("listo")
    write_log("ocupacion")

    

def csv_ocupacion_anexar():
    connection = connection()
    cursor = connection.cursor()
    q_ocupacion = queries.ocupacion_sql()
    cursor.execute(q_ocupacion)
    datos = []
    for row in cursor:
        datos.append(row)
    connection.close()
    d =pd.DataFrame(datos) 
    d.to_csv(r'C:\ReportesPowerBI\files\ocupacion.csv', encoding="utf-8-sig", header=False,index=False, mode="a")
    print("listo")
    write_log("ocupacion")

def csv_censo_diario():
    connection = connection()
    cursor = connection.cursor()
    q_censo_diario = queries.censo_diario()
    cursor.execute(q_censo_diario)
    tit_no_facturados = [row[0] for row in cursor.description]
    datos = []
    for row in cursor:
        datos.append(row)
    datos.insert(0,tit_no_facturados)
    connection.close()
    d =pd.DataFrame(datos) 
    d.to_csv(r'C:\ReportesPowerBI\files\censo diario.csv', encoding="utf-8-sig", header=False,index=False)
    print("listo")
    write_log("censo diario")

def csv_historico_servicio():
    connection = connection() 
    cursor = connection.cursor()
    q_historicos_servicios = queries.historicos_servicios()
    cursor.execute(q_historicos_servicios)
    tit_no_facturados = [row[0] for row in cursor.description]
    datos = []
    for row in cursor:
        datos.append(row)
    datos.insert(0,tit_no_facturados)
    connection.close()
    d =pd.DataFrame(datos) 
    d.to_csv(r'C:\ReportesPowerBI\files\historico servicios.csv', encoding="utf-8-sig", header=False,index=False)
    print("listo")
    write_log("historicos_servicios")

def csv_ingresosnorm():
    connection = connection() 
    
    q_camas = queries.camas()
    camas = pd.read_sql(q_camas, connection)
    connection.close()
    camas['SERVICIO'] = camas['NOMBRE_CAMA'].apply(shortname_area)
    camas.to_csv(r'C:\ReportesPowerBI\files\ingresosnorm.csv', encoding="utf-8-sig",index=False)
    print("listo")
    write_log("camas")

def csv_radicados():
    connection = connection()
    
    q_radicados = queries.radicados()
    radicados = pd.read_sql(q_radicados, connection)
    connection.close()
    radicados.to_csv(r'C:\ReportesPowerBI\files\radicaciones.csv', encoding="utf-8-sig",index=False)
    print("listo")
    write_log("radicaciones")

def csv_facturas():
    connection = connection() 
    
    q_facturas = queries.facturas()
    facturas = pd.read_sql(q_facturas, connection)
    connection.close()
    facturas.to_csv(r'C:\ReportesPowerBI\files\facturas.csv', encoding="utf-8-sig",index=False)
    print("listo")
    write_log("facturas")

def csv_ventas():
    connection = connection()
    q_ventas = queries.ventas()
    ventas = pd.read_sql(q_ventas, connection)
    connection.close()
    ventas.to_csv(r'C:\ReportesPowerBI\files\ventas.csv', encoding="utf-8-sig",index=False)
    print("listo")
    write_log("ventas")

def csv_recaudos():
    connection = connection() 
    q_recaudos = queries.recaudos()
    recaudos = pd.read_sql(q_recaudos, connection)
    connection.close()
    recaudos.to_csv(r'C:\ReportesPowerBI\files\recaudos.csv', encoding="utf-8-sig",index=False)
    print("listo")
    write_log("recaudos")

def csv_indicadores_urgencias():
    connection = connection()
    cursor = connection.cursor()
    q_indicadores_urgencia = queries.indicadores_urg()
    cursor.execute(q_indicadores_urgencia) 
    tit_no_facturados = [row[0] for row in cursor.description]
    datos = []
    for row in cursor:
        datos.append(row)
    datos.insert(0,tit_no_facturados)
    connection.close()
    d =pd.DataFrame(datos)
    d.to_csv(r'C:\ReportesPowerBI\files\indic_urg.csv', encoding="utf-8-sig", header=False, index=False)
    print("listo")
    write_log("indicadores urgencia")

def csv_consultas():
    fechas = lista_fechas()
    datos = []
    for fecha in fechas:
        connection = connection()
        cursor = connection.cursor()
        q_consultas = f""" 
        SELECT 
        substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1) AS SEDE,
        CMANOMBRE ESPECIALIDAD_NOMBRE,  
        CCMFECASI HORARIO_DE_CITA,
        --CCMFECPAC FECHA_QUE_REQUERIA_EL_PACIENTE/*,CCMFECCAN FECHA_CANCELACIÃ“N, CCMFECCUM FECHA_CUMPLIMIENTO*/, 
        CASE CMNTIPACT.CMATIPCON WHEN 0 THEN 'Ninguna' WHEN 1 THEN 'General' WHEN 2 THEN 'Especializada' END TIPO_CONSULTA,
        CASE CCMESTADO
            WHEN 0 THEN 'ASIGNADA'
            WHEN 1 THEN 'CANCELADA'
            WHEN 2 THEN 'CUMPLIDA'
            WHEN 3 THEN 'INCUMPLIDA'
            WHEN 4 THEN 'FACTURADA'
            WHEN 5 THEN 'INATENCION' 
        END ESTADO,
        COUNT(CCMPACDOC) TOTAL
        FROM CMNCITMED
        INNER JOIN CMNHORMED ON CMNCITMED.CMNHORMED = CMNHORMED.OID
        INNER JOIN GENMEDICO ON CMNCITMED.GENMEDICO1 = GENMEDICO.OID
        INNER JOIN GENDETCON ON CMNCITMED.GENDETCON = GENDETCON.OID
        INNER JOIN CMNTIPACT ON CMNCITMED.CMNTIPACT = CMNTIPACT.OID
        INNER JOIN ADNCENATE ON CMNHORMED.ADNCENATE = ADNCENATE.OID
        WHERE CMNCITMED.CCMFECASI >= TO_DATE('{fecha} 00:00:00','DD/MM/YYYY hh24:mi:ss') AND CMNCITMED.CCMFECASI <= TO_DATE('{fecha} 23:59:59','DD/MM/YYYY hh24:mi:ss')
        GROUP BY 
        substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1), 
        CMANOMBRE,
        CCMFECASI,
        CASE CMNTIPACT.CMATIPCON WHEN 0 THEN 'Ninguna' WHEN 1 THEN 'General' WHEN 2 THEN 'Especializada' END,
        CASE CCMESTADO
            WHEN 0 THEN 'ASIGNADA'
            WHEN 1 THEN 'CANCELADA'
            WHEN 2 THEN 'CUMPLIDA'
            WHEN 3 THEN 'INCUMPLIDA'
            WHEN 4 THEN 'FACTURADA'
            WHEN 5 THEN 'INATENCION' 
        END
        """
        cursor.execute(q_consultas) 
        tit_no_facturados = [row[0] for row in cursor.description]
        for row in cursor:
            datos.append(row)
        connection.close()
    datos.insert(0,tit_no_facturados)
    d =pd.DataFrame(datos)
    d.to_csv(r'C:\ReportesPowerBI\files\consultas.csv', encoding="utf-8-sig", header=False, index=False, mode="a")
    print("listo")
    write_log("consultas")

def csv_consultas_anexar():
    connection = connection()
    cursor = connection.cursor()
    q_consultas = queries.consultas()
    cursor.execute(q_consultas) 
    datos = []
    for row in cursor:
        datos.append(row)
    connection.close()
    d =pd.DataFrame(datos)
    d.to_csv(r'C:\ReportesPowerBI\files\consultas.csv', encoding="utf-8-sig", header=False, index=False, mode="a")
    print("listo")
    write_log("consultas")

csv_estancias() 
csv_ocupacion()
csv_seguimiento()
csv_censo_diario()
csv_indicadores_urgencias()
csv_consultas()
csv_historico_servicio()
csv_ingresosnorm()
csv_radicados()
csv_facturas()
csv_ventas()
csv_recaudos()

schedule.every(1).hours.do(csv_estancias_anexar)
schedule.every().days.at("07:00").do(csv_ocupacion_anexar)
schedule.every().days.at("07:00").do(csv_censo_diario)
schedule.every().days.at("07:00").do(csv_seguimiento)
schedule.every().days.at("07:00").do(csv_historico_servicio) 
schedule.every().days.at("03:00").do(csv_ingresosnorm)
schedule.every().days.at("03:00").do(csv_radicados)
schedule.every().days.at("03:00").do(csv_facturas)
schedule.every().days.at("03:00").do(csv_ventas)
schedule.every().days.at("03:00").do(csv_recaudos)
schedule.every().days.at("03:00").do(csv_indicadores_urgencias)
schedule.every().days.at("03:00").do(csv_consultas_anexar)
print("se ejecuto")
while True:
    schedule.run_pending()
    time.sleep(1)