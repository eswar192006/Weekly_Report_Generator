import os
from jinja2 import Environment, FileSystemLoader


def build_html_report(report: dict, output_filename: str = "report.html") -> str:
    output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    template_dir = os.path.join(os.path.dirname(__file__), "..", "app", "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html")
    html = template.render(report=report)

    report_path = os.path.join(output_dir, output_filename)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    return report_path
