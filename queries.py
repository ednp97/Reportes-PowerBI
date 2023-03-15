from datetime import datetime
from datetime import timedelta

today = datetime.today()
ayer = today + timedelta(days=-1)
ayerstr = "'" + str(ayer.year) + "-" + str(ayer.month) + "-" + str(ayer.day) + " 23:59:59'"

def yesterday():
    today = datetime.today()
    ayer = today + timedelta(days=-1)
    hoystr_in = "'" + str(today.year) + "-" + str(today.month) + "-" + str(today.day) + " 00:00:00'"
    hoystr_fin = "'" + str(today.year) + "-" + str(today.month) + "-" + str(today.day) + " 23:59:59'"
    ayerstr_in = "'" + str(ayer.year) + "-" + str(ayer.month) + "-" + str(ayer.day) + " 00:00:00'"
    ayerstr_fin = "'" + str(ayer.year) + "-" + str(ayer.month) + "-" + str(ayer.day) + " 23:59:59'" #genera la fecha a consultar
    fechas = [ayerstr_fin,ayerstr_in,hoystr_in,hoystr_fin]
    return fechas

def ocupacion_sql():
    ayerstr = yesterday()
    ocupacion = (f"""select 
    TO_CHAR({ayerstr[0]}) AS FECHA_CONSULTA,
    substr(ACANOMBRE, instr(ACANOMBRE,'-')-LENGTH(ACANOMBRE)+1) AS SEDE,
    hsunombre PISO, TOTAL_CAMAS, NVL(TOTAL_OCUPADAS,0) OCUPADAS, 
    TOTAL_CAMAS-NVL(TOTAL_OCUPADAS,0) DISPONIBLE, 
    NVL(SUMADIAS,0) DIAS_CAMA_OCUP,
    TRUNC(100*NVL(TOTAL_OCUPADAS,0)/TOTAL_CAMAS,2) AS PORC_OCUP
    from HPNSUBGRU piso
    inner join (select ADNCENATE, HPNSUBGRU, COUNT(*) TOTAL_CAMAS FROM HPNDEFCAM GROUP BY adncenate, HPNSUBGRU) Camas on Camas.hpnsubgru = piso.oid 
    inner join ADNCENATE sedes on camas.ADNCENATE = sedes.oid
    left join (select HPNSUBGRU, COUNT(HPNDEFCAM.OID) TOTAL_OCUPADAS, SUM(trunc(nvl(HESFECSAL,TO_DATE({ayerstr[0]},'YYYY-MM-DD HH24:MI:SS'))-HESFECING)) SUMADIAS
    from hpnestanc INNER JOIN HPNDEFCAM ON HPNDEFCAM.OID = HPNESTANC.HPNDEFCAM
    where (TO_DATE({ayerstr[0]},'YYYY-MM-DD HH24:MI:SS') between hesfecing and nvl(HESFECSAL,TO_DATE({ayerstr[0]},'YYYY-MM-DD HH24:MI:SS')))
    GROUP BY HPNSUBGRU) OCUPADAS ON OCUPADAS.HPNSUBGRU = PISO.OID
    """)
    return ocupacion

def estancia_sql(fecha):
    fecha = yesterday()
    sqlstr = (f"""select 
    {fecha[0]} AS FECHA,
    substr(ACANOMBRE, instr(ACANOMBRE,'-')-LENGTH(ACANOMBRE)+1) AS SEDE,
    HGRNOMBRE tipo,
    hsunombre as PISO,
    CASE HCAESTADO 
        WHEN 0 THEN 'Ninguno'
        WHEN 1 THEN 'Desocupada'
        WHEN 2 THEN 'Ocupada'
        WHEN 3 THEN 'Bloqueada'
        WHEN 4 THEN 'Desbloqueada'
        WHEN 5 THEN 'Mantenimiento'
        WHEN 6 THEN 'Inactiva'
    END as estado,
    count(*) as camas 
from HPNDEFCAM,ADNCENATE,HPNGRUPOS,HPNSUBGRU
    where HPNDEFCAM.ADNCENATE  = adncenate.oid and HPNDEFCAM.HPNGRUPOS = hpngrupos.oid and hpndefcam.hpnsubgru = hpnsubgru.oid
    group by acanombre,adncenate,hcaestado,HGRNOMBRE,hsunombre
    order by 2,3,4
    """)
    return sqlstr

def seguimiento_sql(): # INGRESOS Y EGRESOS PISO POR DIA
    seguimiento =(f"""SELECT 
    AINCONSEC NUMINGRESO, 
    ADNINGRESO.OID,
    GPANOMCOM PACIENTE,
    CASE WHEN GCFNOMBRE IS NULL THEN 'MEDICAMENTOS' ELSE TO_CHAR(GCFNOMBRE) END GRUPO_FAC,
    substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1) AS SEDE,
    HSUNOMBRE PISO,
    HISTORICO.ESTANCIA, 
    SIPCODCUP CUP,  
    SERDESSER SERVICIO, 
    TO_CHAR(AINFECING,'DD/MM/YYYY') FECHA_INGRESO,
    TO_CHAR(SERFECSER,'DD/MM/YYYY') FECHA_SERVICIO,
    TO_CHAR(ADEFECSAL,'DD/MM/YYYY') FECHA_EGRESO, 
    ROUND((SERFECSER-AINFECING),0) AS INGR_VS_SERV, 
    ROUND((ADEFECSAL-SERFECSER),0) AS EGRESO_VS_SERV,
    ROUND((NVL(hesfecsal, SYSDATE)-AINFECING),0) AS ESTANCIA_APROX, 
    SERVALPRO VALORPRO,
    SERAPLPRO APL_PROC,
    ROUND(CASE SERAPLPRO WHEN 0 THEN CASE SLNSERPRO.SERVALPRO WHEN 0 THEN ISMVALPRO ELSE SERVALPRO END ELSE 0 END)*SERCANTID VALORSERV
    FROM SLNSERPRO
    left join SLNPROHOJ on SLNSERPRO.OID=SLNPROHOJ.OID
    left join INNCSUMPA on SLNPROHOJ.INNCSUMPA1=INNCSUMPA.OID
    left join INNMSUMPA on SLNPROHOJ.OID=INNMSUMPA.SLNPROHOJ
    LEFT JOIN SLNSERHOJ ON SLNSERHOJ.OID = SLNSERPRO.OID
    LEFT JOIN GENSERIPS ON SLNSERHOJ.GENSERIPS1 = GENSERIPS.OID
    LEFT JOIN GENCONFAC ON GENCONFAC.OID = GENSERIPS.GENCONFAC1
    INNER JOIN ADNINGRESO ON ADNINGRESO.OID = SLNSERPRO.ADNINGRES1
    inner join GENPACIEN ON GENPACIEN.OID = ADNINGRESO.GENPACIEN
    LEFT JOIN ADNEGRESO ON ADNINGRESO.OID = ADNEGRESO.ADNINGRESO
    LEFT JOIN SLNFACTUR ON ADNINGRESO.OID = SLNFACTUR.ADNINGRESO
    inner JOIN HPNDEFCAM ON HPNDEFCAM.ADNINGRESO = ADNINGRESO.OID --> con INNER JOIN: Pacientes acostados | con LEFT JOIN: Todos los pacientes
    inner JOIN HPNSUBGRU ON HPNDEFCAM.HPNSUBGRU = HPNSUBGRU.OID --> con INNER JOIN: Pacientes acostados | con LEFT JOIN: Todos los pacientes
    inner JOIN ADNCENATE ON HPNDEFCAM.ADNCENATE = ADNCENATE.OID --> con INNER JOIN: Pacientes acostados | con LEFT JOIN: Todos los pacientes
    inner join (select adningres, hsunombre ESTANCIA, hcacodigo, hesfecing, hesfecsal
                from hpnestanc 
                inner join hpndefcam on hpndefcam.oid = hpnestanc.hpndefcam 
                inner join hpnsubgru on hpnsubgru.oid = hpndefcam.hpnsubgru 
                order by hesfecing) HISTORICO ON HISTORICO.ADNINGRES = ADNINGRESO.OID --> Se pueden repetir registros si hay pacientes ocupando dos camas
    WHERE 
    --AINFECING > TO_DATE('31/12/2021 23:59:59','DD/MM/YYYY HH24:MI:SS') AND  -->Para filtrar por fecha de ingreso
    --ACACODIGO LIKE :SEDE  -->Para filtrar por sede
    --AND HSUNOMBRE LIKE '%'||:SERVICIO||'%' -->Para filtrar por Servicio
    --AND ESTANCIA IS NULL
    /*and */serfecser >=hesfecing and serfecser <(NVL(hesfecsal, SYSDATE))  -->para discriminar los servicios por la cama donde estuvo hospitalizado
    order by 4,5,9,1,2""")
    return seguimiento

def hospitalizacion_sql():
    hospitalizacion = (f"""SELECT 
    substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1) SEDE,
    HSUNOMBRE PISO,
    EXTRACT(YEAR FROM TO_DATE(HESFECING, 'dd/mm/yyy')) VIGENCIA,
    EXTRACT(MONTH FROM TO_DATE(HESFECING, 'dd/mm/yyy')) MES,
    EXTRACT(DAY FROM TO_DATE(HESFECING, 'dd/mm/yyy')) DIA,
    MAX('HOSPITALIZACION') CLASIFICACION,
    MAX('INGRESO A PISO') AS INDICADOR,
    COUNT(ADNINGRESO) VALORIND
    FROM HPNESTANC 
    INNER JOIN HPNDEFCAM ON HPNDEFCAM.OID = HPNESTANC.HPNDEFCAM
    INNER JOIN ADNCENATE ON ADNCENATE.OID = HPNDEFCAM.ADNCENATE
    inner JOIN HPNSUBGRU ON HPNDEFCAM.HPNSUBGRU = HPNSUBGRU.OID
    --WHERE TO_DATE(HESFECING ,'DD/MM/YYYY') = :FECHA_CONSULTA
    group by substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1),
    HSUNOMBRE,
    EXTRACT(YEAR FROM TO_DATE(HESFECING, 'dd/mm/yyy')),
    EXTRACT(MONTH FROM TO_DATE(HESFECING, 'dd/mm/yyy')),
    EXTRACT(DAY FROM TO_DATE(HESFECING, 'dd/mm/yyy'))
    
    UNION
    
    SELECT 
    substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1) SEDE,
    HSUNOMBRE PISO,
    EXTRACT(YEAR FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')) VIGENCIA,
    EXTRACT(MONTH FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')) MES,
    EXTRACT(DAY FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')) DIA,
    MAX('HOSPITALIZACION') CLASIFICACION,
    MAX('EGRESO DE PISO') AS INDICADOR,
    COUNT(*) VALORIND
    FROM HPNESTANC 
    INNER JOIN HPNDEFCAM ON HPNDEFCAM.OID = HPNESTANC.HPNDEFCAM
    INNER JOIN ADNCENATE ON ADNCENATE.OID = HPNDEFCAM.ADNCENATE
    inner JOIN HPNSUBGRU ON HPNDEFCAM.HPNSUBGRU = HPNSUBGRU.OID
    group by substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1),
    HSUNOMBRE,
    EXTRACT(YEAR FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')),
    EXTRACT(MONTH FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')),
    EXTRACT(DAY FROM TO_DATE(HESFECSAL, 'dd/mm/yyy'))
    """)
    return hospitalizacion

