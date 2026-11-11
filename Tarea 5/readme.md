# Tarea 5
## Juxin Xu y Lucas Poblete

## Preguntas
1. **(Item 1)** Antes de comenzar a programar, describa brevemente en su informe las similitudes y diferencias entre la tabla de rutas utilizadas para esta actividad, versus una tabla de rutas real.
> En las tablas de rutas utilizadas para esta atividad, se muestran rangos de puertos asociados a un puerto donde hacer forwarding, por otro lado, las tablas reales, guardan rangos de direcciones IP asociadas a la direccion de IP de un router donde hacer forwarding.
2. **(Item 5)** La forma en que su script recibe la información descrita deberá ser definida por usted y explicada apropiadamente en su informe. 
> primero se debe ejecutar el script con:
```
python3 cliente.py
```
> Luego, cada vez que se desee enviar un mensaje, se debe indicar la ip y puerto final junto con el mensaje siguiendo la estructura separada por ; descrito en "Simulando un mini-internet" y luego la ip y puerto de envio en los siguientes inputs:
```
IP_router_final;puerto_router_final;mensaje : 127.0.0.1;8883;hola
IP_envio;puerto_envio : 127.0.0.1;8882
```