# Instrucciones

## Actividad
- Módulo 3. Reto - Diseñando Arquitecturas Resilientes

Estimado estudiante, a continuación se presentan los pasos para desarrollar la actividad del Módulo 3. Lee con atención y desarrolla todos los pasos, entregando las evidencias solicitadas.

## Caso: contexto del negocio

Eres parte del equipo de arquitectura de Sistemas UltraSeguros S.A., una empresa líder que ofrece servicios críticos para múltiples clientes alrededor del mundo. Entre estos servicios se encuentran:
- gestión de transacciones financieras
- análisis de datos en tiempo real
- monitoreo de infraestructuras críticas

El éxito de la compañía depende de un sistema capaz de mantenerse operativo incluso en las peores circunstancias. En un mundo donde los picos de tráfico, errores inesperados y fallos en componentes individuales son inevitables, tus clientes confían en que la plataforma pueda adaptarse, degradarse progresivamente y recuperarse automáticamente sin interrupciones significativas.

La gerencia ha identificado un problema urgente: durante los picos de tráfico, el sistema tiende a fallar bajo carga, afectando la experiencia del cliente y generando pérdidas millonarias. ¿Puedes diseñar una arquitectura que haga que el sistema reaccione a los fallos automáticamente y se recupere con inteligencia?

## El Reto

Tu misión como arquitecto es diseñar y construir un sistema que cumpla con las siguientes características:

### 1. Degradación progresiva y recuperación automática
- Si el sistema detecta fallos recurrentes o altos niveles de errores, debe degradar automáticamente sus capacidades para mantener los servicios críticos.
- Cuando los indicadores de salud regresen a niveles aceptables, el sistema debe recuperar gradualmente todas sus funcionalidades.

### 2. Resiliencia dinámica basada en la salud de los servicios
- Cambios en los niveles de servicio deben registrarse y ser visibles en logs o métricas.

### 3. Pruebas bajo carga
- Se proporcionará un script de pruebas que simula picos de carga e incluye solicitudes con fallos intencionales.
- Tu sistema debe transitar por los 3 niveles de servicio (Full, Degradado, Operación Mínima), recuperarse al nivel inicial y transicionar entre los mismos.

### 4. Tolerancia a fallos
- En estado de Operación Mínima, el sistema debe seguir respondiendo con un mensaje claro cuando la petición falle: `Nivel 3: Sistema bajo mantenimiento, intente más tarde`.
- En estado de Operación Mínima, también debe responder cuando la petición se resuelva con un mensaje: `Nivel 3: Operación al mínimo`.

## Requerimientos técnicos

- **API Gateway**: punto de entrada para todas las solicitudes; enrutar dinámicamente entre niveles de servicio.
- **3 servicios diferentes por nivel**:
  - Nivel 1 (full): todas las capacidades activas.
  - Nivel 2 (degradado): subconjunto de capacidades, priorizando esenciales.
  - Nivel 3 (mínimo): respuesta de mantenimiento.
- **Logs y métricas**: registrar cambios de nivel y métricas clave.

## Pruebas

El script de pruebas K6 simula 6 minutos de solicitudes con carga variable y fallos intencionales. Tu solución debe:
- Pasar por los 3 niveles durante la ejecución.
- Mostrar recuperación completa al final.
- Demostrar degradación y recuperación dinámica.

## Entregables

- **Código fuente**:
  - Archivo ZIP con la implementación completa.
- **Documentación técnica (PDF)**:
  - Decisiones de arquitectura (justificación de componentes y servicios usados).
  - Atributo de calidad más importante (prioridad y motivo).
  - Diagrama de arquitectura.
  - Tácticas de arquitectura (cumplimiento de objetivos).
- **Demostración en vivo o video (2.5 puntos)**:
  - MP4 (máx. 5 min) o enlace de YouTube.
  - Ejecución funcional bajo el script de prueba.
  - Explicación de detección de fallos, degradación y recuperación.
  - Logs y métricas que validen comportamiento esperado.

## Restricciones

- Solo servicios de AWS.
- No se proporciona plantilla inicial.
- No modificar el script de pruebas.

## Objetivo final

Demuestra que tu solución puede mantener el sistema en funcionamiento incluso en las peores circunstancias. Solo las arquitecturas más resilientes e inteligentes superarán el reto.

## Detalles de transiciones esperadas

### Inicio
- El sistema comienza en Nivel 1 (Full Service).

### Degradación
- 5 errores o más: transicionar a Nivel 2 (Degradado).
- 10 errores o más: transicionar a Nivel 3 (Mantenimiento).

### Recuperación
- Desde Nivel 3: si indicadores regresan saludables, ir a Nivel 2.
- Desde Nivel 2: si indicadores están estables, volver a Nivel 1.