def indicadores_sql(fecha):
    ayerstr = fecha
    sql = (f"""SELECT 
    substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1) SEDE,
    HSUNOMBRE PISO,
    EXTRACT(YEAR FROM TO_DATE(HESFECING, 'dd/mm/yyy')) VIGENCIA,
    EXTRACT(MONTH FROM TO_DATE(HESFECING, 'dd/mm/yyy')) MES,
    EXTRACT(DAY FROM TO_DATE(HESFECING, 'dd/mm/yyy')) DIA,
    TO_CHAR(HESFECING, 'DD/MM/YYYY') AS FECHA_IND,
    MAX('HOSPITALIZACION') CLASIFICACION,
    MAX('INGRESO A PISO') AS INDICADOR,
    COUNT(ADNINGRESO) VALORIND
FROM HPNESTANC 
    INNER JOIN HPNDEFCAM ON HPNDEFCAM.OID = HPNESTANC.HPNDEFCAM
    INNER JOIN ADNCENATE ON ADNCENATE.OID = HPNDEFCAM.ADNCENATE
    inner JOIN HPNSUBGRU ON HPNDEFCAM.HPNSUBGRU = HPNSUBGRU.OID
    --WHERE TO_DATE(HESFECING ,'DD/MM/YYYY') = :FECHA_CONSULTA
group by substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1),
    HSUNOMBRE,
    EXTRACT(YEAR FROM TO_DATE(HESFECING, 'dd/mm/yyy')),
    EXTRACT(MONTH FROM TO_DATE(HESFECING, 'dd/mm/yyy')),
    EXTRACT(DAY FROM TO_DATE(HESFECING, 'dd/mm/yyy'))
UNION ALL
SELECT 
    substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1) SEDE,
    HSUNOMBRE PISO,
    EXTRACT(YEAR FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')) VIGENCIA,
    EXTRACT(MONTH FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')) MES,
    EXTRACT(DAY FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')) DIA,
    MAX('HOSPITALIZACION') CLASIFICACION,
    MAX('EGRESO DE PISO') AS INDICADOR,
    COUNT(*) VALORIND
FROM HPNESTANC 
    INNER JOIN HPNDEFCAM ON HPNDEFCAM.OID = HPNESTANC.HPNDEFCAM
    INNER JOIN ADNCENATE ON ADNCENATE.OID = HPNDEFCAM.ADNCENATE
    inner JOIN HPNSUBGRU ON HPNDEFCAM.HPNSUBGRU = HPNSUBGRU.OID
    --WHERE TO_DATE(HESFECING ,'DD/MM/YYYY') = :{ayerstr}
group by substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1),
    HSUNOMBRE,
    EXTRACT(YEAR FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')),
    EXTRACT(MONTH FROM TO_DATE(HESFECSAL, 'dd/mm/yyy')),
    EXTRACT(DAY FROM TO_DATE(HESFECSAL, 'dd/mm/yyy'))
    """)
    return sql

