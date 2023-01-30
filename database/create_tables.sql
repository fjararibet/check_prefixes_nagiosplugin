CREATE TABLE IF NOT EXISTS bgp.Equipo (
    IP VARCHAR(50) PRIMARY KEY ,
    Nombre VARCHAR(50) NOT NULL,
    CONSTRAINT IP_not_empty CHECK (IP <> ''),
    CONSTRAINT Nombre_not_empty CHECK (Nombre <> '')
);

CREATE TABLE IF NOT EXISTS bgp.Peer (
    IP VARCHAR(50) PRIMARY KEY,
    ISP VARCHAR(50),
    ASN INT,
    CONSTRAINT peer_ip_not_empty CHECK (IP <> '')
);

CREATE TABLE IF NOT EXISTS bgp.Peering (
    equipo_IP VARCHAR(50),
    peer_IP VARCHAR(50),
    PRIMARY KEY (equipo_IP, peer_IP),
    FOREIGN KEY (equipo_IP) REFERENCES Equipo(IP),
    FOREIGN KEY (peer_IP) REFERENCES Peer(IP)
);

CREATE TABLE IF NOT EXISTS bgp.PfxRcd (
    Prefijos INT,
    Fecha_hora DATETIME,
    equipo_IP VARCHAR(50),
    peer_IP VARCHAR(50),
    PRIMARY KEY (Fecha_hora, equipo_IP, peer_IP),
    FOREIGN KEY (equipo_IP) REFERENCES Equipo(IP),
    FOREIGN KEY (peer_IP) REFERENCES Peer(IP)
);