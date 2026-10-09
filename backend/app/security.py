import ipaddress
import re
import socket
from urllib.parse import urlparse
from typing import Tuple, Optional
from app.config import SUPPORTED_PLATFORMS

class SecurityError(Exception):
    pass

def sanitize_filename(filename: str, max_length: int = 150) -> str:
    """
    Sanitizes a filename to prevent path traversal, invalid characters,
    and filesystem issues across Windows/Linux/macOS.
    """
    if not filename:
        return "downloaded_media"
    
    # Strip illegal characters for Windows and Unix filesystems
    # \ / : * ? " < > | and control characters
    sanitized = re.sub(r'[\\/*?:"<>|\x00-\x1f]', "", filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")
    # Replace whitespace sequences with a single space
    sanitized = re.sub(r'\s+', " ", sanitized)
    
    if not sanitized:
        sanitized = "downloaded_media"
        
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip(". ")
        
    return sanitized

def detect_platform(url: str) -> str:
    """
    Detects which platform the URL belongs to: youtube, tiktok, instagram, or generic.
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        return "unknown"
        
    for platform, domains in SUPPORTED_PLATFORMS.items():
        if any(hostname == d or hostname.endswith("." + d) for d in domains):
            return platform
            
    return "generic"

def is_ip_disallowed(ip_str: str) -> bool:
    """
    Checks if an IP address is private, loopback, link-local, multicast, or metadata.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_loopback:
            return True
        if ip.is_private:
            return True
        if ip.is_link_local:
            return True
        if ip.is_multicast:
            return True
        if ip.is_reserved:
            return True
        if ip.is_unspecified:
            return True
            
        # Cloud metadata protection (AWS, GCP, Azure, OpenStack)
        if str(ip) == "169.254.169.254":
            return True
            
        return False
    except ValueError:
        return True

def validate_url(url: str) -> Tuple[bool, Optional[str], str]:
    """
    Validates a URL against SSRF and syntax rules.
    Returns: (is_valid, error_message, detected_platform)
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty.", "unknown"
        
    url = url.strip()
    if len(url) > 2048:
        return False, "URL is too long (maximum 2048 characters allowed).", "unknown"
        
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL format: {str(e)}", "unknown"
        
    if parsed.scheme.lower() not in ("http", "https"):
        return False, "Only HTTP and HTTPS protocols are permitted.", "unknown"
        
    hostname = parsed.hostname
    if not hostname:
        return False, "URL must contain a valid hostname.", "unknown"
        
    hostname = hostname.lower()
    
    # Reject credentials in URL like http://user:pass@example.com
    if parsed.username or parsed.password:
        return False, "URLs with embedded credentials are not allowed.", "unknown"
        
    # Block localhost explicitly
    if hostname in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
        return False, "Access to localhost or internal metadata is strictly blocked.", "unknown"
        
    # DNS Resolution & SSRF check
    try:
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        if not addr_info:
            return False, f"Unable to resolve host: {hostname}", "unknown"
            
        for item in addr_info:
            sockaddr = item[4]
            ip_str = sockaddr[0]
            if is_ip_disallowed(ip_str):
                return False, f"Access to private/internal network address ({ip_str}) is prohibited.", "unknown"
    except socket.gaierror:
        return False, f"Could not resolve domain: {hostname}. Please check the URL.", "unknown"
    except Exception as e:
        return False, f"Network validation failed: {str(e)}", "unknown"
        
    platform = detect_platform(url)
    return True, None, platform