def servnofacSql (fecha_in, fecha_fin):
    ayer = fecha_in
    sql = (f""""
SELECT      
    '' Tipo_Documento,
    SLNORDSER.SOSORDSER Numero_Orden,
    to_char(SLNORDSER.SOSFECORD,'DD/MM/YYYY') Fecha_Orden,
    ADNINGRESO.AINCONSEC Numero_Ingreso,
    to_char(ADNINGRESO.AINFECING,'DD/MM/YYYY') Fecha_Ingreso,
    to_char(ADNEGRESO.ADEFECSAL,'DD/MM/YYYY') Fecha_Egreso,
    GENDETCON.GDECODIGO Codigo_Plan,
    GENDETCON.GDENOMBRE Nombre_Plan,
    ADNCENATE.ACACODIGO Codigo_CentroA,
    ADNCENATE.ACANOMBRE Nombre_CentroA,
    GEENENTADM.ENTCODIGO Codigo_Entidad,
    GEENENTADM.ENTNOMBRE Nombre_Entidad,
    CASE 
        WHEN GENPACIEN.PACTIPDOC=0 THEN 'Ninguno'
        WHEN GENPACIEN.PACTIPDOC=1 THEN 'Cédula de ciudadanía'
        WHEN GENPACIEN.PACTIPDOC=2 THEN 'Cédula de extranjería'
        WHEN GENPACIEN.PACTIPDOC=3 THEN 'Tarjeta de identidad'
        WHEN GENPACIEN.PACTIPDOC=4 THEN 'Registro civil'
        WHEN GENPACIEN.PACTIPDOC=5 THEN 'Pasaporte'
        WHEN GENPACIEN.PACTIPDOC=6 THEN 'Adulto sin identificación'
        WHEN GENPACIEN.PACTIPDOC=7 THEN 'Menor sin identificación'
        WHEN GENPACIEN.PACTIPDOC=8 THEN 'Número único de identificación'
        WHEN GENPACIEN.PACTIPDOC=9 THEN 'Salvoconducto'
        WHEN GENPACIEN.PACTIPDOC=10 THEN 'Certificado nacido vivo'
        WHEN GENPACIEN.PACTIPDOC=11 THEN 'Carné Diplomático'
        WHEN GENPACIEN.PACTIPDOC=12 THEN 'Permiso Especial de Permanencia'
        WHEN GENPACIEN.PACTIPDOC=14 THEN 'Permiso por protección temporal'
        WHEN GENPACIEN.PACTIPDOC=15 THEN 'Documento de identificación extranjero'
    END Tipo_Documento_Paciente,
    GENPACIEN.PACNUMDOC Numero_de_identificacion,
    GENPACIEN.GPANOMCOM Paciente,
    to_char(GENPACIEN.GPAFECNAC,'DD/MM/YYYY') PacienteFechaNac,
    CASE
        WHEN GENDETCON.GDETIPPLA= 0  THEN 'Ninguno'
        WHEN GENDETCON.GDETIPPLA= 1  THEN 'Subsidiado'
        WHEN GENDETCON.GDETIPPLA= 2  THEN 'Vinculado'
        WHEN GENDETCON.GDETIPPLA= 3  THEN 'Contributivo'
        WHEN GENDETCON.GDETIPPLA= 4  THEN 'Particular'
        WHEN GENDETCON.GDETIPPLA= 5  THEN 'AccidenteTransito'
        WHEN GENDETCON.GDETIPPLA= 6  THEN 'Otros'
        WHEN GENDETCON.GDETIPPLA= 7  THEN 'IPSPrivada'
        WHEN GENDETCON.GDETIPPLA= 8  THEN 'EmpresaRegimenEspecial'
        WHEN GENDETCON.GDETIPPLA= 9  THEN 'FOSYGATraumaMayor'
        WHEN GENDETCON.GDETIPPLA= 10 THEN 'EventosCatastroficos'
        WHEN GENDETCON.GDETIPPLA= 11 THEN 'CompañiasAseguradoras'
        WHEN GENDETCON.GDETIPPLA= 12 THEN 'Desplazados'
        WHEN GENDETCON.GDETIPPLA= 13 THEN 'ConvenioUCI'
    END TipoPlan,
    CASE 
        WHEN ADNINGRESO.AINTIPING=0 THEN 'Ninguno' 
        WHEN ADNINGRESO.AINTIPING=1 THEN 'Ambulatorio'
        WHEN ADNINGRESO.AINTIPING=2 THEN 'Hospitalario'
    end as TIPO_INGRESO,
    INNPRODUC.IPRCODIGO Servicio_Codigo,
    SLNSERPRO.SERDESSER Servicio_Nombre,
    SLNSERPRO.SERCANTID Cantidad, 
    SLNSERPRO.SERFECSER FechaServicio,
    INNGRUPO.IGRCODIGO GrupoSerCodigo,
    INNGRUPO.IGRNOMBRE GrupoSerNombre,
    INNSUBGRU.ISGCODIGO SubgrupoCodigo,
    INNSUBGRU.ISGNOMBRE SubgrupoNombre,
    GENMEDICO.GMECODIGO MedicoCodigo,
    GENMEDICO.GMENOMCOM MedicoNombre,
    GENARESER.GASCODIGO AreaCodigo,
    GENARESER.GASNOMBRE AreaNombre,
    CTNCENCOS.CCCODIGO CentroCodigo,
    CTNCENCOS.CCNOMBRE CentroNombre,
    '' GrupoQuiCodigo,
    '' GrupoQuiNombre,
    SLNSERPRO.SERCANTID Cantidad, 
    SLNSERPRO.SERVALPAC ValPac,
    SLNSERPRO.SERVALENT ValEnt,
    CASE WHEN SLNSERPRO.SERVALPRO=0 THEN (INNMSUMPA.ISMVALPRO*SLNSERPRO.SERCANTID) ELSE (SLNSERPRO.SERVALPRO*SLNSERPRO.SERCANTID) END TotSer,
    '' Grupoquirurgico
FROM SLNSERPRO
    left join SLNPROHOJ on SLNSERPRO.OID=SLNPROHOJ.OID
    inner join INNCSUMPA on SLNPROHOJ.INNCSUMPA1=INNCSUMPA.OID
    inner join INNMSUMPA on SLNPROHOJ.OID=INNMSUMPA.SLNPROHOJ
    inner join ADNINGRESO on SLNSERPRO.ADNINGRES1=ADNINGRESO.OID
    inner join GENPACIEN on  ADNINGRESO.GENPACIEN = GENPACIEN.oid
    left join ADNEGRESO on ADNINGRESO.OID = ADNEGRESO. ADNINGRESO
    inner join GENDETCON on ADNINGRESO.GENDETCON = GENDETCON.OID
    inner join ADNCENATE on ADNINGRESO.ADNCENATE=ADNCENATE.OID
    inner join GENCONTRA on GENDETCON.GENCONTRA1=GENCONTRA.OID
    inner join GEENENTADM on GENCONTRA.DGNENTADM1=GEENENTADM.OID
    inner join INNPRODUC on SLNPROHOJ.INNPRODUC1=INNPRODUC.OID
    inner join INNGRUPO on INNPRODUC.IGRCODIGO = INNGRUPO.OID
    inner join INNSUBGRU on INNPRODUC.ISGCODIGO = INNSUBGRU.OID
    inner join GENMEDICO on SLNSERPRO.GENMEDICO1=GENMEDICO.OID
    inner join SLNORDSER on SLNSERPRO.SLNORDSER1=SLNORDSER.OID AND SLNORDSER.SOSESTADO <>2
    inner join GENARESER on SLNORDSER.GENARESER1=GENARESER.OID
    inner join CTNCENCOS on GENARESER.CTNCENCOS1=CTNCENCOS.OID
WHERE 
    (ADNINGRESO.AINFECING >=TO_DATE('31/10/2022 00:00:00','DD/MM/YYYY hh24:mi:ss') AND ADNINGRESO.AINFECING <=TO_DATE('01/12/2022 23:59:59','DD/MM/YYYY hh24:mi:ss'))
    and ADNINGRESO.AINESTADO IN (0,3)
    and SLNSERPRO.SERAPLPRO=0
   AND ADNCENATE.ACACODIGO >= '01' AND ADNCENATE.ACACODIGO <= '05' -->SEDES

UNION ALL

SELECT  
    '' Tipo_Documento,
    SLNORDSER.SOSORDSER Numero_Orden,
    to_char(SLNORDSER.SOSFECORD,'DD/MM/YYYY') Fecha_Orden,
    ADNINGRESO.AINCONSEC Numero_Ingreso,
    to_char(ADNINGRESO.AINFECING,'DD/MM/YYYY') Fecha_Ingreso,
    to_char(ADNEGRESO.ADEFECSAL,'DD/MM/YYYY') Fecha_Egreso,
    GENDETCON.GDECODIGO Codigo_Plan,
    GENDETCON.GDENOMBRE Nombre_Plan,
    ADNCENATE.ACACODIGO Codigo_CentroA,
    ADNCENATE.ACANOMBRE Nombre_CentroA,
    GEENENTADM.ENTCODIGO Codigo_Entidad,
    GEENENTADM.ENTNOMBRE Nombre_Entidad,
    CASE 
        WHEN GENPACIEN.PACTIPDOC=0 THEN 'Ninguno'
        WHEN GENPACIEN.PACTIPDOC=1 THEN 'Cédula de ciudadanía'
        WHEN GENPACIEN.PACTIPDOC=2 THEN 'Cédula de extranjería'
        WHEN GENPACIEN.PACTIPDOC=3 THEN 'Tarjeta de identidad'
        WHEN GENPACIEN.PACTIPDOC=4 THEN 'Registro civil'
        WHEN GENPACIEN.PACTIPDOC=5 THEN 'Pasaporte'
        WHEN GENPACIEN.PACTIPDOC=6 THEN 'Adulto sin identificación'
        WHEN GENPACIEN.PACTIPDOC=7 THEN 'Menor sin identificación'
        WHEN GENPACIEN.PACTIPDOC=8 THEN 'Número único de identificación'
        WHEN GENPACIEN.PACTIPDOC=9 THEN 'Salvoconducto'
        WHEN GENPACIEN.PACTIPDOC=10 THEN 'Certificado nacido vivo'
        WHEN GENPACIEN.PACTIPDOC=11 THEN 'Carné Diplomático'
        WHEN GENPACIEN.PACTIPDOC=12 THEN 'Permiso Especial de Permanencia'
        WHEN GENPACIEN.PACTIPDOC=14 THEN 'Permiso por protección temporal'
        WHEN GENPACIEN.PACTIPDOC=15 THEN 'Documento de identificación extranjero'
    END Tipo_Documento_Paciente,
    GENPACIEN.PACNUMDOC Numero_de_identificacion,
    GENPACIEN.GPANOMCOM Paciente,
    to_char(GENPACIEN.GPAFECNAC,'DD/MM/YYYY') PacienteFechaNac,
    CASE
        WHEN GENDETCON.GDETIPPLA= 0  THEN 'Ninguno'
        WHEN GENDETCON.GDETIPPLA= 1  THEN 'Subsidiado'
        WHEN GENDETCON.GDETIPPLA= 2  THEN 'Vinculado'
        WHEN GENDETCON.GDETIPPLA= 3  THEN 'Contributivo'
        WHEN GENDETCON.GDETIPPLA= 4  THEN 'Particular'
        WHEN GENDETCON.GDETIPPLA= 5  THEN 'AccidenteTransito'
        WHEN GENDETCON.GDETIPPLA= 6  THEN 'Otros'
        WHEN GENDETCON.GDETIPPLA= 7  THEN 'IPSPrivada'
        WHEN GENDETCON.GDETIPPLA= 8  THEN 'EmpresaRegimenEspecial'
        WHEN GENDETCON.GDETIPPLA= 9  THEN 'FOSYGATraumaMayor'
        WHEN GENDETCON.GDETIPPLA= 10 THEN 'EventosCatastroficos'
        WHEN GENDETCON.GDETIPPLA= 11 THEN 'CompañiasAseguradoras'
        WHEN GENDETCON.GDETIPPLA= 12 THEN 'Desplazados'
        WHEN GENDETCON.GDETIPPLA= 13 THEN 'ConvenioUCI'
    END TipoPlan,
    CASE 
        WHEN ADNINGRESO.AINTIPING=0 THEN 'Ninguno' 
        WHEN ADNINGRESO.AINTIPING=1 THEN 'Ambulatorio'
        WHEN ADNINGRESO.AINTIPING=2 THEN 'Hospitalario'
    end as TIPO_INGRESO,
    GENSERIPS.SIPCODIGO Servicio_Codigo,
    SLNSERPRO.SERDESSER Servicio_Nombre,
    SLNSERPRO.SERCANTID Cantidad, 
    SLNSERPRO.SERFECSER FechaServicio,
    GENGRUPOS.GGRCODIGO GrupoSerCodigo,
    GENGRUPOS.GGRNOMBRE GrupoSerNombre,
    GENSUBGRU.GSUCODIGO SubgrupoCodigo,
    GENSUBGRU.GSUNOMBRE SubgrupoNombre,
    GENMEDICO.GMECODIGO MedicoCodigo,
    GENMEDICO.GMENOMCOM MedicoNombre,
    GENARESER.GASCODIGO AreaCodigo,
    GENARESER.GASNOMBRE AreaNombre,
    CTNCENCOS.CCCODIGO CentroCodigo,
    CTNCENCOS.CCNOMBRE CentroNombre,
    To_Char(GENGRUQUI.SGQCODIGO) GrupoQuiCodigo,
    To_Char(GENGRUQUI.SGQNOMBRE) GrupoQuiNombre,
    SLNSERPRO.SERCANTID Cantidad, 
    SLNSERPRO.SERVALPAC ValPac,
    SLNSERPRO.SERVALENT ValEnt,
    CASE WHEN GENGRUQUI1 IS NULL THEN ((round(GENMANTAR.SMTVALSER*SLNSERPRO.SERCANTID/100))*100)ELSE ((round(SLNSERPRO.SERVALPRO*SLNSERPRO.SERCANTID/100))*100) END TotSer,
    To_Char(genmanser.GENGRUQUI1) Grupoquirurgico
FROM SLNSERPRO
    inner join SLNSERHOJ on SLNSERPRO.OID=SLNSERHOJ.OID
    inner join ADNINGRESO on SLNSERPRO.ADNINGRES1=ADNINGRESO.OID
    inner join GENPACIEN on  ADNINGRESO.GENPACIEN = GENPACIEN.oid
    left  join ADNEGRESO on ADNINGRESO.OID = ADNEGRESO. ADNINGRESO
    inner join GENDETCON on ADNINGRESO.GENDETCON = GENDETCON.OID
    inner join ADNCENATE on ADNINGRESO.ADNCENATE=ADNCENATE.OID
    inner join GENCONTRA on GENDETCON.GENCONTRA1=GENCONTRA.OID
    inner join GEENENTADM on GENCONTRA.DGNENTADM1=GEENENTADM.OID
    inner join GENSERIPS on SLNSERHOJ.GENSERIPS1 = GENSERIPS.OID
    inner join GENGRUPOS on GENSERIPS.GENGRUPOS1=GENGRUPOS.OID
    inner join GENSUBGRU on GENSERIPS.GENSUBGRU1=GENSUBGRU.OID
    inner join GENMANSER on  SLNSERHOJ.GENMANSER1=GENMANSER.OID
    inner join GENMANTAR on GENMANSER.OID=GENMANTAR.GENMANSER1 AND  GENMANTAR.OID = (SELECT MAX(OID) FROM GENMANTAR WHERE GENMANSER.OID=GENMANTAR.GENMANSER1)
    inner join GENMEDICO on SLNSERPRO.GENMEDICO1=GENMEDICO.OID
    inner join SLNORDSER on SLNSERPRO.SLNORDSER1=SLNORDSER.OID AND SLNORDSER.SOSESTADO <>2
    inner join GENARESER on SLNORDSER.GENARESER1=GENARESER.OID
    inner join CTNCENCOS on GENARESER.CTNCENCOS1=CTNCENCOS.OID
    left join GENGRUQUI on GENMANSER.GENGRUQUI1=GENGRUQUI.OID
WHERE 
    (ADNINGRESO.AINFECING >=TO_DATE('31/10/2022 00:00:00','DD/MM/YYYY hh24:mi:ss') AND ADNINGRESO.AINFECING <=TO_DATE('01/12/2022 23:59:59','DD/MM/YYYY hh24:mi:ss'))
    AND ADNCENATE.ACACODIGO >= '01'  AND ADNCENATE.ACACODIGO <= '05' --> TODAS LAS SEDES
    and ADNINGRESO.AINESTADO IN (0,3)
    and SLNSERPRO.SERAPLPRO=0;
    """)
    print(sql)
    return sql

