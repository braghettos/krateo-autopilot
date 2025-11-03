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
        form_path = labels.get("krateo.io/blueprint-form-path")

        if not form_path:
            return "Form found, but no path label set."
        
        frontend_link = get_frontend_link()
        if "Failed" in frontend_link:
            return "Could not get frontend link."
        
        form_url = f"http://{frontend_link}:8080/{form_path}"
        return f"Form found: path: `{form_url}`\n"

    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
def get_frontend_link() -> str:
    log.info("Attempting to get frontend service IP.")
    try:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "svc",
                "frontend",
                "-n",
                "krateo-system",
                "-o=jsonpath={.status.loadBalancer.ingress[0].ip}"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        ip = result.stdout.strip()
        return ip
    except Exception as e:
        return f"Failed to get frontend link: {str(e)}"
