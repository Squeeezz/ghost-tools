"""User-initiated DNS diagnostics; does not scan ports or local network peers."""
import socket


def lookup_dns(host: str) -> list[str]:
    if not host or len(host) > 253 or any(ch.isspace() for ch in host):
        raise ValueError("Please provide a valid hostname without whitespace")
    results = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    return sorted({item[4][0] for item in results})