def consultaedgar(fecha_in, fecha_fin):
    sede_in ='01'
    sede_fin = '05'
    sql =(
           """ SELECT 
            '' Tipo_Documento,
            SLNORDSER.SOSORDSER Numero_Orden,
            to_char(SLNORDSER.SOSFECORD,'DD/MM/YYYY') Fecha_Orden,
            ADNINGRESO.AINCONSEC Numero_Ingreso,
            to_char(ADNINGRESO.AINFECING,'DD/MM/YYYY') Fecha_Ingreso,
            to_char(ADNEGRESO.ADEFECSAL,'DD/MM/YYYY') Fecha_Egreso,
            GENDETCON.GDECODIGO Codigo_Plan,
            GENDETCON.GDENOMBRE Nombre_Plan,
            ADNCENATE.ACACODIGO Codigo_CentroA,
            ADNCENATE.ACANOMBRE Nombre_CentroA,
            GEENENTADM.ENTCODIGO Codigo_Entidad,
            GEENENTADM.ENTNOMBRE Nombre_Entidad,
            CASE 
            WHEN GENPACIEN.PACTIPDOC=0 THEN 'Ninguno'
            WHEN GENPACIEN.PACTIPDOC=1 THEN 'Cédula de ciudadanía'
            WHEN GENPACIEN.PACTIPDOC=2 THEN 'Cédula de extranjería'
            WHEN GENPACIEN.PACTIPDOC=3 THEN 'Tarjeta de identidad'
            WHEN GENPACIEN.PACTIPDOC=4 THEN 'Registro civil'
            WHEN GENPACIEN.PACTIPDOC=5 THEN 'Pasaporte'
            WHEN GENPACIEN.PACTIPDOC=6 THEN 'Adulto sin identificación'
            WHEN GENPACIEN.PACTIPDOC=7 THEN 'Menor sin identificación'
            WHEN GENPACIEN.PACTIPDOC=8 THEN 'Número único de identificación'
            WHEN GENPACIEN.PACTIPDOC=9 THEN 'Salvoconducto'
            WHEN GENPACIEN.PACTIPDOC=10 THEN 'Certificado nacido vivo'
            WHEN GENPACIEN.PACTIPDOC=11 THEN 'Carné Diplomático'
            WHEN GENPACIEN.PACTIPDOC=12 THEN 'Permiso Especial de Permanencia'
            WHEN GENPACIEN.PACTIPDOC=14 THEN 'Permiso por protección temporal'
            WHEN GENPACIEN.PACTIPDOC=15 THEN 'Documento de identificación extranjero'
            END Tipo_Documento_Paciente,
            GENPACIEN.PACNUMDOC Numero_de_identificacion,
            GENPACIEN.GPANOMCOM Paciente,
            to_char(GENPACIEN.GPAFECNAC,'DD/MM/YYYY')PacienteFechaNac,
            CASE
            WHEN GENDETCON.GDETIPPLA= 0  THEN 'Ninguno'
            WHEN GENDETCON.GDETIPPLA= 1  THEN 'Subsidiado'
            WHEN GENDETCON.GDETIPPLA= 2  THEN 'Vinculado'
            WHEN GENDETCON.GDETIPPLA= 3  THEN 'Contributivo'
            WHEN GENDETCON.GDETIPPLA= 4  THEN 'Particular'
            WHEN GENDETCON.GDETIPPLA= 5  THEN 'AccidenteTransito'
            WHEN GENDETCON.GDETIPPLA= 6  THEN 'Otros'
            WHEN GENDETCON.GDETIPPLA= 7  THEN 'IPSPrivada'
            WHEN GENDETCON.GDETIPPLA= 8  THEN 'EmpresaRegimenEspecial'
            WHEN GENDETCON.GDETIPPLA= 9  THEN 'FOSYGATraumaMayor'
            WHEN GENDETCON.GDETIPPLA= 10 THEN 'EventosCatastroficos'
            WHEN GENDETCON.GDETIPPLA= 11 THEN 'CompañiasAseguradoras'
            WHEN GENDETCON.GDETIPPLA= 12 THEN 'Desplazados'
            WHEN GENDETCON.GDETIPPLA= 13 THEN 'ConvenioUCI'
            END TipoPlan,
            CASE 
            WHEN ADNINGRESO.AINTIPING=0 THEN 'Ninguno' 
            WHEN ADNINGRESO.AINTIPING=1 THEN 'Ambulatorio'
            WHEN ADNINGRESO.AINTIPING=2 THEN 'Hospitalario'
            end as TIPO_INGRESO,
            INNPRODUC.IPRCODIGO Servicio_Codigo,
            SLNSERPRO.SERDESSER Servicio_Nombre,
            SLNSERPRO.SERCANTID Cantidad, 
            SLNSERPRO.SERFECSER FechaServicio,
            INNGRUPO.IGRCODIGO GrupoSerCodigo,
            INNGRUPO.IGRNOMBRE GrupoSerNombre,
            INNSUBGRU.ISGCODIGO SubgrupoCodigo,
            INNSUBGRU.ISGNOMBRE SubgrupoNombre,
            GENMEDICO.GMECODIGO MedicoCodigo,
            GENMEDICO.GMENOMCOM MedicoNombre,
            GENARESER.GASCODIGO AreaCodigo,
            GENARESER.GASNOMBRE AreaNombre,
            CTNCENCOS.CCCODIGO CentroCodigo,
            CTNCENCOS.CCNOMBRE CentroNombre,
            '' GrupoQuiCodigo,
            '' GrupoQuiNombre,
            SLNSERPRO.SERCANTID Cantidad, 
            SLNSERPRO.SERVALPAC ValPac,
            SLNSERPRO.SERVALENT ValEnt,
            CASE WHEN SLNSERPRO.SERVALPRO=0 THEN (INNMSUMPA.ISMVALPRO*SLNSERPRO.SERCANTID) ELSE (SLNSERPRO.SERVALPRO*SLNSERPRO.SERCANTID) END TotSer,
            '' Grupoquirurgico
            FROM SLNSERPRO
            left join SLNPROHOJ on SLNSERPRO.OID=SLNPROHOJ.OID
            inner join INNCSUMPA on SLNPROHOJ.INNCSUMPA1=INNCSUMPA.OID
            inner join INNMSUMPA on SLNPROHOJ.OID=INNMSUMPA.SLNPROHOJ
            inner join ADNINGRESO on SLNSERPRO.ADNINGRES1=ADNINGRESO.OID
            inner join GENPACIEN on  ADNINGRESO.GENPACIEN = GENPACIEN.oid
            left join ADNEGRESO on ADNINGRESO.OID = ADNEGRESO. ADNINGRESO
            inner join GENDETCON on ADNINGRESO.GENDETCON = GENDETCON.OID
            inner join ADNCENATE on ADNINGRESO.ADNCENATE=ADNCENATE.OID
            inner join GENCONTRA on GENDETCON.GENCONTRA1=GENCONTRA.OID
            inner join GEENENTADM on GENCONTRA.DGNENTADM1=GEENENTADM.OID
            inner join INNPRODUC on SLNPROHOJ.INNPRODUC1=INNPRODUC.OID
            inner join INNGRUPO on INNPRODUC.IGRCODIGO = INNGRUPO.OID
            inner join INNSUBGRU on INNPRODUC.ISGCODIGO = INNSUBGRU.OID
            inner join GENMEDICO on SLNSERPRO.GENMEDICO1=GENMEDICO.OID
            inner join SLNORDSER on SLNSERPRO.SLNORDSER1=SLNORDSER.OID AND SLNORDSER.SOSESTADO <>2
            inner join GENARESER on SLNORDSER.GENARESER1=GENARESER.OID
            inner join CTNCENCOS on GENARESER.CTNCENCOS1=CTNCENCOS.OID
            WHERE 
            (ADNINGRESO.AINFECING >=TO_DATE('"""+fecha_in+""" 00:00:00','DD/MM/YYYY hh24:mi:ss') AND ADNINGRESO.AINFECING <=TO_DATE('"""+fecha_fin+""" 23:59:59','DD/MM/YYYY hh24:mi:ss'))
            and ADNINGRESO.AINESTADO IN (0,3)
            and SLNSERPRO.SERAPLPRO=0
            AND ADNCENATE.ACACODIGO >= """+sede_in+"""  AND ADNCENATE.ACACODIGO <= """+sede_fin+"""

            UNION ALL

            SELECT  
            '' Tipo_Documento,
            SLNORDSER.SOSORDSER Numero_Orden,
            to_char(SLNORDSER.SOSFECORD,'DD/MM/YYYY') Fecha_Orden,
            ADNINGRESO.AINCONSEC Numero_Ingreso,
            to_char(ADNINGRESO.AINFECING,'DD/MM/YYYY') Fecha_Ingreso,
            to_char(ADNEGRESO.ADEFECSAL,'DD/MM/YYYY') Fecha_Egreso,
            GENDETCON.GDECODIGO Codigo_Plan,
            GENDETCON.GDENOMBRE Nombre_Plan,
            ADNCENATE.ACACODIGO Codigo_CentroA,
            ADNCENATE.ACANOMBRE Nombre_CentroA,
            GEENENTADM.ENTCODIGO Codigo_Entidad,
            GEENENTADM.ENTNOMBRE Nombre_Entidad,
            CASE 
            WHEN GENPACIEN.PACTIPDOC=0 THEN 'Ninguno'
            WHEN GENPACIEN.PACTIPDOC=1 THEN 'Cédula de ciudadanía'
            WHEN GENPACIEN.PACTIPDOC=2 THEN 'Cédula de extranjería'
            WHEN GENPACIEN.PACTIPDOC=3 THEN 'Tarjeta de identidad'
            WHEN GENPACIEN.PACTIPDOC=4 THEN 'Registro civil'
            WHEN GENPACIEN.PACTIPDOC=5 THEN 'Pasaporte'
            WHEN GENPACIEN.PACTIPDOC=6 THEN 'Adulto sin identificación'
            WHEN GENPACIEN.PACTIPDOC=7 THEN 'Menor sin identificación'
            WHEN GENPACIEN.PACTIPDOC=8 THEN 'Número único de identificación'
            WHEN GENPACIEN.PACTIPDOC=9 THEN 'Salvoconducto'
            WHEN GENPACIEN.PACTIPDOC=10 THEN 'Certificado nacido vivo'
            WHEN GENPACIEN.PACTIPDOC=11 THEN 'Carné Diplomático'
            WHEN GENPACIEN.PACTIPDOC=12 THEN 'Permiso Especial de Permanencia'
            WHEN GENPACIEN.PACTIPDOC=14 THEN 'Permiso por protección temporal'
            WHEN GENPACIEN.PACTIPDOC=15 THEN 'Documento de identificación extranjero'
            END Tipo_Documento_Paciente,
            GENPACIEN.PACNUMDOC Numero_de_identificacion,
            GENPACIEN.GPANOMCOM Paciente,
            to_char(GENPACIEN.GPAFECNAC,'DD/MM/YYYY')PacienteFechaNac,
            CASE
            WHEN GENDETCON.GDETIPPLA= 0  THEN 'Ninguno'
            WHEN GENDETCON.GDETIPPLA= 1  THEN 'Subsidiado'
            WHEN GENDETCON.GDETIPPLA= 2  THEN 'Vinculado'
            WHEN GENDETCON.GDETIPPLA= 3  THEN 'Contributivo'
            WHEN GENDETCON.GDETIPPLA= 4  THEN 'Particular'
            WHEN GENDETCON.GDETIPPLA= 5  THEN 'AccidenteTransito'
            WHEN GENDETCON.GDETIPPLA= 6  THEN 'Otros'
            WHEN GENDETCON.GDETIPPLA= 7  THEN 'IPSPrivada'
            WHEN GENDETCON.GDETIPPLA= 8  THEN 'EmpresaRegimenEspecial'
            WHEN GENDETCON.GDETIPPLA= 9  THEN 'FOSYGATraumaMayor'
            WHEN GENDETCON.GDETIPPLA= 10 THEN 'EventosCatastroficos'
            WHEN GENDETCON.GDETIPPLA= 11 THEN 'CompañiasAseguradoras'
            WHEN GENDETCON.GDETIPPLA= 12 THEN 'Desplazados'
            WHEN GENDETCON.GDETIPPLA= 13 THEN 'ConvenioUCI'
            END TipoPlan,
            CASE 
            WHEN ADNINGRESO.AINTIPING=0 THEN 'Ninguno' 
            WHEN ADNINGRESO.AINTIPING=1 THEN 'Ambulatorio'
            WHEN ADNINGRESO.AINTIPING=2 THEN 'Hospitalario'
            end as TIPO_INGRESO,
            GENSERIPS.SIPCODIGO Servicio_Codigo,
            SLNSERPRO.SERDESSER Servicio_Nombre,
            SLNSERPRO.SERCANTID Cantidad, 
            SLNSERPRO.SERFECSER FechaServicio,
            GENGRUPOS.GGRCODIGO GrupoSerCodigo,
            GENGRUPOS.GGRNOMBRE GrupoSerNombre,
            GENSUBGRU.GSUCODIGO SubgrupoCodigo,
            GENSUBGRU.GSUNOMBRE SubgrupoNombre,
            GENMEDICO.GMECODIGO MedicoCodigo,
            GENMEDICO.GMENOMCOM MedicoNombre,
            GENARESER.GASCODIGO AreaCodigo,
            GENARESER.GASNOMBRE AreaNombre,
            CTNCENCOS.CCCODIGO CentroCodigo,
            CTNCENCOS.CCNOMBRE CentroNombre,
            To_Char(GENGRUQUI.SGQCODIGO) GrupoQuiCodigo,
            To_Char(GENGRUQUI.SGQNOMBRE) GrupoQuiNombre,
            SLNSERPRO.SERCANTID Cantidad, 
            SLNSERPRO.SERVALPAC ValPac,
            SLNSERPRO.SERVALENT ValEnt,
            CASE WHEN GENGRUQUI1 IS NULL THEN ((round(GENMANTAR.SMTVALSER*SLNSERPRO.SERCANTID/100))*100)ELSE ((round(SLNSERPRO.SERVALPRO*SLNSERPRO.SERCANTID/100))*100)END TotSer,
            To_Char(genmanser.GENGRUQUI1) Grupoquirurgico
            FROM SLNSERPRO
            inner join SLNSERHOJ on SLNSERPRO.OID=SLNSERHOJ.OID
            inner join ADNINGRESO on SLNSERPRO.ADNINGRES1=ADNINGRESO.OID
            inner join GENPACIEN on  ADNINGRESO.GENPACIEN = GENPACIEN.oid
            left  join ADNEGRESO on ADNINGRESO.OID = ADNEGRESO. ADNINGRESO
            inner join GENDETCON on ADNINGRESO.GENDETCON = GENDETCON.OID
            inner join ADNCENATE on ADNINGRESO.ADNCENATE=ADNCENATE.OID
            inner join GENCONTRA on GENDETCON.GENCONTRA1=GENCONTRA.OID
            inner join GEENENTADM on GENCONTRA.DGNENTADM1=GEENENTADM.OID
            inner join GENSERIPS on SLNSERHOJ.GENSERIPS1 = GENSERIPS.OID
            inner join GENGRUPOS on GENSERIPS.GENGRUPOS1=GENGRUPOS.OID
            inner join GENSUBGRU on GENSERIPS.GENSUBGRU1=GENSUBGRU.OID
            inner join GENMANSER on  SLNSERHOJ.GENMANSER1=GENMANSER.OID
            inner join GENMANTAR on GENMANSER.OID=GENMANTAR.GENMANSER1 AND  GENMANTAR.OID = (SELECT MAX(OID) FROM GENMANTAR WHERE GENMANSER.OID=GENMANTAR.GENMANSER1)
            inner join GENMEDICO on SLNSERPRO.GENMEDICO1=GENMEDICO.OID
            inner join SLNORDSER on SLNSERPRO.SLNORDSER1=SLNORDSER.OID AND SLNORDSER.SOSESTADO <>2
            inner join GENARESER on SLNORDSER.GENARESER1=GENARESER.OID
            inner join CTNCENCOS on GENARESER.CTNCENCOS1=CTNCENCOS.OID
            left join GENGRUQUI on GENMANSER.GENGRUQUI1=GENGRUQUI.OID
            WHERE 
            (ADNINGRESO.AINFECING >=TO_DATE('"""+fecha_in+""" 00:00:00','DD/MM/YYYY hh24:mi:ss') AND ADNINGRESO.AINFECING <=TO_DATE('"""+fecha_fin+""" 23:59:59','DD/MM/YYYY hh24:mi:ss'))
            AND ADNCENATE.ACACODIGO >= """+sede_in+"""  AND ADNCENATE.ACACODIGO <= """+sede_fin+"""
            and ADNINGRESO.AINESTADO IN (0,3)
            and SLNSERPRO.SERAPLPRO=0
        """
    )
    return sql

