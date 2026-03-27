import boto3
import json
import time
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Inicializamos el cliente fuera del handler para reutilizar conexiones (Optimización)
lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('EstadoSistema')

def lambda_handler(event, context):
    # 1. Alineación de ventana de tiempo (Bloques de 60s)
    ahora = int(time.time())
    min_actual = (ahora // 60) * 60
    min_anterior = min_actual - 60

    try:
        # 2. Procesar Body de K6
        body = json.loads(event.get('body', '{}'))
        es_error = body.get('error', False)

        # 3. Registro Atómico de Salud
        if es_error:
            table.update_item(
                Key={'id': f"bucket_{min_actual}"},
                UpdateExpression="ADD errores :v",
                ExpressionAttributeValues={':v': 1}
            )

        # 4. Consulta de Salud (Minuto anterior)
        res = table.get_item(Key={'id': f"bucket_{min_anterior}"})
        conteo = int(res.get('Item', {}).get('errores', 0))

        # 5. Selección Dinámica de Nivel
        if conteo >= 10:
            nivel = 3
        elif conteo >= 5:
            nivel = 2
        else:
            nivel = 1

        # DESACOPLAMIENTO: Obtenemos el destino desde variables de entorno
        target_arn = os.environ.get(f'NIVEL_{nivel}_ARN')
        
        if not target_arn:
            raise Exception(f"Configuración faltante para NIVEL_{nivel}_ARN")

        # 6. Invocación Síncrona Optimizada
        # Si es nivel 3, pasamos el flag de éxito/error para cumplir los mensajes del reto
        if nivel == 3:
            event['simulate_success'] = not es_error

        logger.info(f"Ruteando a {target_arn} (Basado en {conteo} errores)")

        response = lambda_client.invoke(
            FunctionName=target_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps(event)
        )
        
        # Retornamos directamente el resultado de la hija
        return json.loads(response['Payload'].read())

    except Exception as e:
        logger.error(f"Fallo en Router: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"msg": "Error en capa de ruteo", "dev_log": str(e)})
        }
