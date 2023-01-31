# upload_bgp.php

Script php que captura la información del comando "show ip bgp summary" y la sube a la base de datos a través de la librería mysqli.
Opciones:  
`--exclude-peer`  Recibe una IP. Ignora la IP del vecino indicado, excluyéndolo en la subida de datos. Se puede usar varias veces.  
`--exclude-asn`  Recibe un ASN. Ignora todas la IP que tengan el ASN indicado. Se puede usar varias veces.

# check_prefixes.py

Plugin para nagios para monitorear la cantidad de prefijos.  
Opciones:  
`-h, --help`            muestra ayuda.  
 `-w RANGE, --warning RANGE` 
                        retorna warning si los prefijos están fuera del rango.  
 `-c RANGE, --critical RANGE`
                        retorna critical si los prefijos están fuera del rango.  
                        
# check_prefixes_proportion.py

Plugin para nagios para monitorear la proporción (en porcentaje) de prefijos con respecto al máximo del último mes encontrado en la base de datos.  
Opciones:  
`-h, --help`            muestra ayuda.  
 `-w RANGE, --warning RANGE` 
                        retorna warning si los prefijos están fuera del rango (0-100).  
 `-c RANGE, --critical RANGE`
                        retorna critical si los prefijos están fuera del rango (0-100).  

# check_all_prefixes.py

Plugin para nagios para monitorear la proporción (en porcentaje) de prefijos con respecto al máximo del último mes encontrado en la base de datos.  
Opciones:  
`-h, --help`            muestra ayuda.  
 `-w RANGE, --warning RANGE` 
                        retorna warning si los prefijos están fuera del rango (0-100).  
 `-c RANGE, --critical RANGE`
                        retorna critical si los prefijos están fuera del rango (0-100).  
 `-exp [IP ...], --exclude-peer [IP ...]`
                        Excluye a un vecino. Puede ser usada varias veces.   
 `-exa [ASN ...], --exclude-asn [ASN ...]`
                        Excluye a un ASN. Puede ser usada varias veces.  
## Convertir en ejecutable.
Para convertir algún plugin en ejecutable usando pyinstaller hay que indicar el directorio hooks, usando el siguiente comando.  

`pyinstaller --onefile --additional-hooks-dir ./hooks ./plugins/plugin.py`  

Se encontrará el ejecutable en la carpte `dist`.