def censo_diario(): 
    censo = """
    SELECT 
    AINCONSEC NUMINGRESO, 
    GPANOMCOM PACIENTE,
    CASE WHEN GCFNOMBRE IS NULL THEN 'MEDICAMENTOS' ELSE TO_CHAR(GCFNOMBRE) END GRUPO_FAC,
    substr(acanombre, instr(acanombre,'-')-LENGTH(acanombre)+1) AS SEDE,
    HSUNOMBRE PISO,
    HISTORICO.ESTANCIA, 
    SIPCODCUP CUP,   
    SERDESSER SERVICIO, 
    TO_CHAR(AINFECING,'DD/MM/YYYY') FECHA_INGRESO,
    TO_CHAR(SERFECSER,'DD/MM/YYYY') FECHA_SERVICIO,
    TO_CHAR(ADEFECSAL,'DD/MM/YYYY') FECHA_EGRESO, 
    ROUND((SERFECSER-AINFECING),0) AS INGR_VS_SERV, 
    ROUND((ADEFECSAL-SERFECSER),0) AS EGRESO_VS_SERV,
    ROUND((NVL(hesfecsal, SYSDATE)-AINFECING),0) AS ESTANCIA_APROX, 
    ROUND((CASE SERAPLPRO WHEN 0 THEN SERVALPRO ELSE 0 END)*(SERCANTID)) VALORSERV
    FROM SLNSERPRO
    LEFT JOIN SLNSERHOJ ON SLNSERHOJ.OID = SLNSERPRO.OID
    LEFT JOIN GENSERIPS ON SLNSERHOJ.GENSERIPS1 = GENSERIPS.OID
    LEFT JOIN GENCONFAC ON GENCONFAC.OID = GENSERIPS.GENCONFAC1
    INNER JOIN ADNINGRESO ON ADNINGRESO.OID = SLNSERPRO.ADNINGRES1
    inner join GENPACIEN ON GENPACIEN.OID = ADNINGRESO.GENPACIEN
    LEFT JOIN ADNEGRESO ON ADNINGRESO.OID = ADNEGRESO.ADNINGRESO
    LEFT JOIN SLNFACTUR ON ADNINGRESO.OID = SLNFACTUR.ADNINGRESO
    inner JOIN HPNDEFCAM ON HPNDEFCAM.ADNINGRESO = ADNINGRESO.OID --> con INNER JOIN: Pacientes acostados | con LEFT JOIN: Todos los pacientes
    inner JOIN HPNSUBGRU ON HPNDEFCAM.HPNSUBGRU = HPNSUBGRU.OID --> con INNER JOIN: Pacientes acostados | con LEFT JOIN: Todos los pacientes
    inner JOIN ADNCENATE ON HPNDEFCAM.ADNCENATE = ADNCENATE.OID --> con INNER JOIN: Pacientes acostados | con LEFT JOIN: Todos los pacientes
    left join (select adningres, hsunombre ESTANCIA, hcacodigo, hesfecing, hesfecsal
            from hpnestanc 
            inner join hpndefcam on hpndefcam.oid = hpnestanc.hpndefcam 
            inner join hpnsubgru on hpnsubgru.oid = hpndefcam.hpnsubgru 
            order by hesfecing) HISTORICO ON HISTORICO.ADNINGRES = ADNINGRESO.OID --> Se pueden repetir registros si hay pacientes ocupando dos camas
    WHERE 
    --AINFECING >=:FECHA_INI AND AINFECING <=:FECHA_FIN AND  -->Para filtrar por fecha de ingreso
    --ACACODIGO LIKE :SEDE  -->Para filtrar por sede
    --AND HSUNOMBRE LIKE '%'||:SERVICIO||'%' -->Para filtrar por Servicio
    /*and */serfecser >=hesfecing and serfecser <(NVL(hesfecsal, SYSDATE))  -->para discriminar los servicios por la cama donde estuvo hospitalizado
    order by 4,5,9,1,2
    """
    return censo 

