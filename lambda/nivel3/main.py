import json

def lambda_handler(event, context):
    # K6 envía el error en el body
    body = json.loads(event.get('body', '{}'))
    is_error_payload = body.get('error', False)

    if is_error_payload:
        msg = "Nivel 3: Sistema bajo mantenimiento, intente mas tarde"
    else:
        msg = "Nivel 3: Operacion al minimo"

    return {
        "statusCode": 200,
        "body": json.dumps(msg)
    }
