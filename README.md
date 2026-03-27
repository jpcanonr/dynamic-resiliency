# Documentación Técnica: Arquitectura de Resiliencia Dinámica

## 1. Prerrequisitos de Implementación

Para desplegar y ejecutar esta solución correctamente, se requieren los siguientes componentes y herramientas:

### 🛠️ Stack Tecnológico

- **Lenguaje de Programación**: Python 3.14 (utilizado para la lógica de todas las funciones Lambda)
- **SDK de AWS**: Boto3 (para la comunicación entre Lambdas y DynamoDB)
- **Herramienta de Pruebas de Carga**: k6 por Grafana (para la ejecución del script de simulación de fallos)

### ☁️ Componentes de AWS (Infraestructura)

#### Amazon API Gateway (HTTP API)

- Debe tener configurada una ruta ANY `/servicio`
- Debe tener una integración con la Lambda `entrada`

#### AWS Lambda (4 funciones)

- **entrada**: El orquestador/router
- **nivel1**: Servicio en estado óptimo
- **nivel2**: Servicio en estado degradado
- **nivel3**: Servicio en estado de mantenimiento

#### Amazon DynamoDB

- Una tabla denominada `EstadoSistema`
- Partition Key: `id` (Tipo: String)

##### ⚙️ Configuración Inicial de la Tabla
Para que el script de pruebas `k6/reto3.js` funcione según la lógica de degradación esperada, se debe crear un ítem inicial en la tabla `EstadoSistema` con los siguientes atributos exactos:

| Atributo | Tipo   | Valor Inicial | Descripción |
| :---     | :---   | :---          | :---        |
| **id** | String | `config`      | Identificador único del estado del sistema. |
| **errors** | Number | `0`            | Contador inicial de fallos. |
| **level** | Number | `1`            | Nivel de servicio inicial (Full Service). |

#### IAM (Identity and Access Management)

- El rol de ejecución de la Lambda `entrada` debe tener permisos para:
  - `dynamodb:UpdateItem`
  - `dynamodb:GetItem`
  - `lambda:InvokeFunction`

### 📋 Configuración Necesaria

- **Variables de Entorno**: La Lambda `entrada` debe tener configuradas las variables `NIVEL_1_ARN`, `NIVEL_2_ARN` y `NIVEL_3_ARN` con los ARNs correspondientes de las funciones de nivel
- **Handler de Lambda**: Asegurarse de que el Runtime Handler esté configurado como `main.lambda_handler` (o el nombre correspondiente a su archivo `.py`)
- **Timeout**: Se recomienda configurar un timeout de al menos 10 segundos para la Lambda `entrada` para absorber la latencia de las invocaciones síncronas

## 2. Decisiones de Arquitectura

La solución se basa en una arquitectura **Serverless Event-Driven**, seleccionada por su capacidad de escalado automático y su modelo de pago por uso, ideal para manejar picos de tráfico inesperados.

### Justificación de Componentes

- **Amazon API Gateway (HTTP API)**: Utilizado como punto de entrada desacoplado. Permite una interfaz REST/HTTP limpia que separa el mundo exterior de la lógica interna.
- **AWS Lambda (Router "Entrada")**: Actúa como el orquestador de inteligencia. Se eligió para centralizar la lógica de evaluación de salud sin sobrecargar las funciones de negocio.
- **Amazon DynamoDB**: Elegido por su latencia de milisegundos y su capacidad de manejar Contadores Atómicos. Es el "estado compartido" necesario para que todas las ejecuciones de Lambda conozcan la salud del sistema.
- **AWS Lambda (Niveles 1, 2, 3)**: Microservicios que contienen la lógica de negocio degradada.

### Decisiones de Consistencia y Desacoplamiento

- **Consistencia Atómica**: Para evitar condiciones de carrera (Race Conditions) durante picos de carga, se implementó la instrucción ADD de DynamoDB. Esto garantiza que cada error reportado por el script K6 sea contado exactamente una vez, permitiendo transiciones de nivel precisas.
- **Desacoplamiento por Variables de Entorno**: Se evitó el hard-coding de ARNs de Lambda. El Router resuelve el destino mediante variables de entorno (NIVEL_X_ARN), permitiendo que los servicios de nivel evolucionen, se renombren o cambien de versión sin necesidad de modificar ni desplegar el código del Router.

## 3. Atributo de Calidad más Importante

El atributo priorizado es la **Resiliencia** (Disponibilidad bajo degradación).

### Justificación

En el contexto de Sistemas UltraSeguros S.A., un fallo total del sistema implica pérdidas millonarias y daño reputacional. Se priorizó que el sistema siempre responda, incluso si la respuesta es de capacidad reducida o un mensaje de mantenimiento controlado.

Es preferible una degradación elegante (Nivel 2 o 3) que un fallo catastrófico (Error 500 o Timeouts), ya que permite mantener la confianza del cliente al informar proactivamente sobre el estado del sistema.