def historicos_servicios():
    historico = """ 
    select 
    substr(SEDE_ING.ACANOMBRE, instr(SEDE_ING.ACANOMBRE,'-')-LENGTH(SEDE_ING.ACANOMBRE)+1) SEDE_INGRESO, 
    ainconsec,
    CASE 
    WHEN AINTIPING=0 THEN 'Ninguno' 
    WHEN AINTIPING=1 THEN 'Ambulatorio'
    WHEN AINTIPING=2 THEN 'Hospitalario'
    end as TIPO_INGRESO,
    extract(year from to_Date(ainfecing,'dd/mm/yyy')) año,
    extract(month from to_Date(ainfecing,'dd/mm/yyy')) mes,
    CASE WHEN FACTURADO.ADNINGRESO IS NULL THEN 'PENDIENTE' ELSE 'FACTURADO' END ESTADO,
    NVL(SEDE_HOSP,substr(SEDE_ING.ACANOMBRE, instr(SEDE_ING.ACANOMBRE,'-')-LENGTH(SEDE_ING.ACANOMBRE)+1)) SEDE_PROD,
    GRUPO_FAC, 
    NUMREG,
    cantidad,
    TOTSER,
    TOTALFAC
    from adningreso INGRESO
    inner join adncenate SEDE_ING on INGRESO.ADNCENATE = SEDE_ING.OID
    LEFT JOIN (
        SELECT ADNINGRESO, SUM(SFAVALCAR) TOTALFAC 
        FROM SLNFACTUR WHERE SFADOCANU=0 GROUP BY ADNINGRESO) FACTURADO ON FACTURADO.ADNINGRESO = INGRESO.OID
    INNER JOIN 
    (select DISTINCT 
        adningres1,
        CASE WHEN GCFNOMBRE IS NULL THEN 'MEDICAMENTOS' ELSE TO_CHAR(GCFNOMBRE) END GRUPO_FAC,
        SEDE_HOSP,
        COUNT(*) NUMREG,
        SUM(SLNSERPRO.SERCANTID) Cantidad, 
        SUM(CASE WHEN SLNSERPRO.SERVALPRO=0 THEN (INNMSUMPA.ISMVALPRO*SLNSERPRO.SERCANTID) ELSE (SLNSERPRO.SERVALPRO*SLNSERPRO.SERCANTID) END) TotSer
    FROM SLNSERPRO
    left join SLNSERHOJ on SLNSERPRO.OID=SLNSERHOJ.OID
    left join SLNPROHOJ on SLNSERPRO.OID=SLNPROHOJ.OID
    left JOIN GENSERIPS on (SLNSERHOJ.GENSERIPS1 = GENSERIPS.OID)
    left JOIN GENCONFAC ON GENCONFAC.OID = GENSERIPS.GENCONFAC1
    left join INNCSUMPA on SLNPROHOJ.INNCSUMPA1=INNCSUMPA.OID
    left join INNMSUMPA on SLNPROHOJ.OID=INNMSUMPA.SLNPROHOJ
    left join (
    select adningres, substr(SEDE.ACANOMBRE, instr(SEDE.ACANOMBRE,'-')-LENGTH(ACANOMBRE)+1) SEDE_HOSP, hesfecing, hesfecsal
    from hpnestanc 
        inner join hpndefcam on hpndefcam.oid = hpnestanc.hpndefcam 
        inner join hpnsubgru on hpnsubgru.oid = hpndefcam.hpnsubgru 
        inner join adncenate SEDE on hpndefcam.adncenate = SEDE.oid
        order by hesfecing) HISTORICO ON (HISTORICO.ADNINGRES = ADNINGRES1 AND serfecser >=historico.hesfecing and serfecser <(NVL(historico.hesfecsal, SYSDATE)))
        group by adningres1, CASE WHEN GCFNOMBRE IS NULL THEN 'MEDICAMENTOS' ELSE TO_CHAR(GCFNOMBRE) END, SEDE_HOSP) LIQUIDACION ON LIQUIDACION.ADNINGRES1 = INGRESO.OID
    where extract(year from to_Date(ainfecing,'dd/mm/yyy'))=2022
    """
    return historico

def camas():
    query_camas = f"""select adningreso.ainconsec as CONSECUTIVO, adningreso.ainfecing as FECHA_INGRESO,
        CASE 
        WHEN adningreso.aintiping=0 THEN 'Ninguno'
        WHEN adningreso.aintiping=1 THEN 'Ambulatorio'
        WHEN adningreso.aintiping=2 THEN 'Hospitalario'
        end as TIPO_INGRESO,
        CASE 
        WHEN adningreso.ainestado=0 THEN 'Registrado'
        WHEN adningreso.ainestado=1 THEN 'Facturado'
        WHEN adningreso.ainestado=2 THEN 'Anulado'
        WHEN adningreso.ainestado=3 THEN 'Bloqueado'
        WHEN adningreso.ainestado=4 THEN 'Cerrado'
        end as ESTADO_INGRESO,
        CASE
        WHEN adningreso.ainurgcon=0 THEN 'Urgencias'
        WHEN adningreso.ainurgcon=1 THEN 'Consulta_Externa'
        WHEN adningreso.ainurgcon=2 THEN 'Nacido_Hospital'
        WHEN adningreso.ainurgcon=3 THEN 'Remitido'
        WHEN adningreso.ainurgcon=4 THEN 'Hosp_Urgencias'
        WHEN adningreso.ainurgcon=5 THEN 'Hospitalizacion'
        WHEN adningreso.ainurgcon=6 THEN 'Imagenes'
        WHEN adningreso.ainurgcon=7 THEN 'Laboratorio'
        WHEN adningreso.ainurgcon=8 THEN 'Urgencia_Ginecologica'
        WHEN adningreso.ainurgcon=9 THEN 'Quirofano'
        WHEN adningreso.ainurgcon=10 THEN 'Cirugia_Ambulatoria'
        WHEN adningreso.ainurgcon=11 THEN 'Cirugia_Programada'
        WHEN adningreso.ainurgcon=12 THEN 'Uci_Neonatal'
        WHEN adningreso.ainurgcon=13 THEN 'Uci_Adulto'
        WHEN adningreso.ainurgcon=-1 THEN 'Ninguno'
        end as INGRESO_POR,
        CASE 
        WHEN adningreso.aincauing=0 THEN 'Ninguna'
        WHEN adningreso.aincauing=1 THEN 'Enfermedad_Profesional'
        WHEN adningreso.aincauing=2 THEN 'Heridos_en_Combate'
        WHEN adningreso.aincauing=3 THEN 'Enfermedad_General_Adulto'
        WHEN adningreso.aincauing=4 THEN 'Enfermedad_General_Pediatria'
        WHEN adningreso.aincauing=5 THEN 'Odontología'
        WHEN adningreso.aincauing=6 THEN 'Accidente_de_Transito'
        WHEN adningreso.aincauing=7 THEN 'Catastrofe_Fisalud'
        WHEN adningreso.aincauing=8 THEN 'Quemados'
        WHEN adningreso.aincauing=9 THEN 'Maternidad'
        WHEN adningreso.aincauing=10 THEN 'Accidente_Laboral'
        WHEN adningreso.aincauing=11 THEN 'Cirugia_Programada'
        end as CAUSA_INGRESO,
        CASE
        WHEN adningreso.aintiprie=0 THEN 'Ninguna'
        WHEN adningreso.aintiprie=1 THEN 'Accidente_de_Transito'
        WHEN adningreso.aintiprie=2 THEN 'Catastrofe'
        WHEN adningreso.aintiprie=3 THEN 'Enfermedad_General_y_Maternidad'
        WHEN adningreso.aintiprie=4 THEN 'Accidente_de_Trabajo'
        WHEN adningreso.aintiprie=5 THEN 'Enfermedad_Profesional'
        WHEN adningreso.aintiprie=6 THEN 'Atención_Inicial_de_Urgencias'
        WHEN adningreso.aintiprie=7 THEN 'Otro_Tipo_de_Accidente'
        WHEN adningreso.aintiprie=8 THEN 'Lesión_por_Agresión'
        WHEN adningreso.aintiprie=9 THEN 'Lesión_Autoinfligida'
        WHEN adningreso.aintiprie=10 THEN 'Maltrato_Físico'
        WHEN adningreso.aintiprie=11 THEN 'Promoción_y_Prevención'
        WHEN adningreso.aintiprie=12 THEN 'Otro'
        WHEN adningreso.aintiprie=13 THEN 'Accidente_Rábico'
        WHEN adningreso.aintiprie=14 THEN 'Accidente_Ofídico'
        WHEN adningreso.aintiprie=15 THEN 'Sospecha_de_Abuso_Sexual'
        WHEN adningreso.aintiprie=16 THEN 'Sospecha_de_Violencia_Sexual'
        WHEN adningreso.aintiprie=17 THEN 'Sospecha_de_Maltrato_Emocional'
        end as TIPO_RIESGO,
        adncenate.acacodigo as CENTRO_DE_ATENCION,
        gendetcon.gdenombre as PLAN_BENEFICIOS, geenentadm.entnombre as EPS,
        hpnsubgru.hsunombre AS NOMBRE_CAMA,AINFECHOS as FECHAHOSP,AINFECEGRE as FECHAEGRESO, AINFECFAC as FECHAFACT    
        from adningreso
        inner join genpacien on adningreso.genpacien=genpacien.oid
        inner join gendetcon on adningreso.gendetcon=gendetcon.oid
        inner join gencontra on gendetcon.gencontra1=gencontra.oid
        inner join geenentadm on gencontra.dgnentadm1=geenentadm.oid
        inner join adncenate on adningreso.adncenate=adncenate.oid
        left join ADNEGRESO on ADNINGRESO.ADNEGRESO = ADNEGRESO.OID
        left join HPNDEFCAM on adningreso.HPNDEFCAM = HPNDEFCAM.oid
        left join HPNSUBGRU on HPNDEFCAM.HPNSUBGRU = hpnsubgru.oid
    
        where adningreso.ainfecing BETWEEN TO_DATE('2021-10-31 00:00:00','YYYY-MM-DD HH24:MI:SS') and TO_DATE({ayerstr},'YYYY-MM-DD HH24:MI:SS')
    """
    return query_camas

def radicados():
    q_radicados = '''
    select slnfactur.sfanumfac,CASE 
        WHEN crnradfacc.crfestado=0 THEN 'Registrado'
        WHEN crnradfacc.crfestado=1 THEN 'Confirmado'
        WHEN crnradfacc.crfestado=2 THEN 'Radicado Entidad'
        WHEN crnradfacc.crfestado=3 THEN 'Anulado'
        WHEN crnradfacc.crfestado=-1 THEN 'No Registrado'
        end as ESTADO,crnradfacd.CRFFECRAD
    from slnfactur 
    inner join CRNRADFACD on  CRNRADFACD.slnfactur = slnfactur.oid
    inner join crnradfacc on  crnradfacc.oid = CRNRADFACD.CRNRADFACC'''
    return q_radicados

