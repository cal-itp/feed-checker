import json
import typer
import urllib.error
import urllib.parse
import urllib.request
import yaml

from transitland import get_transitland_urls
from transitfeeds import get_transitfeeds_urls


def clean_url(url):
    url = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(url.query, keep_blank_values=True)
    query.pop("api_key", None)
    query.pop("token", None)
    url = url._replace(query=urllib.parse.urlencode(query, True))
    return urllib.parse.urlunparse(url)


def tabulate(data, column_names):
    columns = []
    for name in column_names:
        columns.append([name, *data[name]])
    column_sizes = [max([len(s) for s in column]) for column in columns]
    num_rows = max([len(column) for column in columns])
    for i_row in range(num_rows):
        row = []
        for i_col, column in enumerate(columns):
            value = column[i_row] if len(column) > i_row else ""
            size = column_sizes[i_col]
            row.append(f"{value:<{size}}")
        print("   ".join(row))


def main(
    yml_file=typer.Argument("agencies.yml", help="A yml file containing urls"),
    csv_file=typer.Option(None, help="A csv file (one url per line)"),
    url=typer.Option(None, help="URL to check instead of a file",),
    output=typer.Option(None, help="Path to a file to save output to."),
    verbose: bool = typer.Option(False, help="Print a result table to stdout"),
):
    results = {}

    if url:
        results[url] = {
            "transitfeeds": {"status": "missing"},
            "transitland": {"status": "missing"},
        }
    elif csv_file:
        with open(csv_file, "r") as f:
            urls = f.read().strip().splitlines()
            for url in urls:
                results[url] = {
                    "transitfeeds": {"status": "missing"},
                    "transitland": {"status": "missing"},
                }
    else:
        with open(yml_file, "r") as f:
            agencies_obj = yaml.load(f, Loader=yaml.SafeLoader)
            for agency in agencies_obj.values():
                for feed in agency["feeds"]:
                    for url_number, (url_type, url) in enumerate(feed.items()):
                        if not url:
                            continue
                        results[url] = {
                            "url_type": url_type,
                            "itp_id": agency["itp_id"],
                            "url_number": url_number,
                            "transitfeeds": {"status": "missing"},
                            "transitland": {"status": "missing"},
                        }

    for public_web_url, url in get_transitland_urls():
        if url in results:
            results[url]["transitland"] = {
                "status": "present",
                "public_web_url": public_web_url,
            }

    for public_web_url, url in get_transitfeeds_urls():
        if url in results:
            results[url]["transitfeeds"] = {
                "status": "present",
                "public_web_url": public_web_url,
            }

    missing = []
    for url, data in results.items():
        statuses = [
            data["transitfeeds"]["status"],
            data["transitland"]["status"],
        ]
        if "present" not in statuses:
            missing.append(url)

    if missing and verbose:
        print(f"Unable to find {len(missing)}/{len(results)} urls:")
        for url in missing:
            print(url)
    else:
        matched = len(results) - len(missing)
        print(f"Found {matched}/{len(results)} urls were found")

    if output:
        with open(output, "w") as f:
            f.write(json.dumps(results, indent=4))
            print(f"Results saved to {output}")


if __name__ == "__main__":
    typer.run(main)
