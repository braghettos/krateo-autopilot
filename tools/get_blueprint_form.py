import subprocess
import logging
import json
log = logging.getLogger(__name__)

def get_blueprint_form(name: str, namespace: str) -> str:
    log.info(f"Attempting to get form: name='{name}', namespace='{namespace}'")
    try:
        label_selector = f"krateo.io/blueprint-form-name={name},krateo.io/blueprint-form-namespace={namespace}"
        cmd = [
            "kubectl", "get", "forms.widgets.templates.krateo.io",
            "-A",
            "-o", "json",
            "-l", label_selector
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        data = json.loads(result.stdout)
        items = data.get("items", [])

        if not items:
            return "No forms found."

        # Take the first matched CR
        labels = items[0].get("metadata", {}).get("labels", {})
        form_path = labels.get("krateo.io/blueprint-form-path").rstrip("/").lstrip("/")
        
        if not form_path:
            return "Form found, but no path label set."
        
        frontend_link = get_frontend_ip()
        if "Failed" in frontend_link:
            return "Could not get frontend link."
        
        form_url = f"http://{frontend_link}/{form_path}"
        return f"Form found: path: `{form_url}`\n"

    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
def get_frontend_ip() -> str:
    log.info("Attempting to get frontend service address.")
    try:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "svc",
                "frontend",
                "-n",
                "krateo-system",
                "-o",
                "json"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        svc = json.loads(result.stdout)
        svc_type = svc["spec"]["type"]
        ports = svc["spec"].get("ports", [])
        port = ports[0].get("port") if ports else None
        
        if not port:
            raise ValueError("No ports found in service definition.")
        
        ip = None

        if svc_type == "LoadBalancer":
            ingress = svc["status"].get("loadBalancer", {}).get("ingress", [])
            if ingress:
                ip = ingress[0].get("ip") or ingress[0].get("hostname")
        
        if svc_type == "NodePort":
            ip = svc["spec"].get("externalIPs", [None])[0]
            if not ip:
                ip = svc["spec"].get("clusterIP")
            port = ports[0].get("nodePort", port)
        
        if svc_type == "ClusterIP":
            ip = svc["spec"].get("clusterIP")
        
        if not ip:
            raise ValueError(f"Could not determine IP for service type {svc_type}.")
        
        address = f"{ip}:{port}"
        log.info(f"Frontend service address resolved: {address}")
        return address
    
    except Exception as e:
        log.error(f"Error getting frontend IP: {e}")
        return f"Failed to get frontend link: {str(e)}"