def facturas():
    q_facturas= f'''SELECT 
    adningreso.ainconsec as INGCONSECUTIVO,
    SFANUMFAC FACTURA, SFAFECFAC,
    trunc(SFATOTFAC,0) VALOR,
    SFAVALREC RECIBO_DE_CAJA,
    SFAVALFRA FRANQUICIA,
    SUM((SFATOTFAC+SFAVALREC)-SFAVALFRA) VALORTOTAL,
    (CASE 
    WHEN SFATIPDOC='0'  THEN 'Factura_Paciente' 
    WHEN SFATIPDOC='1'  THEN 'Factura_Entidad'
    WHEN SFATIPDOC='2'  THEN 'Factura_CapitadaEstatal'
    WHEN SFATIPDOC='5'  THEN 'CuentaCobro_EntidadCapitada'
    WHEN SFATIPDOC='6'  THEN 'Factura_EntidadCapitada'
    WHEN SFATIPDOC='7'  THEN 'Factura_Global'
    WHEN SFATIPDOC='8'  THEN 'CuentaCobro_PFGP'
    WHEN SFATIPDOC='16' THEN 'Factura_GlobalPFGP'
    ELSE '' END) TIPO_FACTURA,
    GENUSUARIO1 as FACTURADOR, usudescri as NOMFACT
    FROM SLNFACTUR
    inner join ADNINGRESO ON SLNFACTUR.ADNINGRESO=adningreso.oid
    LEFT JOIN  ADNCENATE ON ADNINGRESO.ADNCENATE=adncenate.oid
    inner join genusuario on slnfactur.genusuario1 = genusuario.oid
    WHERE (SFAFECFAC BETWEEN TO_DATE('2021-10-31 00:00:00','YYYY-MM-DD HH24:MI:SS') and TO_DATE({ayerstr},'YYYY-MM-DD HH24:MI:SS')
    AND SFADOCANU=0 
    AND SFAESTDOC!=0 
    AND CTNTIPCOM1 IS NOT NULL 
    AND SFATIPDOC NOT IN (3,4,9,10,11,12,13,14,15)) OR  (SFAFECFAC BETWEEN TO_DATE('2021-10-31 00:00:00','YYYY-MM-DD HH24:MI:SS') and TO_DATE({ayerstr},'YYYY-MM-DD HH24:MI:SS') 
    AND SFADOCANU=0
    AND SFAESTDOC!=0 AND CTNTIPCOM3 IS NOT NULL AND SFATIPDOC NOT IN (3,4,9,10,11,12,13,14,15)) 
    GROUP BY adningreso.ainconsec,SFAFECFAC,SFANUMFAC,SFATOTFAC,SFAVALREC,SFAVALFRA,SFATIPDOC,GENUSUARIO1,genusuario.usudescri
    ORDER BY SFANUMFAC'''
    return q_facturas

def ventas():
    q_ventas= f'''SELECT ADNINGRESO.AINCONSEC AS INGRESO,
    COUNT(SERCANTID) AS CANTIDAD, SUM((SERCANTID * SERVALPRO))AS VALOR,SLNSERPRO.SERFECSER AS FECHASER
    FROM SLNSERPRO
    INNER JOIN ADNINGRESO ON ADNINGRESO.OID = SLNSERPRO.ADNINGRES1
    INNER JOIN SLNORDSER ON SLNORDSER.OID=SLNSERPRO.SLNORDSER1
    WHERE ADNINGRESO.AINESTADO IN (0,1,3) 
    --AND GDEPAQUET=1 */
    AND SLNSERPRO.SERFECSER >= TO_DATE('2021-10-31 00:00:00','YYYY-MM-DD HH24:MI:SS') AND SLNSERPRO.SERFECSER<=TO_DATE({ayerstr},'YYYY-MM-DD HH24:MI:SS') AND SLNORDSER.SOSESTADO != 2 
    and slnserpro.seraplpro !=1
    --AND adningreso.adnegreso IS NOT NULL/
    GROUP BY ADNINGRESO.AINCONSEC,SLNSERPRO.SERFECSER'''

    return q_ventas

def recaudos():
    q_recaudos = f'''SELECT CCTNUMTRA TRASLADO,CRNCXC.CXCDOCUME factura, CXCDOCFECVEN FECHA_VENCIMIENTO, CRNCTRASL.CCTFECTRA FECHA_TRASLADO,
    CMTNVALOR VALOR_TRASLADO, CRNSALDO SALDO_CARTERA 

    FROM CRNMTRASL --DETALLE DEL TRASLADO

    INNER JOIN CRNCTRASL ON CRNCTRASL.OID = CRNMTRASL.CRNCTRASL --CABECERA TRASLADO
    INNER JOIN GENTERCER ON GENTERCER.OID = CRNMTRASL.GENTERCER
    INNER JOIN CRNCXC ON CRNCXC.OID = CRNMTRASL.CRNCXC

    where gentercer.tertipcon in (1,2,3)
    order by 2 desc'''

    return q_recaudos

