#!/usr/bin/php
<?php

$excluded_peers = array();
$excluded_asns = array();

# Extraer peers excluidos
$option = getopt('', array("exclude-peer:", "exclude-asn:"));

if (isset($option['exclude-peer'])) {
	array_push($excluded_peers, $option['exclude-peer']);
}

if (isset($option['exclude-asn'])) {
	array_push($excluded_asns, $option['exclude-asn']);
}

$bgp_summary = `sudo vtysh -c "show ip bgp summary"`;

# Extraer la cantidad de vecinos
$cantidad_vecinos = `echo "$bgp_summary" | grep "Total number of neighbors" | tail -c +27`;
$cantidad_vecinos = intval($cantidad_vecinos);

# Guardar los datos de los vecinos en un arreglo
$datos_vecinos = `echo "$bgp_summary" | grep -A $cantidad_vecinos -w Neighbor | tail -n +2`;
$datos_vecinos = preg_split("/\n/", $datos_vecinos, $cantidad_vecinos);


# Incluir link a base de datos
# connect.php debe guardar la conexión en la variable $link
require("connect.php");

# SQL para insertar, no insertan si ya existe
$equipo_insert = "INSERT INTO Equipo(IP, Nombre) VALUES (?,?) ON DUPLICATE KEY UPDATE IP=IP, Nombre=?";
$peer_insert = "INSERT INTO Peer(IP, ISP, ASN) VALUES (?,?,?) ON DUPLICATE KEY UPDATE IP=IP, ISP=?, ASN=?";
$peering_insert = "INSERT INTO Peering(equipo_IP, peer_IP) VALUES (?,?) ON DUPLICATE KEY UPDATE equipo_IP=equipo_IP";
$pfxrcd_insert = "INSERT INTO PfxRcd(Prefijos, Fecha_hora, equipo_IP, peer_IP) VALUES (?,?,?,?) ON DUPLICATE KEY UPDATE Fecha_hora=Fecha_hora";

# Preparar y asociar variables a las sentencias
try {
	$equipo_stmt = mysqli_prepare($link, $equipo_insert);
	$peer_stmt = mysqli_prepare($link, $peer_insert);
	$peering_stmt = mysqli_prepare($link, $peering_insert);
	$pfxrcd_stmt = mysqli_prepare($link, $pfxrcd_insert);
	mysqli_stmt_bind_param($equipo_stmt, 'sss', $equipo_ip, $equipo_nombre, $equipo_nombre);
	mysqli_stmt_bind_param($peer_stmt, 'ssisi', $peer_ip, $isp, $asn, $isp, $asn);
	mysqli_stmt_bind_param($peering_stmt, 'ss', $equipo_ip, $peer_ip);
	mysqli_stmt_bind_param($pfxrcd_stmt, 'isss', $prefijos, $fecha_hora, $equipo_ip, $peer_ip);
} catch(Exception $e) {
	log_error($e);
}


# Inserta los datos con los valores de bgp summary
foreach ($datos_vecinos as $datos_bgp) {

	# Separar los datos entre espacio y ponerlos en un arreglo
	$datos_bgp = preg_split("/\s+/", $datos_bgp);

	# Asignar variables
	$peer_ip = $datos_bgp[0];
	$equipo_ip = trim(`sudo vtysh -c "show ip bgp neighbors $peer_ip" | grep "Local host:" | awk -F '[," "]' '{print $3}'`);
	$equipo_nombre = trim(`hostname`);
	$isp = trim(`whois "$peer_ip" | grep "owner:" | tail -c +7`);
	$asn = $datos_bgp[2];
	$prefijos = is_numeric($datos_bgp[9]) ? intval($datos_bgp[9]) : null;
	$fecha_hora = `date -u "+%F %H:%M:%S"`;

	# Si es un peer o ASN excluido, se lo salta.
	if (in_array($peer_ip, $excluded_peers) || in_array($asn, $excluded_asns)) {
		continue;
	}

	# Comienzo de transacción
	# En caso de error, no se debiera insertar nada. Ejemplo: equipo_ip vacío
	mysqli_begin_transaction($link);

	try {
		mysqli_stmt_execute($equipo_stmt);
		mysqli_stmt_execute($peer_stmt);
		mysqli_stmt_execute($peering_stmt);
		mysqli_stmt_execute($pfxrcd_stmt);

		# Si el código ha llegado hasta acá, no hay errores en la inserción
		# Se confirman los cambios
		mysqli_commit($link);
	} catch (Exception $e) {
		# En caso de error, se hace rollback y se loggea.
		mysqli_rollback($link);
		log_error($e);
	}
}

# Se cierran sentencias y conexión a db.
mysqli_stmt_close($equipo_stmt);
mysqli_stmt_close($peer_stmt);
mysqli_stmt_close($peering_stmt);
mysqli_stmt_close($pfxrcd_stmt);
mysqli_close($link);

# Escribe los errores en log.txt en el mismo directorio donde se corra este script.
function log_error($exception) {
	$fecha = `date -u "+%F %H:%M:%S"`;
	$error =  "UTC {$fecha}Error: {$exception->getMessage()}\nTrace:\n{$exception->getTraceAsString()}\n\n";
	file_put_contents("log.txt", $error, FILE_APPEND);
}
?>