## 3. Diagrama de la Arquitectura (Vista de Componentes)

```text
                                  +-----------------------+
                                  |   Script de Pruebas   |
                                  |      (k6 Runner)      |
                                  +-----------+-----------+
                                              |
                                              | (HTTP POST / JSON)
                                              v
                                  +-----------+-----------+
                                  |   Amazon API Gateway  |
                                  |     (Punto de Entrada)|
                                  +-----------+-----------+
                                              |
                                              v
      +---------------------------------------+---------------------------------------+
      |                                                                               |
      |                          Lambda "entrada" (Router)                            |
      |   1. Procesa Payload (error: true/false)                                      |
      |   2. Registra métrica atómica en DynamoDB                                     |
      |   3. Consulta salud del minuto anterior                                       |
      |   4. Selecciona ARN de destino vía Variables de Entorno                       |
      |                                                                               |
      +-------+-------------------------------+-------------------------------+-------+
              |                               |                               |
      (Si Nivel = 1)                  (Si Nivel = 2)                  (Si Nivel = 3)
              v                               v                               v
    +---------+---------+           +---------+---------+           +---------+---------+
    |  Lambda "nivel1"  |           |  Lambda "nivel2"  |           |  Lambda "nivel3"  |
    |  (Full Service)   |           | (Modo Degradado)  |           | (Mantenimiento)   |
    +-------------------+           +-------------------+           +---------+---------+
                                                                              |
                                                                    +---------+---------+
      +-----------------------+                                     | Mensajes Reto:    |
      |   Amazon DynamoDB     | <-----------------------------------+ "Bajo mant."      |
      |  (Tabla: Estado)      |      (Estado de Salud Global)       | "Op. al mínimo"   |
      +-----------------------+                                     +-------------------+
```

### Flujo de la solución

- **Ingreso**: API Gateway recibe el POST desde K6.
- **Registro**: La Lambda entrada recibe el evento y utiliza Contadores Atómicos para incrementar los fallos en la tabla EstadoSistema sin colisiones de escritura.
- **Evaluación**: Basándose en los errores acumulados en el "bucket" de tiempo anterior, el Router invoca síncronamente la Lambda de nivel correspondiente.
- **Consulta de Salud**: El Router lee los errores acumulados en la ventana de tiempo anterior.
- **Ruteo Dinámico**: Se selecciona el ARN desde las variables de entorno y se invoca la Lambda nivel1, nivel2 o nivel3.
- **Respuesta**: El sistema devuelve un mensaje dinámico. En el Nivel 3, se discrimina si la petición fue exitosa o fallida para responder con los mensajes literales exigidos por el reto

## 4. Tácticas de Arquitectura

Se implementaron tácticas específicas para garantizar que el sistema cumpla con los objetivos de recuperación automática:

### A. Ventana de Tiempo Discreta (Time-Windowing)

Para evitar el "flapping" (oscilación rápida entre niveles), el sistema no reacciona a una sola petición, sino a la salud agregada de ventanas de 60 segundos. Esto alinea el comportamiento del sistema con los ciclos de negocio y las pruebas de carga.

### B. Patrón Circuit Breaker (Disyuntor)

El sistema actúa como un disyuntor:

- **Cerrado (Nivel 1)**: Tráfico normal.
- **Abierto (Nivel 3)**: Cuando los errores superan el umbral de 10 por minuto, el sistema "abre el circuito" para proteger la base de datos y servicios críticos, desviando todo al modo mantenimiento.

### C. Recuperación Automática (Self-Healing)

El sistema es sin estado (stateless) respecto a errores pasados; cada minuto se evalúa de nuevo. Si en el minuto N hubo 10 errores, pero en el minuto N+1 hubo 0, la arquitectura transiciona automáticamente de regreso al Nivel 1 sin intervención humana, basándose en la métrica fresca de DynamoDB.

### D. Observabilidad

Se implementó un logging estructurado que registra: Slot de tiempo, Errores detectados y Nivel asignado. Esto permite auditar las transiciones mediante CloudWatch Logs para validar que el sistema cumplió con los 6 minutos de prueba de forma dinámica.

## 5. Logging y Observabilidad

- Todas las Lambdas usan el logging estándar de AWS Lambda y se asocian automáticamente a grupos de logs de CloudWatch: `AWS/Lambda` -> `LogGroup` generado por nombre de función (por ejemplo, `/aws/lambda/entrada`).
- El código de `lambda/entrada/main.py` inicializa un logger global:

```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
```

- A lo largo del handler principal (`lambda_handler`) se emiten eventos de log:
  - `logger.info(...)` para ruteos exitosos y decisiones de nivel
  - `logger.error(...)` para excepciones de ruteo y errores internos.

- En caso de error en el router, la Lambda devuelve un HTTP 500 y escribe el mensaje dentro de `dev_log`, además del log de error que se puede revisar en CloudWatch.