def indicadores_urg():
    
    query_productos = f"""
    SELECT acacodigo SEDE,TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,'01. NUMERO DE CAMILLA DEL SERVICIO DE URGENCIAS' AS INDICADOR,  count(*) TOTAL
    FROM HPNDEFCAM 
    INNER JOIN ADNCENATE ON ADNCENATE.OID = HPNDEFCAM.ADNCENATE
    WHERE HPNDEFCAM.HCAOBSHOS =2 GROUP BY ACACODIGO

    UNION

    SELECT ACACODIGO SEDE,TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,'02. NUMERO DE CONSULTORIOS PARA LA ATENCION DE URGENCIAS ' INDICADOR, COUNT(*) TOTAL 
    FROM CMNCONSUL
    INNER JOIN ADNCENATE ON ADNCENATE.OID = CMNCONSUL.ADNCENATE
    WHERE CMNCONSUL.CCNURGEN=1
    GROUP BY ACACODIGO

    UNION

    SELECT 
    ACACODIGO SEDE, 
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,
    /*EXTRACT(MONTH FROM TO_DATE(hcnfolio.HCFECFOL, 'dd/mm/yyy')) mes, */
    '03. NUMERO DE CONSULTAS O INGRESOS AL SERVICIO DE URGENCIA GENERAL (INCLUYE REANIMACION)' INDICADOR,  
    count(*) TOTAL
    FROM HCNFOLIO 
    INNER JOIN HCNTIPHIS ON HCNFOLIO.HCNTIPHIS = HCNTIPHIS.OID
    INNER JOIN ADNINGRESO ON HCNFOLIO.ADNINGRESO = ADNINGRESO.OID
    INNER JOIN ADNCENATE ON ADNCENATE.OID = ADNINGRESO.ADNCENATE
    WHERE HCNTIPHIS.OID = 3 --
    --AND EXTRACT(YEAR FROM TO_DATE(hcnfolio.HCFECFOL, 'dd/mm/yyy')) = 2022
    AND HCFECFOL BETWEEN SYSDATE-1 AND SYSDATE
    group by ACACODIGO, SYSDATE /*, EXTRACT(MONTH FROM TO_DATE(HCFECFOL, 'dd/mm/yyy'))*/

    UNION 

    SELECT ACACODIGO SEDE,TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA, '04. NRO CAMAS DE OBSERVACION' INDICADOR, COUNT(*) TOTAL 
    FROM HPNDEFCAM 
    INNER JOIN ADNCENATE ON ADNCENATE.OID = HPNDEFCAM.ADNCENATE
    WHERE HPNDEFCAM.HCAOBSHOS =2 AND HPNDEFCAM.hpngrupoS=5
    group by acacodigo

    UNION

    SELECT 
    ACACODIGO AS SEDE,
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,
    CASE WHEN genpacien.GPASEXPAC=1 THEN '05. NUMEROS DE PACIENTES EN OBSERVACION ADULTOS HOMBRES' ELSE '05. NUMEROS DE PACIENTES EN OBSERVACION ADULTOS MUJERES' END INDICADOR, 
    count(*) TOTAL
    FROM HCNFOLIO 
    INNER JOIN HCNTIPHIS ON HCNFOLIO.HCNTIPHIS = HCNTIPHIS.OID
    INNER JOIN ADNINGRESO ON HCNFOLIO.ADNINGRESO = ADNINGRESO.OID
    INNER JOIN GENDETCON ON GENDETCON.OID = ADNINGRESO.GENDETCON
    INNER JOIN ADNCENATE ON ADNCENATE.OID = ADNINGRESO.ADNCENATE
    inner join hpndefcam on hpndefcam.oid = adningreso.hpndefcam
    inner join genpacien on genpacien.oid = adningreso.genpacien
    WHERE HCNTIPHIS.OID = 3
    and HPNDEFCAM.HCAOBSHOS =2 AND HPNDEFCAM.hpngrupoS=5
    AND HCFECFOL BETWEEN SYSDATE-1 AND SYSDATE
    --AND EXTRACT(YEAR FROM TO_DATE(hcnfolio.HCFECFOL, 'dd/mm/yyy')) = 2022
    group by ACACODIGO, SYSDATE, GPASEXPAC

    UNION

    SELECT 
    ACACODIGO SEDE, 
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA, 
    '06. NUMERO DE PACIENTES VIVOS EGRESADOS POR URGENCIAS' AS INDICADOR,
    COUNT(*) TOTAL 
    FROM ADNEGRESO
    INNER JOIN ADNINGRESO ON ADNINGRESO.OID = ADNEGRESO.ADNINGRESO
    INNER JOIN ADNCENATE ON ADNINGRESO.ADNCENATE = ADNCENATE.OID
    WHERE ADEESTPAC NOT IN (3, 4) --ESTADO VIVO 
    AND ADEALTURG = 1 --8 Urgencias
    AND ADNEGRESO.ADEFECSAL BETWEEN SYSDATE-1 AND SYSDATE
    --AND EXTRACT(YEAR FROM TO_DATE(ADNEGRESO.ADEFECSAL, 'dd/mm/yyy')) = 2022
    GROUP BY ACACODIGO, SYSDATE

    UNION

    SELECT 
    ACACODIGO SEDE,
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA, 
    TO_CHAR('07. CONSULTAS '||CMANOMBRE) AS INDICADOR,
    COUNT(*) TOTAL
    from cmncitmed 
    INNER JOIN CMNTIPACT ON CMNTIPACT.OID = CMNCITMED.CMNTIPACT 
    INNER JOIN CMNHORMED ON CMNHORMED.OID = CMNCITMED.CMNHORMED
    INNER JOIN GENPACIEN ON GENPACIEN.OID = CMNCITMED.GENPACIEN
    INNER JOIN GENESPECI ON CMNCITMED.GENESPECI = GENESPECI.OID
    INNER JOIN ADNCENATE ON ADNCENATE.OID = CMNHORMED.ADNCENATE
    WHERE CMANOMBRE LIKE '%PSI%' AND CMACONSUL = 1 AND CMATIPCON = 2
    AND CCMFECCIT BETWEEN SYSDATE-1 AND SYSDATE
    --AND EXTRACT(YEAR FROM TO_DATE(CCMFECCIT, 'dd/mm/yyy'))=2022
    GROUP BY ACACODIGO, CMANOMBRE, SYSDATE

    UNION

    select 
    nomsede.ACACODIGO SEDE, 
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA, 
    '08. CONSULTAS PRIORITARIAS (PACIENTES CON TRIAGE 3 O 4)'AS INDICADOR,
    count(*) TOTAL
    FROM HCNTRIAGE RegTriage
    inner join adncenate nomsede on nomsede.oid = RegTriage.adncenate
    INNER JOIN HCNCLAURGTR Triage ON Triage.oid = regtriage.HCNCLAURGTR
    INNER JOIN GENPACIEN paciente ON paciente.oid = RegTriage.genpacien
    INNER JOIN ADNINGRESO ON ADNINGRESO.HCENTRIAGE = RegTriage.OID
    WHERE HCCODIGO IN ('003','004','005')
    AND HCTFECTRI BETWEEN SYSDATE-1 AND SYSDATE
	--AND EXTRACT(YEAR FROM TO_DATE(HCTFECTRI, 'dd/mm/yyy'))=2022
    group by nomsede.ACACODIGO, SYSDATE

    UNION

    SELECT 
    ADNCENATE.ACACODIGO AS SEDE,
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,
    '09. PACIENTES QUE PASARON A HOSPITALIZACION' as INDICADOR,
    count(*) TOTAL
    FROM HCNFOLIO 
    INNER JOIN HCNTIPHIS ON HCNFOLIO.HCNTIPHIS = HCNTIPHIS.OID
    INNER JOIN ADNINGRESO ON HCNFOLIO.ADNINGRESO = ADNINGRESO.OID
    INNER JOIN ADNCENATE ON ADNCENATE.OID = ADNINGRESO.ADNCENATE
    inner join hpndefcam on hpndefcam.oid = adningreso.hpndefcam
    inner join genpacien on genpacien.oid = adningreso.genpacien
    WHERE HCNTIPHIS.OID = 3
    and HPNDEFCAM.HCAOBSHOS =1 ---AND HPNDEFCAM.hpngrupoS=5
    AND HCFECFOL BETWEEN SYSDATE-1 AND SYSDATE
    --AND EXTRACT(YEAR FROM TO_DATE(HCFECFOL, 'dd/mm/yyy'))=2022
    group by ADNCENATE.ACACODIGO, SYSDATE

    UNION

    SELECT
    ACACODIGO AS SEDE,
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,
    '10. NUMERO DE INFECCIONES ASOCIADAS AL PROCESO DE ATENCIÓN' INDICADOR,
    COUNT(*) TOTAL
    FROM HCNINYACC 
    INNER JOIN HCNIYAEVTS ON "HCNIYAEVTS"."InsidentesAccidentes" = HCNINYACC.OID
    INNER JOIN ADNINGRESO ON HCNINYACC.ADNINGRESO = ADNINGRESO.OID
    INNER JOIN HCNFOLIO ON HCNFOLIO.ADNINGRESO = ADNINGRESO.OID
    INNER JOIN HCNTIPHIS ON HCNFOLIO.HCNTIPHIS = HCNTIPHIS.OID
    INNER JOIN ADNCENATE ON ADNCENATE.OID = ADNINGRESO.ADNCENATE
    WHERE "HCNIYAEVTS"."EventosAdversos" = 70 -- INFECCIONES 
    AND HCNTIPHIS.OID = 3 --  PACIENTES CON HISTORIA DE URGENCIAS
    AND IYAFECDOC BETWEEN SYSDATE-1 AND SYSDATE
   -- AND EXTRACT(YEAR FROM TO_DATE(IYAFECDOC, 'dd/mm/yyy'))=2022
    group by ACACODIGO, SYSDATE

    UNION

    SELECT 
    ACACODIGO AS SEDE,
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,
    '11. ACCIDENTE OFIDICO' AS INDICADOR,
    count(*) TOTAL
    FROM HCNFOLIO 
    INNER JOIN HCNTIPHIS ON HCNFOLIO.HCNTIPHIS = HCNTIPHIS.OID
    INNER JOIN ADNINGRESO ON HCNFOLIO.ADNINGRESO = ADNINGRESO.OID
    INNER JOIN ADNEGRESO ON ADNINGRESO.ADNEGRESO = ADNEGRESO.OID
    INNER JOIN ADNDIAEGR ON ADNEGRESO.OID = ADNDIAEGR.ADNEGRESO
    INNER JOIN ADNCENATE ON ADNCENATE.OID = ADNINGRESO.ADNCENATE
    INNER JOIN GENDIAGNO ON GENDIAGNO.OID = ADNDIAEGR.DIACODIGO
    inner join genpacien on genpacien.oid = adningreso.genpacien
    WHERE HCNTIPHIS.OID = 3 AND
    (GENDIAGNO.DIACODIGO LIKE 'T63%' OR
    GENDIAGNO.DIACODIGO LIKE 'X20%') 
    AND ADNDIAEGR.TIPO = 1
    AND HCFECFOL BETWEEN SYSDATE-1 AND SYSDATE
    --AND EXTRACT(YEAR FROM TO_DATE(HCFECFOL, 'dd/mm/yyy'))=2022
    group by ACACODIGO, SYSDATE

    UNION

    SELECT 
    ACACODIGO AS SEDE,
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,
    '12. TERAPIAS RESPIRATORIAS' AS INDICADOR,
    SUM(SERCANTID) TOTAL
    FROM HCNFOLIO 
    INNER JOIN HCNTIPHIS ON HCNFOLIO.HCNTIPHIS = HCNTIPHIS.OID
    INNER JOIN ADNINGRESO ON HCNFOLIO.ADNINGRESO = ADNINGRESO.OID
    INNER JOIN ADNEGRESO ON ADNINGRESO.ADNEGRESO = ADNEGRESO.OID
    INNER JOIN ADNDIAEGR ON ADNEGRESO.OID = ADNDIAEGR.ADNEGRESO
    INNER JOIN ADNCENATE ON ADNCENATE.OID = ADNINGRESO.ADNCENATE
    INNER JOIN GENDIAGNO ON GENDIAGNO.OID = ADNDIAEGR.DIACODIGO
    inner join SLNSERPRO ON SLNSERPRO.ADNINGRES1 = ADNINGRESO.OID
    inner join genpacien on genpacien.oid = adningreso.genpacien
    WHERE HCNTIPHIS.OID = 3 
    AND ADNDIAEGR.TIPO = 1
    AND SERDESSER LIKE '%RESPIRATORIA%'
    AND HCFECFOL BETWEEN SYSDATE-1 AND SYSDATE
    --AND EXTRACT(YEAR FROM TO_DATE(HCFECFOL, 'dd/mm/yyy'))=2022
    group by ACACODIGO, SYSDATE

    UNION

    SELECT 
    ACACODIGO AS SEDE,
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,
    '13. Total Urgencia Ginecológica (REVISAR)' AS INDICADOR,
    count(*) TOTAL
    FROM HCNFOLIO 
    INNER JOIN HCNTIPHIS ON HCNFOLIO.HCNTIPHIS = HCNTIPHIS.OID
    INNER JOIN ADNINGRESO ON HCNFOLIO.ADNINGRESO = ADNINGRESO.OID
    INNER JOIN ADNEGRESO ON ADNINGRESO.ADNEGRESO = ADNEGRESO.OID
    INNER JOIN ADNDIAEGR ON ADNEGRESO.OID = ADNDIAEGR.ADNEGRESO
    INNER JOIN ADNCENATE ON ADNCENATE.OID = ADNINGRESO.ADNCENATE
    INNER JOIN GENDIAGNO ON GENDIAGNO.OID = ADNDIAEGR.DIACODIGO
    inner join genpacien on genpacien.oid = adningreso.genpacien
    WHERE HCNTIPHIS.OID = 3 AND
    (GENDIAGNO.DIACODIGO LIKE '0%') 
    AND ADNDIAEGR.TIPO = 1
    AND HCFECFOL BETWEEN SYSDATE-1 AND SYSDATE
    --AND EXTRACT(YEAR FROM TO_DATE(HCFECFOL, 'dd/mm/yyy'))=2022
    group by ACACODIGO, SYSDATE

    UNION

    SELECT 
    ACACODIGO AS SEDE, 
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,
    '14. MORTALIDAD POR URGENCIAS' AS INDICADOR,
    COUNT(*) TOTAL 
    FROM ADNEGRESO
    INNER JOIN ADNINGRESO ON ADNINGRESO.OID = ADNEGRESO.ADNINGRESO
    INNER JOIN ADNCENATE ON ADNINGRESO.ADNCENATE = ADNCENATE.OID
    WHERE ADEESTPAC IN (3, 4) --ESTADO VIVO 
    AND ADEALTURG = 1 --8 Urgencias
    AND ADNEGRESO.ADEFECSAL BETWEEN SYSDATE-1 AND SYSDATE
    --AND EXTRACT(YEAR FROM TO_DATE(ADNEGRESO.ADEFECSAL, 'dd/mm/yyy'))=2022
    GROUP BY ACACODIGO, SYSDATE

    UNION

    SELECT 
    ACACODIGO AS SEDE,
    TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS') FECHA,
    '15. NUMERO DE REMISIONES' AS INDICADOR,
    count(*) TOTAL
    FROM HCNFOLIO 
    INNER JOIN HCNTIPHIS ON HCNFOLIO.HCNTIPHIS = HCNTIPHIS.OID
    INNER JOIN ADNINGRESO ON HCNFOLIO.ADNINGRESO = ADNINGRESO.OID
    INNER JOIN ADNEGRESO ON ADNINGRESO.ADNEGRESO = ADNEGRESO.OID
    INNER JOIN ADNDIAEGR ON ADNEGRESO.OID = ADNDIAEGR.ADNEGRESO
    INNER JOIN ADNCENATE ON ADNCENATE.OID = ADNINGRESO.ADNCENATE
    INNER JOIN GENDIAGNO ON GENDIAGNO.OID = ADNDIAEGR.DIACODIGO
    INNER JOIN (SELECT ADNINGRESO AS INGRESO FROM HCNREFER INNER JOIN HCNFOLIO ON HCNREFER.HCNFOLIO = HCNFOLIO.OID) REFERENCIA ON REFERENCIA.INGRESO = ADNINGRESO.OID
    inner join genpacien on genpacien.oid = adningreso.genpacien
    WHERE HCNTIPHIS.OID = 3 
    --    and HPNDEFCAM.HCAOBSHOS =2 AND HPNDEFCAM.hpngrupoS=5
    AND HCFECFOL BETWEEN SYSDATE-1 AND SYSDATE
    AND EXTRACT(YEAR FROM TO_DATE(HCFECFOL, 'dd/mm/yyy'))=2022
    group by ACACODIGO, SYSDATE
    """
    return query_productos

def consultas(): 
    fechas = yesterday()
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
    WHERE CMNCITMED.CCMFECASI >= TO_DATE({fechas[1]},'YYYY-MM-DD HH24:MI:SS') AND CMNCITMED.CCMFECASI <= TO_DATE({fechas[0]},'YYYY-MM-DD HH24:MI:SS')
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
    return q_consultas


